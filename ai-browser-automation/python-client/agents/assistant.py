import asyncio
import os
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.ai import get_ai_response, parse_ai_response
from core.mcp_client import create_mcp_connection

async def run_chat_assistant():
    print("\n💬 Starting Interactive Assistant...")
    # ... (Paste your previous agent.py logic here, but use core.ai functions) ...
    # Simplified for brevity:
    server_script = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server/src/index.ts"))
    server_params = StdioServerParameters(command="npx", args=["tsx", server_script], env=os.environ)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tools_schema = [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in tools.tools]
            
            messages = [{"role": "system", "content": "You are a QA Assistant."}]
            
            while True:
                user_in = input("\n👤 You: ")
                if user_in == "exit": break
                messages.append({"role": "user", "content": user_in})
                
                resp = get_ai_response(messages, tools_schema)
                intent = parse_ai_response(resp)
                
                if intent["type"] == "text":
                    print(f"🤖 {intent['content']}")
                    messages.append({"role": "assistant", "content": intent['content']})
                elif intent["type"] == "tool_call":
                    print(f"⚙️ {intent['name']} {intent['args']}")
                    res = await session.call_tool(intent["name"], arguments=intent["args"])
                    
                    # Handle Image/Text response
                    content_list = []
                    for c in res.content:
                        if c.type == "text":
                            if c.text.startswith("IMAGE_BASE64:"):
                                content_list.append({"type": "image", "data": c.text.replace("IMAGE_BASE64:", "")})
                            else:
                                content_list.append({"type": "text", "text": c.text})
                                print(f"✅ {c.text[:100]}")
                    
                    messages.append({"role": "user", "content": content_list})