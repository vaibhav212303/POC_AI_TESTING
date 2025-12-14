import json
import asyncio
import os
import base64
from playwright.async_api import async_playwright
from browser_tools import TOOLS_SCHEMA, BrowserTools
from llm_provider import LLMProvider

class AgentService:
    def __init__(self):
        self.llm = LLMProvider()
        self.queue = asyncio.Queue()
        self.running_event = asyncio.Event()
        self.running_event.set() 
        self.is_step_mode = False

    def pause(self):
        self.running_event.clear()
        self.is_step_mode = False
    
    def resume(self):
        self.is_step_mode = False
        self.running_event.set()

    def step(self):
        self.is_step_mode = True
        self.running_event.set()

    async def run_task(self, user_task: str, provider: str = "ollama"):
        asyncio.create_task(self._agent_logic(user_task, provider))
        while True:
            event = await self.queue.get()
            yield event
            if event["type"] == "done" or event["type"] == "error":
                break

    async def _agent_logic(self, user_task: str, provider: str):
        await self.queue.put({"type": "info", "content": f"🚀 Initializing {provider.upper()} Agent..."})
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir="videos/",
                record_video_size={"width": 1280, "height": 720}
            )
            
            page = await context.new_page()
            
            try:
                client = await context.new_cdp_session(page)
                await client.send("Page.startScreencast", {"format": "jpeg", "quality": 50})
                client.on("Page.screencastFrame", lambda event: self._handle_screencast(client, event))
            except Exception:
                pass 

            tools = BrowserTools(page)
            await self.queue.put({"type": "success", "content": "Recording started..."})

            full_prompt = f"""You are a Web Automation Agent.
            RULES:
            1. Use tools to navigate and act.
            2. If you don't know the selector, use 'inspect_page'.
            3. Do not write code.
            TASK: {user_task}"""

            history = [{"role": "user", "content": full_prompt}]

            for step in range(15):
                if not self.running_event.is_set():
                    await self.queue.put({"type": "info", "content": "⏸️ PAUSED."})
                    await self.running_event.wait()
                
                if self.is_step_mode: 
                    self.running_event.clear()

                await self.queue.put({"type": "thought", "content": "🤔 Thinking..."})
                
                resp_data = await self.llm.query(provider, history, TOOLS_SCHEMA)

                if "error" in resp_data:
                    await self.queue.put({"type": "error", "content": str(resp_data['error'])})
                    break
                
                if "message" not in resp_data: 
                    await self.queue.put({"type": "error", "content": "Invalid LLM Response"})
                    break
                
                msg = resp_data["message"]
                
                assistant_msg = {"role": "assistant", "content": msg.get("content")}
                if msg.get("tool_calls"):
                    assistant_msg["tool_calls"] = msg["tool_calls"]
                history.append(assistant_msg)
                
                if msg.get("tool_calls"):
                    for tool_call in msg["tool_calls"]:
                        fname = tool_call["function"]["name"]
                        fargs = tool_call["function"]["arguments"]
                        call_id = tool_call.get("id") 
                        
                        await self.queue.put({"type": "action", "content": f"🛠️ {fname} {str(fargs)}"})
                        
                        # --- SAFE TOOL EXECUTION ---
                        result = "Tool not found"
                        if hasattr(tools, fname):
                            func = getattr(tools, fname)
                            
                            # Fix parsing
                            if isinstance(fargs, str): 
                                try:
                                    fargs = json.loads(fargs)
                                except:
                                    pass # Keep as string if json fails (rare)

                            # SAFETY CHECK: Handle null arguments
                            if fargs is None:
                                fargs = {}
                                
                            try:
                                result = await func(**fargs)
                            except Exception as e:
                                result = f"Error executing tool: {e}"
                        # ---------------------------
                        
                        if isinstance(result, str) and result.startswith("IMAGE_DATA:"):
                            b64_data = result.replace("IMAGE_DATA:", "")
                            await self.queue.put({"type": "screenshot", "content": b64_data})
                            result = "✅ Screenshot captured successfully."
                        else:
                            await self.queue.put({"type": "result", "content": str(result)[:200]})
                        
                        tool_msg = {
                            "role": "tool",
                            "content": str(result),
                            "name": fname
                        }
                        if call_id:
                            tool_msg["tool_call_id"] = call_id
                        
                        history.append(tool_msg)

                else:
                    content = msg.get("content", "")
                    await self.queue.put({"type": "bot", "content": content})
                    if "TASK_COMPLETED" in content or "done" in content.lower():
                        break 

            await self.queue.put({"type": "info", "content": "Finalizing Recording..."})
            await context.close() 
            await browser.close()
            
            try:
                video_files = [f for f in os.listdir("videos") if f.endswith(".webm")]
                if video_files:
                    latest_video = max([os.path.join("videos", f) for f in video_files], key=os.path.getmtime)
                    video_filename = os.path.basename(latest_video)
                    await self.queue.put({
                        "type": "video_download",
                        "content": f"http://localhost:8000/videos/{video_filename}"
                    })
            except Exception as e:
                await self.queue.put({"type": "error", "content": f"Video Save Error: {e}"})
            
            await self.queue.put({"type": "done", "content": "Session Ended"})

    def _handle_screencast(self, client, event):
        try:
            asyncio.create_task(client.send("Page.screencastFrameAck", {"sessionId": event["sessionId"]}))
            self.queue.put_nowait({"type": "video_frame", "content": event["data"]})
        except: pass