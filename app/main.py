from fastapi import FastAPI
from pydantic import BaseModel
from .orchestrator import run_orchestration, conversation_history

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    responses = run_orchestration(req.message)
    return {"responses": responses, "history": conversation_history}

@app.get("/history")
def get_history():
    return {"history": conversation_history}
