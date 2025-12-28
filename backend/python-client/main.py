import asyncio
import sys
import os
import subprocess

from agents.assistant import run_chat_assistant
from utils.file_parser import get_test_files
from utils.reporter import parse_test_results, open_html_report

# Update imports to include the Generation Nodes
from workflow.engine import WorkflowEngine
from workflow.nodes import (FixtureLoaderNode, PlaywrightAgentNode, VerifiedPomNode, VerifiedSpecNode)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def main_menu():
    print("\n" + "="*50)
    print("      🤖 AI BROWSER AUTOMATION SUITE      ")
    print("="*50)
    print("1. Interactive Chat Assistant (Manual Control)")
    print("2. Autonomous Architect (N8N Style Workflow)")
    print("3. Exit")
    print("="*50)
    
    choice = input("\nEnter your choice (1-3): ").strip()
    if choice == "1":
        print("\n💬 Starting Interactive Chat... (Type 'quit' to exit chat)")
        try:
            asyncio.run(run_chat_assistant())
        except Exception as e:
            print(f"Error in Chat Mode: {e}")
            
    elif choice == "2":
        # 1. Fetch available test files
        print("\n🔍 Scanning 'playwright-server/fixture/tests/'...")
        files = get_test_files()
        if not files:
            print("❌ No Markdown (.md) files found.")
            input("Press Enter to return to menu...")
            return
            
        # 2. Display selection menu
        print("\n📂 Available Test Scenarios:")
        for idx, f in enumerate(files, 1):
            filename = os.path.basename(f)
            print(f"   {idx}. {filename}")
            
        # 3. User Selection
        try:
            selection = input("\nSelect a test number (or '0' to cancel): ").strip()
            if selection == '0': return
            idx = int(selection) - 1
            if idx < 0 or idx >= len(files):
                print("❌ Invalid selection.")
                return
            selected_file_path = files[idx]
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
            return

        # 4. Initialize N8N Style Workflow Engine
        print(f"\n🚀 Initializing Autonomous Architect for: {os.path.basename(selected_file_path)}")
        
        engine = WorkflowEngine()
        
        # --- Define the Architecture (The "Flow") ---
        # Node 1: Load the File
        engine.add_node(FixtureLoaderNode(selected_file_path))
        # Node 2: AI Agent Execution (Drives Browser & Records Actions)
        engine.add_node(PlaywrightAgentNode())
        # Node 3: Generate Verified POM (From Recorded Actions)
        engine.add_node(VerifiedPomNode())
        # Node 4: Generate Verified Spec (From POM)
        engine.add_node(VerifiedSpecNode())
        # 5. Execute Workflow
        try:
            asyncio.run(engine.run())
            
            # --- POST-WORKFLOW: EXECUTION & REPORTING ---
            print("\n" + "="*50)
            print("      🧪 EXECUTING GENERATED TESTS       ")
            print("="*50)
            
            server_dir = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server"))
            
            # Run Playwright (Headless or Headed based on preference)
            # We use the JSON reporter for our Python parser
            subprocess.run(
                ["npx", "playwright", "test", "--reporter=json,html"], 
                cwd=server_dir, 
                shell=True if os.name == 'nt' else False
            )
            
            # Parse & Display Results
            results = parse_test_results(server_dir)
            if results.get("total", 0) > 0:
                print(f"\n📊 Summary: {results['passed']} Passed | {results['failed']} Failed")
                if results['failed'] == 0:
                    print("🎉 SUCCESS! Opening Report...")
                    open_html_report(server_dir)
                else:
                    print("❌ Failures Detected. Check report details.")
                    # Optional: Trigger Self-Healing here in the future
            else:
                print("⚠️ No tests were run. Check generated files.")
        except Exception as e:
            print(f"🔥 Workflow Critical Error: {e}")
        input("\nPress Enter to return to menu...")

    elif choice == "3":
        print("\n👋 Goodbye!")
        sys.exit()
    else:
        print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    while True:
        try:
            main_menu()
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            sys.exit()