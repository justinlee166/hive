from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import asyncio
import random
from .orchestrator import run_orchestration, run_streaming_orchestration, conversation_history, AGENTS, build_context, call_claude

app = FastAPI()

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    temperature: float = 0.7

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

async def conduct_autonomous_discussion(websocket: WebSocket, temperature: float, max_rounds: int = 3):
    """
    Conduct multi-turn autonomous discussion between agents
    """
    for round_num in range(max_rounds):
        print(f"🔄 Starting autonomous round {round_num + 1}/{max_rounds}")
        
        # Randomize agent order for each round
        agents_order = AGENTS.copy()
        random.shuffle(agents_order)
        
        for agent in agents_order:
            # Send typing indicator
            await websocket.send_json({
                "role": "agent",
                "agent": agent,
                "content": None,
                "status": "typing"
            })
            
            # Generate autonomous response based on updated conversation history
            try:
                prompt = build_context(agent)
                # Add instruction for autonomous discussion
                autonomous_prompt = f"{prompt}\n\nContinue the discussion with the other agents. Build upon their previous points and add your perspective. Keep your response concise (1-2 sentences) and engaging."
                
                reply = call_claude(autonomous_prompt, temperature)
                
                # Add to conversation history
                conversation_history.append({"role": "agent", "agent": agent, "content": reply})
                
                # Send completed response
                await websocket.send_json({
                    "role": "agent",
                    "agent": agent,
                    "content": reply,
                    "status": "done"
                })
                
            except Exception as e:
                # Fallback response if Claude API fails
                reply = f"I'm {agent}, continuing our discussion... (experiencing technical difficulties)"
                conversation_history.append({"role": "agent", "agent": agent, "content": reply})
                await websocket.send_json({
                    "role": "agent",
                    "agent": agent,
                    "content": reply,
                    "status": "done"
                })
            
            # Shorter delay between autonomous responses for natural flow
            await asyncio.sleep(1.0)
        
        # Pause between rounds
        await asyncio.sleep(0.5)

@app.websocket("/ws-chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive the user's message
            data = await websocket.receive_json()
            user_msg = data["message"]
            temperature = data.get("temperature", 0.7)
            
            # Add user message to conversation history
            conversation_history.append({"role": "user", "agent": "user", "content": user_msg})
            
            # Send user message back immediately
            await websocket.send_json({
                "role": "user",
                "agent": "user", 
                "content": user_msg
            })
            
            # === INITIAL ROUND: Each agent responds once ===
            print("🚀 Starting initial agent responses...")
            
            # Randomize agent order for initial responses
            agents_order = AGENTS.copy()
            random.shuffle(agents_order)
            
            # Process each agent's initial response
            for agent in agents_order:
                # Send typing indicator
                await websocket.send_json({
                    "role": "agent",
                    "agent": agent,
                    "content": None,
                    "status": "typing"
                })
                
                # Generate initial response
                try:
                    prompt = build_context(agent)
                    reply = call_claude(prompt, temperature)
                    
                    # Add to conversation history
                    conversation_history.append({"role": "agent", "agent": agent, "content": reply})
                    
                    # Send completed response
                    await websocket.send_json({
                        "role": "agent",
                        "agent": agent,
                        "content": reply,
                        "status": "done"
                    })
                    
                except Exception as e:
                    # Fallback response if Claude API fails
                    reply = f"I'm {agent}, and I'm experiencing some technical difficulties. Please try again!"
                    conversation_history.append({"role": "agent", "agent": agent, "content": reply})
                    await websocket.send_json({
                        "role": "agent",
                        "agent": agent,
                        "content": reply,
                        "status": "done"
                    })
                
                # Wait before next agent
                await asyncio.sleep(1.5)
            
            # === AUTONOMOUS DISCUSSION ROUNDS ===
            print("🤖 Starting autonomous discussion rounds...")
            await asyncio.sleep(1.0)  # Brief pause before autonomous discussion
            
            # Conduct multiple rounds of autonomous discussion
            await conduct_autonomous_discussion(websocket, temperature, max_rounds=3)
            
            # === PAUSE FOR USER INPUT ===
            print("⏸️ Autonomous discussion complete, awaiting user input...")
            
            # Send awaiting user status
            await websocket.send_json({
                "status": "awaiting_user",
                "message": "The agents have paused their discussion and are waiting for your input..."
            })
                
    except WebSocketDisconnect:
        print("👋 WebSocket client disconnected")
        pass

@app.get("/history")
def get_history():
    return {"history": conversation_history}
