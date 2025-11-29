import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.ai import get_ai_response

# Server Config
server_script_path = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server/src/index.ts"))
server_params = StdioServerParameters(command="npx", args=["tsx", server_script_path], env=os.environ)

async def run_chat_assistant():
    print("🔌 Connecting to Browser Server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get Tools
            tools = await session.list_tools()
            tools_schema = []
            
            # --- FIX: INDENTATION CORRECTED HERE ---
            for t in tools.tools:
                schema = getattr(t, 'inputSchema', getattr(t, 'input_schema', {}))
                
                tools_schema.append({
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": schema 
                })
            # ---------------------------------------

            print("✅ Connected! Type your commands.")
            messages = []

            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ["quit", "exit"]:
                    break
                
                messages.append({"role": "user", "parts": [user_input]})

                try:
                    response = get_ai_response(messages, tools_schema)
                    
                    # Check first part for function call
                    part = response.parts[0]

                    if fn := part.function_call:
                        tool_name = fn.name
                        tool_args = dict(fn.args)
                        
                        print(f"🤖 AI Action: {tool_name} {tool_args}")
                        
                        result = await session.call_tool(tool_name, arguments=tool_args)
                        
                        # Update history with tool execution
                        messages.append({"role": "model", "parts": [part]})
                        messages.append({
                            "role": "function", 
                            "name": tool_name, 
                            "parts": [{"function_response": {"name": tool_name, "response": {"result": str(result)}}}]
                        })
                        print(f"✅ Result: {str(result)[:100]}...") 
                    else:
                        print(f"🤖 AI: {part.text}")
                        messages.append({"role": "model", "parts": [part.text]})
                        
                except Exception as e:
                    print(f"❌ Error: {e}")