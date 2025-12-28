import os
import time
import json
import re
from types import SimpleNamespace
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from groq import Groq
from openai import OpenAI

load_dotenv()

# --- CONFIGURATION FROM ENV ---
ENV_GEMINI_MODEL = os.getenv("GEMINI_MODEL_NAME", "models/gemini-1.5-flash")
ENV_OPENAI_MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
ENV_GROQ_MODEL = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
ENV_PROVIDER = os.getenv("AI_PROVIDER", "gemini")

# --- DYNAMIC CONFIGURATION STATE ---
_CURRENT_CONFIG = {
    "provider": ENV_PROVIDER,
    "model_name": {
        "gemini": ENV_GEMINI_MODEL,
        "openai": ENV_OPENAI_MODEL,
        "groq": ENV_GROQ_MODEL
    }.get(ENV_PROVIDER, ENV_GEMINI_MODEL)
}

def set_active_model(provider, model_name=None):
    global _CURRENT_CONFIG
    _CURRENT_CONFIG["provider"] = provider
    
    if not model_name:
        if provider == "gemini":
            model_name = os.getenv("GEMINI_MODEL_NAME", "models/gemini-1.5-flash")
        elif provider == "openai":
            model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        elif provider == "groq":
            model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
            
    _CURRENT_CONFIG["model_name"] = model_name
    print(f"\n🔄 Switched AI to: {provider.upper()} ({model_name})")

def get_current_model_info():
    return f"{_CURRENT_CONFIG['provider'].upper()} : {_CURRENT_CONFIG['model_name']}"

def clean_schema(schema):
    if isinstance(schema, dict):
        schema.pop("additionalProperties", None)
        schema.pop("title", None)
        for key, value in schema.items():
            if isinstance(value, (dict, list)):
                clean_schema(value)
    elif isinstance(schema, list):
        for item in schema:
            clean_schema(item)
    return schema

def get_ai_response(messages, tools_schema=None):
    if tools_schema is None:
        tools_schema = []

    active_provider = _CURRENT_CONFIG["provider"]
    model_name = _CURRENT_CONFIG["model_name"]

    print(f"🧠 Thinking ({active_provider} : {model_name})...")

    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:
            if active_provider == "gemini":
                return _call_gemini(messages, tools_schema, model_name)
            elif active_provider == "groq":
                return _call_groq(messages, tools_schema, model_name)
            elif active_provider == "openai":
                return _call_openai(messages, tools_schema, model_name)
            
            raise ValueError(f"Unknown provider: {active_provider}")

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
                attempt += 1
                wait_time = 10 * attempt 
                print(f"\n⏳ Rate Limit Hit. Waiting {wait_time}s before retry ({attempt}/{max_retries})...")
                time.sleep(wait_time)
            elif "404" in error_str:
                print(f"\n❌ Model '{model_name}' not found.")
                raise e
            else:
                # Only log non-groq errors here, Groq errors handled in _call_groq
                if active_provider != "groq":
                    print(f"❌ API Error: {e}")
                raise e

    return None

def _call_gemini(messages, tools_schema, model_name):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    tools = []
    if tools_schema:
        gemini_funcs = []
        for t in tools_schema:
            raw_schema = t.get("inputSchema", t.get("parameters", {}))
            sanitized_schema = clean_schema(raw_schema.copy()) 
            gemini_funcs.append(FunctionDeclaration(name=t["name"], description=t["description"], parameters=sanitized_schema))
        tools = [Tool(function_declarations=gemini_funcs)]
    
    model = genai.GenerativeModel(model_name=model_name, tools=tools)
    gemini_history = []
    for msg in messages:
        role = "user" if msg["role"] in ["user", "system"] else "model"
        parts = []
        if "parts" in msg:
            parts = msg["parts"]
        elif "content" in msg:
            content = msg["content"]
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if item.get("type") == "text": parts.append(item["text"])
                    elif item.get("type") == "image": parts.append({"mime_type": "image/png", "data": item["data"]})
        gemini_history.append({"role": role, "parts": parts})
    
    if len(gemini_history) > 1:
        chat = model.start_chat(history=gemini_history[:-1])
        response = chat.send_message(gemini_history[-1]["parts"])
    else:
        chat = model.start_chat(history=[])
        response = chat.send_message(gemini_history[0]["parts"])
    return response

