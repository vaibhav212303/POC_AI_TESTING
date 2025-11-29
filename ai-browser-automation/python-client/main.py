import asyncio
import sys
from dotenv import load_dotenv
from agents.assistant import run_chat_assistant
from agents.architect import run_architect_flow

load_dotenv()

def main_menu():
    print("\n🤖 AI QA FRAMEWORK")
    print("===================")
    print("1. Interactive Chat Assistant (Manual Control)")
    print("2. Autonomous Architect (N8N Style Workflow)")
    print("3. Exit")
    
    choice = input("\nSelect Mode (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(run_chat_assistant())
    elif choice == "2":
        asyncio.run(run_architect_flow())
    elif choice == "3":
        sys.exit(0)
    else:
        print("Invalid choice.")
        main_menu()

if __name__ == "__main__":
    main_menu()