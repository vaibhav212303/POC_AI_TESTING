import os
import json
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from dotenv import load_dotenv

load_dotenv()

# Configuration
ACTIVE_MODEL = "gemini" 

def get_ai_response(messages, tools_schema=None):
    """
    Unified AI Request Handler (Text + Vision).
    """
    if tools_schema is None:
        tools_schema = []

    print(f"🧠 Thinking ({ACTIVE_MODEL})...")

    if ACTIVE_MODEL == "gemini":
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # 1. Setup Tools
        tools = []
        if tools_schema:
            gemini_funcs = [
                FunctionDeclaration(
                    name=t["name"], 
                    description=t["description"], 
                    parameters=t["inputSchema"]
                ) for t in tools_schema
            ]
            tools = [Tool(function_declarations=gemini_funcs)]

        model = genai.GenerativeModel(model_name='gemini-2.0-flash', tools=tools)

        # 2. Format History for Gemini (Text + Images)
        gemini_history = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            parts = []
            
            content = msg["content"]
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if item["type"] == "text":
                        parts.append(item["text"])
                    elif item["type"] == "image":
                        parts.append({
                            "mime_type": "image/png",
                            "data": item["data"]
                        })
            gemini_history.append({"role": role, "parts": parts})

        # 3. Send Request
        if len(gemini_history) > 1:
            chat = model.start_chat(history=gemini_history[:-1])
            response = chat.send_message(gemini_history[-1]["parts"])
        else:
            chat = model.start_chat(history=[])
            response = chat.send_message(gemini_history[0]["parts"])
        
        return response

    elif ACTIVE_MODEL == "openai":
        # (OpenAI Implementation omitted for brevity - same as before)
        pass

    return None

def parse_ai_response(response):
    """Standardizes response format across models."""
    try:
        if ACTIVE_MODEL == "gemini":
            candidate = response.candidates[0]
            part = candidate.content.parts[0]
            if part.function_call:
                return {
                    "type": "tool_call",
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args)
                }
            return { "type": "text", "content": part.text }
    except Exception as e:
        return { "type": "text", "content": f"Error parsing: {e}" }