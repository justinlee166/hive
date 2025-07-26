from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import time
import asyncio
from .orchestrator import run_orchestration, run_streaming_orchestration, conversation_history

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    temperature: float = 0.7  # new field

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    responses = run_orchestration(req.message, req.temperature)
    return {"responses": responses, "history": conversation_history}

@app.post("/chat-stream")
async def chat_stream_endpoint(req: ChatRequest):
    """
    Streaming endpoint that yields agent responses one by one as they're ready
    """
    async def generate_stream():
        # First, yield the user's message immediately
        user_event = {
            "role": "user",
            "agent": "user", 
            "content": req.message
        }
        yield f"data: {json.dumps(user_event)}\n\n"
        
        # Small pause before agents start responding
        await asyncio.sleep(0.5)
        
        # Generate and yield each agent response progressively
        async for agent_response in run_streaming_orchestration(req.message, req.temperature):
            yield f"data: {json.dumps(agent_response)}\n\n"
            # Natural pause between agent responses (1-2 seconds)
            await asyncio.sleep(1.5)
        
        # Send final event to indicate completion
        yield f"data: {json.dumps({'event': 'complete'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/history")
def get_history():
    return {"history": conversation_history}
