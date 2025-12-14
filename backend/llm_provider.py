import os
import json
import re
import httpx
import google.generativeai as genai
from openai import AsyncOpenAI
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

class LLMProvider:
    def __init__(self):
        # 1. Gemini
        self.gemini_available = False
        if os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.gemini_available = True
        
        # 2. Ollama
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/chat")
        
        # 3. Grok (xAI)
        self.grok_client = None
        if os.getenv("XAI_API_KEY"):
            self.grok_client = AsyncOpenAI(api_key=os.getenv("XAI_API_KEY"), base_url="https://api.x.ai/v1")

        # 4. Groq (LPU)
        self.groq_client = None
        if os.getenv("GROQ_API_KEY"):
            self.groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    async def query(self, provider: str, messages: list, tools: list):
        print(f"🧠 Querying {provider.upper()}...")
        if provider == "gemini": return await self._query_gemini(messages, tools)
        elif provider == "grok": return await self._query_grok(messages, tools)
        elif provider == "groq": return await self._query_groq_lpu(messages, tools)
        else: return await self._query_ollama(messages, tools)

    # --- GROQ (LPU) ---
    async def _query_groq_lpu(self, messages: list, tools: list):
        if not self.groq_client: return {"error": "GROQ_API_KEY missing"}
        try:
            response = await self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages, tools=tools, tool_choice="auto", temperature=0.0
            )
            return self._normalize_openai_response(response)
        except Exception as e:
            return self._handle_groq_error(str(e))

    # --- GROK (xAI) ---
    async def _query_grok(self, messages: list, tools: list):
        if not self.grok_client: return {"error": "XAI_API_KEY missing"}
        try:
            response = await self.grok_client.chat.completions.create(
                model="grok-beta",
                messages=messages, tools=tools, tool_choice="auto", temperature=0.0
            )
            return self._normalize_openai_response(response)
        except Exception as e:
            return {"error": f"xAI Error: {str(e)}"}

    # --- OLLAMA ---
    async def _query_ollama(self, messages: list, tools: list):
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # Sanitize messages
                sanitized_msgs = []
                for m in messages:
                    msg_copy = m.copy()
                    # Ollama doesn't strictly require 'type': 'function' yet, but good to have
                    if msg_copy.get("tool_calls"):
                         # Ensure Ollama sees the format it expects (often cleaner without 'type' for some versions, 
                         # but standard is aligning). 
                         # For now, pass as is, assuming Ollama handles standard dicts.
                         if msg_copy.get("content") is None:
                             msg_copy["content"] = ""
                    sanitized_msgs.append(msg_copy)

                response = await client.post(self.ollama_url, json={
                    "model": "llama3.2:latest", 
                    "messages": sanitized_msgs, 
                    "tools": tools, 
                    "stream": False, 
                    "options": {"temperature": 0}
                })
                return response.json()
            except Exception as e:
                return {"error": f"Ollama Error: {str(e)}"}

    # --- GEMINI ---
    async def _query_gemini(self, messages: list, tools: list):
        if not self.gemini_available: return {"error": "GEMINI_API_KEY missing"}
        try:
            gemini_tools = self._convert_tools_to_gemini(tools)
            system_instruction = next((m["content"] for m in messages if m["role"] == "system"), None)
            chat_history = self._convert_messages_to_gemini([m for m in messages if m["role"] != "system"])
            
            model = genai.GenerativeModel('gemini-1.5-flash', tools=gemini_tools, system_instruction=system_instruction)
            
            if not chat_history: return {"error": "No messages"}
            last_msg = chat_history.pop()
            
            chat = model.start_chat(history=chat_history)
            response = await chat.send_message_async(last_msg["parts"])
            return self._normalize_gemini_response(response)
        except Exception as e:
            return {"error": f"Gemini Error: {str(e)}"}

    # --- HELPERS ---
    def _normalize_openai_response(self, response):
        """Standardizes OpenAI/Groq/Grok responses"""
        msg = response.choices[0].message
        result = {"message": {"role": "assistant", "content": msg.content}}
        
        if msg.tool_calls:
            result["message"]["tool_calls"] = []
            for tc in msg.tool_calls:
                result["message"]["tool_calls"].append({
                    "id": tc.id,
                    "type": "function", # <--- ✅ CRITICAL FIX: Added type property
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments 
                    }
                })
        return result

    def _handle_groq_error(self, error_str):
        # Auto-fix for Llama 3.3 raw text output
        if "tool_use_failed" in error_str and "failed_generation" in error_str:
            match = re.search(r"<function=(\w+)(.*?)</function>", error_str)
            if match:
                func_name, func_args_raw = match.group(1), match.group(2)
                try:
                    json.loads(func_args_raw) 
                    return {
                        "message": {
                            "role": "assistant", 
                            "content": None,
                            "tool_calls": [{
                                "id": "call_autofix_" + func_name,
                                "type": "function", # <--- ✅ CRITICAL FIX: Added type property
                                "function": {"name": func_name, "arguments": func_args_raw}
                            }]
                        }
                    }
                except: pass
        return {"error": f"Groq Error: {error_str}"}

    def _convert_tools_to_gemini(self, tools):
        declarations = []
        for t in tools:
            declarations.append({
                "name": t["function"]["name"],
                "description": t["function"]["description"],
                "parameters": t["function"]["parameters"]
            })
        return [{"function_declarations": declarations}]

    def _convert_messages_to_gemini(self, messages):
        history = []
        for m in messages:
            role = "user" if m["role"] in ["user", "tool"] else "model"
            parts = []
            if m.get("content"): parts.append(m["content"])
            if m["role"] == "tool":
                parts = [f"Observation from tool ({m.get('name', 'unknown')}): {m['content']}"]
            if parts:
                history.append({"role": role, "parts": parts})
        return history

    def _normalize_gemini_response(self, response):
        result = {"message": {"role": "assistant", "content": ""}}
        for part in response.candidates[0].content.parts:
            if fn := part.function_call:
                result["message"]["tool_calls"] = [{
                    "id": "call_gemini_" + fn.name,
                    "type": "function", # <--- ✅ Added for consistency
                    "function": {
                        "name": fn.name, 
                        "arguments": json.dumps(dict(fn.args)) 
                    }
                }]
                return result
            if part.text: result["message"]["content"] += part.text
        return result