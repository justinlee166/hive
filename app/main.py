from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import asyncio
import random
from .orchestrator import (
    run_orchestration, run_streaming_orchestration, conversation_history, 
    AGENTS, build_enhanced_context, call_claude_with_personality, check_for_user_input_request
)

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

async def conduct_concise_discussion(websocket: WebSocket, temperature: float, max_rounds: int = 4):
    """
    Conduct concise multi-turn autonomous discussion between agents
    """
    for round_num in range(1, max_rounds + 1):
        print(f"🔄 Concise discussion round {round_num}/{max_rounds}")
        
        # Randomize agent order for each round  
        agents_order = AGENTS.copy()
        random.shuffle(agents_order)
        
        round_requested_user_input = False
        
        for agent_idx, agent in enumerate(agents_order):
            is_final_agent_in_round = agent_idx == len(agents_order) - 1
            is_final_round = round_num == max_rounds
            
            # Send typing indicator
            await websocket.send_json({
                "role": "agent",
                "agent": agent,
                "content": None,
                "status": "typing"
            })
            
            try:
                # Choose conversation phase based on position
                if is_final_round and is_final_agent_in_round:
                    conversation_phase = "final_round"
                else:
                    conversation_phase = "autonomous_discussion"
                
                # Generate concise response with enhanced context
                prompt = build_enhanced_context(agent, conversation_phase, round_num)
                # Add specific instruction for conciseness
                concise_prompt = f"{prompt}\n\nIMPORTANT: Keep your response to 1-2 sentences maximum. Be direct and impactful."
                
                reply = call_claude_with_personality(agent, concise_prompt, temperature)
                
                # Add to conversation history
                conversation_history.append({"role": "agent", "agent": agent, "content": reply})
                
                # Send completed response
                await websocket.send_json({
                    "role": "agent",
                    "agent": agent,
                    "content": reply,
                    "status": "done"
                })
                
                # Check if this agent naturally requested user input
                if check_for_user_input_request(reply):
                    print(f"🎯 {agent} naturally requested user input")
                    round_requested_user_input = True
                    break
                
            except Exception as e:
                # Fallback response
                print(f"❌ Error generating response for {agent}: {e}")
                reply = f"Technical difficulties aside, let's continue this discussion."
                conversation_history.append({"role": "agent", "agent": agent, "content": reply})
                await websocket.send_json({
                    "role": "agent",
                    "agent": agent,
                    "content": reply,
                    "status": "done"
                })
            
            # Shorter delay for concise conversation flow
            await asyncio.sleep(0.6)
        
        # If an agent requested user input or we've reached max rounds, stop
        if round_requested_user_input or round_num == max_rounds:
            print(f"⏸️ Concise discussion concluded after {round_num} rounds")
            break
        
        # Brief pause between rounds
        await asyncio.sleep(0.3)

@app.websocket("/ws-chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive the user's message with optional autonomous_rounds parameter
            data = await websocket.receive_json()
            user_msg = data["message"]
            temperature = data.get("temperature", 0.7)
            autonomous_rounds = data.get("autonomous_rounds", 4)  # Default to 4 rounds
            
            # Validate autonomous_rounds range
            autonomous_rounds = max(2, min(8, autonomous_rounds))
            
            print(f"📝 User message received, will conduct {autonomous_rounds} autonomous rounds")
            
            # Add user message to conversation history
            conversation_history.append({"role": "user", "agent": "user", "content": user_msg})
            
            # Send user message back immediately
            await websocket.send_json({
                "role": "user",
                "agent": "user", 
                "content": user_msg
            })
            
            # === INITIAL ROUND: Each agent responds once ===
            print("🚀 Starting concise initial responses...")
            
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
                    from .orchestrator import build_context
                    prompt = build_context(agent, "initial_response")
                    # Add conciseness instruction
                    concise_prompt = f"{prompt}\n\nIMPORTANT: Keep your response to 1-2 sentences maximum. Be direct and focused."
                    
                    reply = call_claude_with_personality(agent, concise_prompt, temperature)
                    
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
                    reply = f"Technical issues aside, let me share my perspective on this."
                    conversation_history.append({"role": "agent", "agent": agent, "content": reply})
                    await websocket.send_json({
                        "role": "agent",
                        "agent": agent,
                        "content": reply,
                        "status": "done"
                    })
                
                # Wait before next agent
                await asyncio.sleep(1.0)
            
            # === CONCISE AUTONOMOUS DISCUSSION ===
            print(f"🤖 Starting {autonomous_rounds} rounds of concise autonomous discussion...")
            await asyncio.sleep(0.8)  # Brief pause before autonomous discussion
            
            # Conduct concise multi-turn discussion with user-specified rounds
            await conduct_concise_discussion(websocket, temperature, max_rounds=autonomous_rounds)
            
            # === PAUSE FOR USER INPUT ===
            print("⏸️ Concise discussion complete, awaiting user input...")
            
            # Send awaiting user status
            await websocket.send_json({
                "status": "awaiting_user",
                "message": "Your turn! What's your take on this?"
            })
                
    except WebSocketDisconnect:
        print("👋 WebSocket client disconnected")
        pass

@app.get("/history")
def get_history():
    return {"history": conversation_history}
