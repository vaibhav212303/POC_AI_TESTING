import asyncio
import os
import json
import sys
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

from ai_handler import get_ai_response, active_model
from generators import generate_manual_test_proposal, generate_pom_code, generate_spec_code
from healer import heal_code

load_dotenv()

# --- PATH CONFIG ---
BASE_DIR = os.path.dirname(os.getcwd())
SERVER_DIR = os.path.join(BASE_DIR, "playwright-server")
SNAPSHOTS_DIR = os.path.join(SERVER_DIR, "snapshots")
MANUAL_DIR = os.path.join(SERVER_DIR, "manual_cases")
PAGES_DIR = os.path.join(SERVER_DIR, "tests", "pages")
SPECS_DIR = os.path.join(SERVER_DIR, "tests", "specs")

async def run_workflow():
    # 1. Setup Connection for Initial Navigation
    server_script = os.path.abspath(os.path.join(SERVER_DIR, "src/index.ts"))
    server_params = StdioServerParameters(command="npx", args=["tsx", server_script], env=os.environ)

    url = input("🌐 Enter URL to Automate: ").strip()
    page_name = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "_")

    print("\n--- 🟢 NODE 1: Navigation & Visualization ---")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Launch & Nav
            await session.call_tool("launch_browser")
            await session.call_tool("navigate", arguments={"url": url})
            
            # Take Screenshot (Baseline Check)
            print("📸 Taking screenshot...")
            res = await session.call_tool("screenshot", arguments={"name": f"../../ai-browser-automation/playwright-server/snapshots/{page_name}_base.png"})
            
            baseline_path = os.path.join(SNAPSHOTS_DIR, f"{page_name}_base.png")
            if os.path.exists(baseline_path):
                print(f"✅ Baseline image exists at {baseline_path}")
            else:
                print(f"⚠️ New Baseline created at {baseline_path}")

            # Get Content for AI Analysis
            content_res = await session.call_tool("get_content")
            page_text = content_res.content[0].text

            # --- 🟡 NODE 2: Test Case Discovery ---
            print("\n--- 🟡 NODE 2: Test Case Strategy ---")
            json_path = os.path.join(MANUAL_DIR, f"{page_name}.json")
            
            manual_data = ""
            if os.path.exists(json_path):
                print("📂 Found existing manual test case.")
                with open(json_path, "r") as f:
                    manual_data = f.read()
            else:
                print("🧠 No test found. Analyzing page to propose one...")
                proposed_json = generate_manual_test_proposal(url, page_text)
                print(f"\nAI Proposal:\n{proposed_json}")
                
                consent = input("\n👉 Approve this test case? (y/n): ")
                if consent.lower() != "y":
                    print("🛑 Aborted by user.")
                    return
                
                with open(json_path, "w") as f:
                    f.write(proposed_json)
                manual_data = proposed_json
                print("✅ Manual Test Case Saved.")

            # --- 🟠 NODE 3: Automation Architecture (POM) ---
            print("\n--- 🟠 NODE 3: Generating Code Architecture ---")
            pom_name, pom_code = generate_pom_code(manual_data)
            spec_code = generate_spec_code(manual_data, pom_name)
            
            pom_path = os.path.join(PAGES_DIR, f"{pom_name}Page.ts")
            spec_path = os.path.join(SPECS_DIR, f"{page_name}.spec.ts")
            
            with open(pom_path, "w") as f: f.write(pom_code)
            with open(spec_path, "w") as f: f.write(spec_code)
            
            print(f"📄 Created POM: {pom_path}")
            print(f"📄 Created Spec: {spec_path}")

    # --- 🔴 NODE 4: Execution & Self-Healing ---
    # We close the MCP session and run the actual Playwright Runner
    print("\n--- 🔴 NODE 4: Execution Phase ---")
    
    max_retries = 2
    attempt = 0
    
    while attempt <= max_retries:
        attempt += 1
        print(f"\n🚀 Execution Attempt {attempt}...")
        
        # Run Playwright Test
        result = subprocess.run(
            ["npx", "playwright", "test", spec_path, "--headed"], 
            cwd=SERVER_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("🎉 SUCCESS! Test Passed.")
            print(result.stdout)
            break
        else:
            print("❌ FAILURE DETECTED.")
            error_log = result.stderr
            print(f"Error Log Snippet: {error_log[-500:]}") # Last 500 chars
            
            if attempt <= max_retries:
                print("\n🚑 Initiating Self-Healing Protocol...")
                heal_code(pom_path, error_log)
                print("🔄 Re-queueing test...")
            else:
                print("💀 Max retries reached. Manual intervention required.")

if __name__ == "__main__":
    try:
        asyncio.run(run_workflow())
    except KeyboardInterrupt:
        pass