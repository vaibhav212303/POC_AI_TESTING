import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- IMPORTS FROM YOUR CORE LOGIC ---
from core.agent_engine import AgentEngine
from core.ai import get_ai_response, parse_ai_response, set_active_model

app = FastAPI()

# Enable CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class StepGenRequest(BaseModel):
    prompt: str
    provider: str = "gemini"
    model: str = "models/gemini-2.5-flash"

class TestCaseSaveRequest(BaseModel):
    filename: str
    content: dict

# ==========================================
# 1. WEBSOCKET ENDPOINT (Chat Interface)
# ==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Client connected")

    # Initialize the Agent
    agent = AgentEngine() 
    success = await agent.initialize()
    
    if not success:
        await websocket.send_json({"type": "error", "content": "Failed to connect to Playwright Server"})
        await websocket.close()
        return

    try:
        while True:
            # Wait for message from Frontend
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            user_message = payload.get("message")
            config = payload.get("config", {}) 

            # Stream response events
            async for event in agent.process_message(
                user_message, 
                provider=config.get("provider", "gemini"),
                model=config.get("model", "models/gemini-2.5-flash")
            ):
                await websocket.send_json(event)
                
            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("👋 Client disconnected")
        await agent.shutdown()
    except Exception as e:
        print(f"Server Error: {e}")
        await agent.shutdown()

# ==========================================
# 2. HTTP ENDPOINTS (Test Builder)
# ==========================================

@app.post("/api/generate-steps")
async def generate_test_steps(request: StepGenRequest):
    """
    Uses AI to convert natural language (e.g. 'Login with admin') 
    into a structured JSON list of steps.
    """
    print(f"✨ Generating steps using {request.provider}...")
    
    # 1. Configure Model
    set_active_model(request.provider, request.model)
    
    # 2. Construct Prompt
    prompt = f"""
    You are a QA Automation Expert. Convert the user's intent into a JSON array of Test Steps.
    
    USER INTENT: "{request.prompt}"
    
    OUTPUT FORMAT (JSON Array only):
    [
      {{ "id": "gen_1", "action": "navigate", "value": "https://example.com", "description": "Open site", "selector": "" }},
      {{ "id": "gen_2", "action": "fill", "selector": "#user", "value": "test", "description": "Enter user" }},
      {{ "id": "gen_3", "action": "click", "selector": "#btn", "value": "", "description": "Click button" }}
    ]
    
    VALID ACTIONS: navigate, click, fill, check, wait.
    RULES:
    1. If the user mentions a specific URL, use 'navigate'.
    2. Make educated guesses for selectors (ids, data-test attributes) if not provided.
    3. RETURN ONLY RAW JSON. NO MARKDOWN.
    """
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # 3. Call AI
        raw_response = get_ai_response(messages)
        parsed = parse_ai_response(raw_response)
        content = parsed["content"]
        
        # 4. Clean Markdown Code Blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        # 5. Parse JSON
        steps = json.loads(content.strip())
        return {"steps": steps}
        
    except Exception as e:
        print(f"❌ Generation Error: {e}")
        return {"steps": [], "error": str(e)}

@app.post("/api/save-testcase")
async def save_testcase(request: TestCaseSaveRequest):
    """
    Saves the JSON built in the frontend to the backend file system.
    """
    try:
        # Determine Path: ../playwright-server/manual_cases/
        # Adjust base_dir logic depending on where you run python from
        base_dir = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server/manual_cases"))
        
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            
        file_path = os.path.join(base_dir, request.filename)
        
        print(f"💾 Saving test case to: {file_path}")
        
        with open(file_path, "w") as f:
            json.dump(request.content, f, indent=2)
            
        return {"status": "success", "path": file_path}
        
    except Exception as e:
        print(f"❌ Save Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Reload=True helps during development
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)