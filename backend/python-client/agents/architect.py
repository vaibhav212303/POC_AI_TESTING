import os
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.ai import get_ai_response
from utils.generators import generate_manual_test_proposal, generate_pom_code, generate_spec_code
from utils.healer import heal_code
from core.mcp_client import create_mcp_connection

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.getcwd())) # Adjust based on depth
SERVER_DIR = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server"))
MANUAL_DIR = os.path.join(SERVER_DIR, "manual_cases")
PAGES_DIR = os.path.join(SERVER_DIR, "tests", "pages")
SPECS_DIR = os.path.join(SERVER_DIR, "tests", "specs")

async def run_architect_flow():
    print("\n🚀 Starting Autonomous Architect Agent...")
    
    # Connect to Server
    server_script = os.path.join(SERVER_DIR, "src/index.ts")
    server_params = StdioServerParameters(command="npx", args=["tsx", server_script], env=os.environ)

    url = input("🌐 Enter URL to Automate: ").strip()
    page_safe_name = url.replace("https://", "").replace(".", "_").replace("/", "_")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. VISUALIZATION
            print("--- Phase 1: Visualization ---")
            await session.call_tool("launch_browser")
            await session.call_tool("navigate", arguments={"url": url})
            content_res = await session.call_tool("get_content")
            page_text = content_res.content[0].text
            
            # 2. TEST DESIGN
            print("--- Phase 2: Test Design ---")
            json_path = os.path.join(MANUAL_DIR, f"{page_safe_name}.json")
            
            if not os.path.exists(json_path):
                proposal = generate_manual_test_proposal(url, page_text)
                print(f"AI Proposal:\n{proposal}")
                if input("Approve? (y/n): ").lower() == 'y':
                    if not os.path.exists(MANUAL_DIR): os.makedirs(MANUAL_DIR)
                    with open(json_path, "w") as f: f.write(proposal)
                    manual_data = proposal
                else:
                    return
            else:
                with open(json_path, "r") as f: manual_data = f.read()

            # 3. CODE GENERATION
            print("--- Phase 3: Architecture Generation ---")
            pom_name, pom_code = generate_pom_code(manual_data)
            spec_code = generate_spec_code(manual_data, pom_name)
            
            if not os.path.exists(PAGES_DIR): os.makedirs(PAGES_DIR)
            if not os.path.exists(SPECS_DIR): os.makedirs(SPECS_DIR)

            pom_path = os.path.join(PAGES_DIR, f"{pom_name}Page.ts")
            spec_path = os.path.join(SPECS_DIR, f"{page_safe_name}.spec.ts")

            with open(pom_path, "w") as f: f.write(pom_code)
            with open(spec_path, "w") as f: f.write(spec_code)
            
            print(f"✅ Generated: {pom_name}Page.ts & {page_safe_name}.spec.ts")

    # 4. EXECUTION & HEALING (Outside MCP loop)
    print("--- Phase 4: Execution & Healing ---")
    run_test_with_healing(spec_path, pom_path)

def run_test_with_healing(spec_path, pom_path):
    for attempt in range(1, 3):
        print(f"▶️ Execution Attempt {attempt}...")
        res = subprocess.run(
            ["npx", "playwright", "test", spec_path, "--headed"],
            cwd=SERVER_DIR, capture_output=True, text=True
        )
        
        if res.returncode == 0:
            print("🎉 Test Passed!")
            break
        else:
            print("❌ Test Failed.")
            print(res.stderr[-300:])
            print("🚑 Healing...")
            heal_code(pom_path, res.stderr)