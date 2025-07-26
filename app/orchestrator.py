import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from anthropic import Anthropic
from .prompts import ROLE_PROMPTS

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# In-memory state (one global for now)
conversation_history = []  # List of dicts: {"role": "user/agent", "agent": "catalyst", "content": "..."}
AGENTS = ["catalyst", "anchor", "weaver"]

def build_context(agent_name: str) -> str:
    """
    Build a context string for Claude that includes:
    - This agent's role prompt
    - Relevant conversation history
    """
    role_instruction = ROLE_PROMPTS[agent_name]
    history_text = ""
    for msg in conversation_history:
        prefix = f"{msg['agent']}:" if msg['role'] == "agent" else "User:"
        history_text += f"{prefix} {msg['content']}\n"
    return f"{role_instruction}\n\nConversation so far:\n{history_text}\n\nYour response:"

def call_claude(prompt: str, temperature: float):
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=400,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def run_orchestration(user_message: str, temperature: float = 0.7):
    conversation_history.append({"role": "user", "agent": "user", "content": user_message})
    results = []
    for agent in AGENTS:
        prompt = build_context(agent)
        reply = call_claude(prompt, temperature)
        conversation_history.append({"role": "agent", "agent": agent, "content": reply})
        results.append({"agent": agent, "reply": reply})
    return results

