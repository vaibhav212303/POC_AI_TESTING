import asyncio
import os
import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.ai import get_ai_response, parse_ai_response, set_active_model, get_current_model_info
from core.mcp_client import create_mcp_connection

async def run_chat_assistant():
    print(f"\n💬 Starting Interactive Assistant ({get_current_model_info()})")
    print("ℹ️  Type '/switch' to change models.")
    print("ℹ️  Type 'exit' to quit.\n")

    try:
        async with create_mcp_connection() as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools = await session.list_tools()
                tools_schema = []
                for t in tools.tools:
                    schema = getattr(t, 'inputSchema', getattr(t, 'input_schema', {}))
                    tools_schema.append({
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": schema 
                    })

                # STRONGER SYSTEM PROMPT to prevent loops
                messages = [{
                    "role": "system", 
                    "content": """You are a browser automation assistant.
                    1. If you successfully execute a tool (like navigate), DO NOT call it again immediately.
                    2. Instead, describe what you see or ask the user for the next step.
                    3. If the browser is not open, call launch_browser first.
                    """
                }]

                last_tool_call = None

                while True:
                    try:
                        user_input = input("\n👤 You: ").strip()
                    except EOFError: break
                    if not user_input: continue
                    if user_input.lower() in ["exit", "quit"]: break
                    
                    if user_input.lower().startswith("/switch"):
                        print("\n🔄 Select Model: 1. Gemini Flash  2. Llama 3.3 (Groq)  3. GPT-4o")
                        sel = input("Choice: ").strip()
                        if sel == "1": set_active_model("gemini", "models/gemini-1.5-flash")
                        elif sel == "2": set_active_model("groq", "llama-3.3-70b-versatile")
                        elif sel == "3": set_active_model("openai", "gpt-4o")
                        continue

                    messages.append({"role": "user", "content": user_input})

                    # AI Loop
                    loop_count = 0
                    while loop_count < 5: # Safety break
                        loop_count += 1
                        try:
                            raw_response = get_ai_response(messages, tools_schema)
                            intent = parse_ai_response(raw_response)

                            if intent["type"] == "text":
                                ai_text = intent["content"]
                                print(f"🤖 AI: {ai_text}")
                                messages.append({"role": "model", "content": ai_text})
                                break 

                            elif intent["type"] == "tool_call":
                                t_name = intent["tool_name"]
                                t_args = intent["tool_args"]
                                
                                # LOOP PREVENTION CHECK
                                current_call = f"{t_name}:{json.dumps(t_args, sort_keys=True)}"
                                if current_call == last_tool_call:
                                    print(f"⚠️ Preventing duplicate tool call loop: {t_name}")
                                    messages.append({"role": "user", "content": "You just did that. What is the next step?"})
                                    continue
                                last_tool_call = current_call

                                print(f"⚙️  Action: {t_name} {t_args}")
                                result = await session.call_tool(t_name, arguments=t_args)
                                
                                result_text = ""
                                for content in result.content:
                                    if content.type == "text":
                                        if content.text.startswith("IMAGE_BASE64:"):
                                            result_text += "[Screenshot Taken]"
                                        else:
                                            result_text += content.text

                                print(f"   ✅ Result: {result_text[:100]}...")
                                messages.append({"role": "model", "content": f"Call {t_name}."})
                                messages.append({"role": "user", "content": f"Tool Output: {result_text}"})

                        except Exception as e:
                            print(f"❌ Error in AI Loop: {e}")
                            break
                    
                    if loop_count >= 5:
                        print("⚠️ Pause: Too many sequential actions.")

    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_chat_assistant())
    except KeyboardInterrupt:
        pass