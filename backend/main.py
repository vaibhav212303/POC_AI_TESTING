import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # <--- NEW IMPORT
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from agent_service import AgentService

app = FastAPI()

# 1. Mount the videos directory to serve files
# This makes files in /videos accessible via http://localhost:8000/videos/filename.webm
os.makedirs("videos", exist_ok=True)
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

app.add_middleware(
   CORSMiddleware,
    # In V1, allow all. In V2, restrict to your Vercel domain.
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (Keep existing global active_agent and ControlRequest) ...
active_agent: AgentService | None = None

class ControlRequest(BaseModel):
    command: str

@app.get("/stream-task")
async def stream_task(task: str, model: str = "ollama"):
    global active_agent
    active_agent = AgentService()
    
    async def event_generator():
        try:
            async for event in active_agent.run_task(task, provider=model):
                yield json.dumps(event)
        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)})

    return EventSourceResponse(event_generator())

@app.post("/control")
async def control_agent(req: ControlRequest):
    global active_agent
    if not active_agent:
        raise HTTPException(status_code=400, detail="No active agent running")

    if req.command == "pause":
        active_agent.pause()
        return {"status": "paused"}
    elif req.command == "resume":
        active_agent.resume()
        return {"status": "resumed"}
    elif req.command == "step":
        active_agent.step()
        return {"status": "stepping"}
    
    raise HTTPException(status_code=400, detail="Invalid command")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)