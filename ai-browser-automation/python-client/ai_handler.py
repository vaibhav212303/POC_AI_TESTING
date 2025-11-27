import os
import json
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
active_model = "gemini" 

def get_ai_response(messages, tools_schema):
    print(f"🧠 Thinking using model: {active_model.upper()}...")

    # --- HELPER: Extract just text for non-vision models ---
    def extract_text_only(msgs):
        clean_msgs = []
        for m in msgs:
            content = m["content"]
            if isinstance(content, list):
                # Join all text parts, ignore images
                text_part = " ".join([c["text"] for c in content if c["type"] == "text"])
                clean_msgs.append({"role": m["role"], "content": text_part})
            else:
                clean_msgs.append(m)
        return clean_msgs

    # -------------------------------------------------------
    # 1. OPENAI LOGIC
    # -------------------------------------------------------
    if active_model == "openai":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        openai_tools = []
        for tool in tools_schema:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            })
        
        # Fallback: Strip images for now (unless you use GPT-4o Vision specific format)
        text_messages = extract_text_only(messages)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=text_messages,
            tools=openai_tools,
            tool_choice="auto" 
        )
        return response.choices[0].message

    # -------------------------------------------------------
    # 2. CLAUDE LOGIC
    # -------------------------------------------------------
    elif active_model == "claude":
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        claude_tools = []
        for tool in tools_schema:
            claude_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["inputSchema"]
            })

        # Fallback: Strip images for now
        text_messages = extract_text_only(messages)
        
        system_msg = "You are a browser automation agent."
        user_messages = [m for m in text_messages if m['role'] != 'system']

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_msg,
            messages=user_messages,
            tools=claude_tools
        )
        return response

    # -------------------------------------------------------
    # 3. GEMINI LOGIC (VISION ENABLED)
    # -------------------------------------------------------
    elif active_model == "gemini":
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        gemini_funcs = []
        for tool in tools_schema:
            gemini_funcs.append(
                FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool["inputSchema"]
                )
            )
        
        # Use 1.5 Flash (Fast & Multimodal)
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash', 
            tools=[Tool(function_declarations=gemini_funcs)]
        )

        # CONSTRUCT GEMINI HISTORY
        # We must convert our "agent format" into "Gemini format"
        gemini_history = []
        
        for msg in messages:
            # Map roles: 'user'/'system' -> 'user', 'assistant' -> 'model'
            role = "user" if msg["role"] in ["user", "system"] else "model"
            
            parts = []
            content = msg["content"]

            # Case A: Content is simple text string
            if isinstance(content, str):
                parts.append(content)
            
            # Case B: Content is a list (Text + Image)
            elif isinstance(content, list):
                for item in content:
                    if item["type"] == "text":
                        parts.append(item["text"])
                    elif item["type"] == "image":
                        # This is where the magic happens
                        parts.append({
                            "mime_type": "image/png",
                            "data": item["data"] # Base64 string
                        })

            gemini_history.append({"role": role, "parts": parts})

        # Execute Chat
        # If we have history, load it. If not, start fresh.
        if len(gemini_history) > 1:
            # All messages except the last one are history
            chat = model.start_chat(history=gemini_history[:-1])
            # The last message is the new prompt
            last_msg = gemini_history[-1]["parts"]
            response = chat.send_message(last_msg)
        else:
            # Only 1 message exists
            chat = model.start_chat(history=[])
            response = chat.send_message(gemini_history[0]["parts"])
        
        return response

    else:
        raise ValueError(f"Unknown model: {active_model}")