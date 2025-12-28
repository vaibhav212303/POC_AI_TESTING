import asyncio
from mcp import ClientSession
from core.ai import get_ai_response, parse_ai_response, set_active_model
from core.mcp_client import create_mcp_connection

class AgentEngine:
    def __init__(self):
        self.session = None
        self.conn_ctx = None
        self.sess_ctx = None
        self.history = [{
            "role": "system",
            "content": "You are a QA Assistant. If you navigate/act, take a screenshot."
        }]

    async def initialize(self):
        """Starts the MCP Client connection."""
        try:
            self.conn_ctx = create_mcp_connection()
            read, write = await self.conn_ctx.__aenter__()
            
            self.sess_ctx = ClientSession(read, write)
            self.session = await self.sess_ctx.__aenter__()
            
            await self.session.initialize()
            return True
        except Exception as e:
            print(f"Connection Failed: {e}")
            return False

    async def shutdown(self):
        """Clean up resources."""
        if self.sess_ctx: await self.sess_ctx.__aexit__(None, None, None)
        if self.conn_ctx: await self.conn_ctx.__aexit__(None, None, None)

    async def process_message(self, user_input, provider="gemini", model="models/gemini-1.5-flash"):
        """
        Runs the AI Loop and YIELDS events to the API Server.
        """
        # Set the model dynamically based on UI selection
        set_active_model(provider, model)

        self.history.append({"role": "user", "content": user_input})
        
        # Fetch available tools
        tools = await self.session.list_tools()
        tools_schema = []
        for t in tools.tools:
            schema = getattr(t, 'inputSchema', getattr(t, 'input_schema', {}))
            tools_schema.append({"name": t.name, "description": t.description, "inputSchema": schema})

        # Loop (Prevent infinite loops with range)
        for _ in range(5):
            try:
                # 1. Yield Thinking Status
                yield {"type": "log", "content": f"🧠 Thinking ({provider})..."}
                
                # 2. Get AI Response
                raw_response = get_ai_response(self.history, tools_schema)
                intent = parse_ai_response(raw_response)

                # 3. Handle Text (Stop)
                if intent["type"] == "text":
                    response_text = intent["content"]
                    self.history.append({"role": "model", "content": response_text})
                    yield {"type": "response", "content": response_text}
                    break 

                # 4. Handle Tool (Action)
                elif intent["type"] == "tool_call":
                    t_name = intent["tool_name"]
                    t_args = intent["tool_args"]
                    
                    yield {"type": "log", "content": f"⚙️ Action: {t_name} {t_args}"}
                    
                    # Execute on Server
                    result = await self.session.call_tool(t_name, arguments=t_args)
                    
                    # Process Results (Look for Images)
                    result_text_clean = ""
                    for content in result.content:
                        if content.type == "text":
                            if content.text.startswith("IMAGE_BASE64:"):
                                base64_data = content.text.replace("IMAGE_BASE64:", "")
                                yield {"type": "image", "content": base64_data}
                                result_text_clean += "[Screenshot Captured]"
                            else:
                                result_text_clean += content.text

                    yield {"type": "log", "content": f"✅ Result: {result_text_clean[:100]}..."}

                    # Update History
                    self.history.append({"role": "model", "content": f"Call {t_name}"})
                    self.history.append({"role": "user", "content": f"Tool Output: {result_text_clean}"})
                    
            except Exception as e:
                yield {"type": "error", "content": str(e)}
                break