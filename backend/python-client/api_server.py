import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# --- CHANGE THIS IMPORT ---
from core.agent_engine import AgentEngine 
# --------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Client connected")

    # Use the new generic class name
    agent = AgentEngine() 
    success = await agent.initialize()
    
    if not success:
        await websocket.send_json({"type": "error", "content": "Failed to connect to Playwright Server"})
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            user_message = payload.get("message")
            config = payload.get("config", {}) 

            async for event in agent.process_message(
                user_message, 
                provider=config.get("provider", "gemini"),
                model=config.get("model", "models/gemini-1.5-flash")
            ):
                await websocket.send_json(event)
                
            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("👋 Client disconnected")
        await agent.shutdown()
    except Exception as e:
        print(f"Server Error: {e}")
        await agent.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)