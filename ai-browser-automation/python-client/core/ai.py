import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

load_dotenv()

# Configuration
ACTIVE_MODEL = "gemini" 

def clean_schema(schema):
    """
    Recursively removes 'additionalProperties' and 'title' fields from the schema,
    as Gemini API rejects them.
    """
    if isinstance(schema, dict):
        # Remove unsupported keys
        schema.pop("additionalProperties", None)
        schema.pop("title", None)
        
        # Recurse into common nested structures
        for key, value in schema.items():
            if isinstance(value, (dict, list)):
                clean_schema(value)
                
    elif isinstance(schema, list):
        for item in schema:
            clean_schema(item)
            
    return schema

def get_ai_response(messages, tools_schema=None):
    """
    Unified AI Request Handler.
    Handles both 'content' (OpenAI style) and 'parts' (Gemini style) in messages.
    """
    
    if tools_schema is None:
        tools_schema = []

    print(f"🧠 Thinking ({ACTIVE_MODEL})...")

    if ACTIVE_MODEL == "gemini":
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # 1. Setup Tools
        tools = []
        if tools_schema:
            gemini_funcs = []
            for t in tools_schema:
                # --- FIX: CLEAN THE SCHEMA ---
                raw_schema = t.get("inputSchema", t.get("parameters", {}))
                sanitized_schema = clean_schema(raw_schema.copy()) 
                
                gemini_funcs.append(
                    FunctionDeclaration(
                        name=t["name"], 
                        description=t["description"], 
                        parameters=sanitized_schema
                    )
                )
            tools = [Tool(function_declarations=gemini_funcs)]

        model = genai.GenerativeModel(model_name='gemini-2.0-flash', tools=tools)

        # 2. Format History for Gemini
        gemini_history = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            parts = []
            
            # --- Support both 'parts' and 'content' keys ---
            if "parts" in msg:
                # Caller already provided Gemini format
                parts = msg["parts"]
            elif "content" in msg:
                # Convert OpenAI format to Gemini
                content = msg["content"]
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for item in content:
                        if item.get("type") == "text":
                            parts.append(item["text"])
            
            gemini_history.append({"role": role, "parts": parts})

        # 3. Send Request
        # We separate the history (context) from the new message (prompt)
        try:
            if len(gemini_history) > 1:
                chat_history = gemini_history[:-1]
                last_message = gemini_history[-1]["parts"]
                
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(last_message)
            else:
                chat = model.start_chat(history=[])
                response = chat.send_message(gemini_history[0]["parts"])
            
            return response
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            raise e

    return None