def _call_groq(messages, tools_schema, model_name):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    groq_tools = []
    if tools_schema:
        for t in tools_schema:
            groq_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("inputSchema", t.get("parameters", {}))
                }
            })

    groq_messages = []
    for m in messages:
        role = m["role"]
        if role == "model": role = "assistant"
        content = ""
        if "content" in m:
            if isinstance(m["content"], str): content = m["content"]
            elif isinstance(m["content"], list): content = " ".join([x["text"] for x in m["content"] if x.get("type") == "text"])
        elif "parts" in m:
            content = " ".join([p for p in m["parts"] if isinstance(p, str)])
        groq_messages.append({"role": role, "content": content})

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=groq_messages,
            tools=groq_tools if groq_tools else None,
            tool_choice="auto" if groq_tools else None
        )
        return response.choices[0].message

    except Exception as e:
        error_str = str(e)
        # --- GROQ ERROR AUTO-FIX v3 (ROBUST) ---
        if "tool_use_failed" in error_str or "failed_generation" in error_str:
            print("   ⚠️ Groq raw tool output detected. Attempting auto-fix...")
            
            # Regex: <function=NAME ... {JSON} ... </function>
            # Matches optional parens ( ) around JSON, allows loose spacing
            match = re.search(r"<function=(\w+)[^\}\{]*(\{.*?\})[^\}\{]*</function>", error_str, re.DOTALL)
            
            if match:
                func_name = match.group(1)
                func_args_str = match.group(2)
                try:
                    json.loads(func_args_str) # Validate
                    print(f"   ✅ Auto-fixed tool call: {func_name}")
                    return SimpleNamespace(
                        role="assistant",
                        content=None,
                        tool_calls=[SimpleNamespace(
                            id="call_autofix_" + str(int(time.time())),
                            type="function",
                            function=SimpleNamespace(name=func_name, arguments=func_args_str)
                        )]
                    )
                except:
                    print("   ❌ Auto-fix failed: Invalid JSON.")
            else:
                print("   ❌ Auto-fix failed: Regex did not match.")
        raise e

def _call_openai(messages, tools_schema, model_name):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    openai_tools = []
    for t in tools_schema:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("inputSchema", t.get("parameters", {}))
            }
        })
    openai_messages = []
    for m in messages:
        role = m["role"]
        if role == "model": role = "assistant"
        content = ""
        if "content" in m:
            content = m["content"]
            if isinstance(content, list): content = " ".join([x["text"] for x in content if x.get("type") == "text"])
        elif "parts" in m: content = " ".join([p for p in m["parts"] if isinstance(p, str)])
        openai_messages.append({"role": role, "content": content})

    response = client.chat.completions.create(
        model=model_name,
        messages=openai_messages,
        tools=openai_tools if openai_tools else None,
        tool_choice="auto" if openai_tools else None
    )
    return response.choices[0].message

def parse_ai_response(response):
    try:
        # 1. Handle GROQ / OPENAI
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_call = response.tool_calls[0]
            return {
                "type": "tool_call",
                "tool_name": tool_call.function.name,
                "tool_args": json.loads(tool_call.function.arguments),
                "raw": response
            }
        elif hasattr(response, 'content') and response.content:
            return {"type": "text", "content": response.content, "raw": response}

        # 2. Handle GEMINI
        part = None
        if hasattr(response, 'candidates'): part = response.candidates[0].content.parts[0]
        elif hasattr(response, 'parts'): part = response.parts[0]
            
        if part:
            if part.function_call:
                return {
                    "type": "tool_call",
                    "tool_name": part.function_call.name,
                    "tool_args": dict(part.function_call.args),
                    "raw": part
                }
            else:
                return {"type": "text", "content": part.text, "raw": part}

    except Exception as e:
        print(f"⚠️ Error parsing AI response object: {e}")
        
    return {"type": "text", "content": "Error parsing response."}