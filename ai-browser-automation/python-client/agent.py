import asyncio
import os
import json
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Import AI logic and Generator
from ai_handler import get_ai_response, active_model
from code_generator import generate_test_file, get_existing_tests 

load_dotenv()

# Global recorder to store actions
session_recorder = []

def parse_ai_response(response):
    """Parses response from Gemini/OpenAI/Claude into a standard format."""
    try:
        if active_model == "gemini":
            candidate = response.candidates[0]
            part = candidate.content.parts[0]
            if part.function_call:
                return {
                    "type": "tool_call",
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args)
                }
            else:
                return { "type": "text", "content": part.text }
        elif active_model == "openai":
            if response.tool_calls:
                tool = response.tool_calls[0]
                return {
                    "type": "tool_call",
                    "name": tool.function.name,
                    "args": json.loads(tool.function.arguments)
                }
            return { "type": "text", "content": response.content }
        elif active_model == "claude":
            for block in response.content:
                if block.type == "tool_use":
                    return { "type": "tool_call", "name": block.name, "args": block.input }
            return { "type": "text", "content": response.content[0].text }
    except Exception as e:
        return { "type": "text", "content": f"Error parsing response: {e}" }

async def run_chat_loop():
    # FIX: Global declaration at the start
    global session_recorder 
    
    server_script_path = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server/src/index.ts"))
    server_params = StdioServerParameters(command="npx", args=["tsx", server_script_path], env=os.environ)

    print("🔌 Connecting to Playwright Server...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools_list = await session.list_tools()
                tools_schema = [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in tools_list.tools]
                print("✅ System Ready. Recorder Active 🔴")
                print("ℹ️  Type 'save test' to generate code, or 'exit' to quit.")

                messages = [
                    {"role": "system", "content": "You are a helpful browser automation assistant. Always launch the browser first if not open."}
                ]

                while True:
                    try:
                        user_input = input("\n👤 You: ")
                    except (EOFError, KeyboardInterrupt):
                        print("\n🛑 Interrupted by user.")
                        break 

                    if user_input.lower() in ["exit", "quit"]:
                        break
                    
                    # --- INTERACTIVE SAVE FLOW ---
                    if "save test" in user_input.lower():
                        if len(session_recorder) == 0:
                            print("⚠️ No actions recorded yet.")
                            continue

                        print("\n💾 Save Options:")
                        print("1. Create New File")
                        print("2. Update Existing File")
                        
                        choice = input("Select (1/2): ").strip()

                        if choice == "2":
                            files = get_existing_tests()
                            if not files:
                                print("⚠️ No existing tests found. Creating new instead.")
                                choice = "1"
                            else:
                                print("\nExisting Tests:")
                                for i, f in enumerate(files):
                                    print(f"{i+1}. {f}")
                                try:
                                    sel = input("Select file number: ").strip()
                                    f_idx = int(sel) - 1
                                    target_file = files[f_idx]
                                    generate_test_file(session_recorder, filename=target_file, mode="update")
                                    session_recorder = [] 
                                    print("✅ Recorder cleared.")
                                except ValueError:
                                    print("❌ Invalid selection.")
                                except IndexError:
                                    print("❌ File number out of range.")
                        
                        if choice == "1":
                            fname = input("Enter filename (e.g., login.spec.ts): ").strip()
                            if not fname: fname = "generated_test.spec.ts"
                            if not fname.endswith(".spec.ts"): fname += ".spec.ts"
                            generate_test_file(session_recorder, filename=fname, mode="new")
                            session_recorder = []
                            print("✅ Recorder cleared.")
                        continue 

                    messages.append({"role": "user", "content": user_input})

                    # 2. AI LOOP
                    while True:
                        try:
                            response = get_ai_response(messages, tools_schema)
                        except Exception as e:
                            if "429" in str(e) or "ResourceExhausted" in str(e):
                                print("\n⏳ Rate Limit Hit. Waiting 60s...")
                                time.sleep(60)
                                continue
                            else:
                                print(f"❌ AI Error: {e}")
                                break

                        intent = parse_ai_response(response)

                        if intent["type"] == "text":
                            ai_text = intent["content"]
                            print(f"🤖 AI: {ai_text}")
                            messages.append({"role": "assistant", "content": ai_text})
                            break 

                        elif intent["type"] == "tool_call":
                            t_name = intent["name"]
                            t_args = intent["args"]
                            print(f"⚙️  Executing: {t_name} {t_args}...")
                            
                            try:
                                result = await session.call_tool(t_name, arguments=t_args)
                                
                                # --- VISION LOGIC START ---
                                output_text = ""
                                image_data = None

                                # Parse content (Text vs Image)
                                for content in result.content:
                                    if content.type == "text":
                                        if content.text.startswith("IMAGE_BASE64:"):
                                            image_data = content.text.replace("IMAGE_BASE64:", "")
                                        else:
                                            output_text += content.text + "\n"
                                
                                output_text = output_text.strip()
                                # --------------------------

                                # Record Action (Only text result)
                                if t_name != "get_content":
                                    session_recorder.append({
                                        "tool": t_name,
                                        "args": t_args,
                                        "result": output_text[:100]
                                    })

                                display_out = (output_text[:100] + '...') if len(output_text) > 100 else output_text
                                print(f"   ✅ Result: {display_out}")

                                # Prepare Message for AI
                                if image_data:
                                    print("   📸 Screenshot captured. Sending to AI...")
                                    messages.append({
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": f"Tool '{t_name}' output: {output_text}"},
                                            {"type": "image", "data": image_data} # Custom type for our handler
                                        ]
                                    })
                                else:
                                    messages.append({
                                        "role": "user", 
                                        "content": f"Tool '{t_name}' output: {output_text}"
                                    })
                                
                                time.sleep(1) 

                            except Exception as e:
                                print(f"   ❌ Tool Error: {e}")
                                messages.append({"role": "user", "content": f"Tool error: {e}"})

    except Exception as e:
        print(f"\n❌ Critical System Error: {e}")

    finally:
        print("\n👋 Session Ended.")
        if len(session_recorder) > 0:
            print(f"💾 Found {len(session_recorder)} unsaved actions.")
            try:
                generate_test_file(session_recorder, filename="autosaved_backup.spec.ts", mode="new")
                print("✅ Saved to 'autosaved_backup.spec.ts'")
            except Exception as e:
                print(f"❌ Failed to auto-save: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_chat_loop())
    except KeyboardInterrupt:
        pass