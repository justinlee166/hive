import os
import random
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from anthropic import Anthropic
from .prompts import ROLE_PROMPTS, CONVERSATION_PROMPTS

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# In-memory state (one global for now)
conversation_history = []  # List of dicts: {"role": "user/agent", "agent": "catalyst", "content": "..."}
AGENTS = ["catalyst", "anchor", "weaver"]

def build_context(agent_name: str, conversation_phase: str = "initial_response") -> str:
    """
    Build a context string for Claude that includes:
    - This agent's role prompt
    - Relevant conversation history
    - Phase-specific instructions
    """
    role_instruction = ROLE_PROMPTS[agent_name]
    phase_instruction = CONVERSATION_PROMPTS.get(conversation_phase, CONVERSATION_PROMPTS["initial_response"])
    
    # Build conversation history WITHOUT agent names to prevent mimicking
    history_text = ""
    recent_messages = conversation_history[-20:]  # Limit context to recent messages
    for msg in recent_messages:
        if msg['role'] == "user":
            history_text += f"User: {msg['content']}\n"
        else:
            # Don't include agent names in history to prevent self-labeling
            history_text += f"Previous response: {msg['content']}\n"
    
    if history_text:
        return f"{role_instruction}\n\nConversation so far:\n{history_text}\n{phase_instruction}"
    else:
        return f"{role_instruction}\n\n{phase_instruction}"

def build_enhanced_context(agent_name: str, conversation_phase: str = "autonomous_discussion", round_number: int = 1) -> str:
    """
    Enhanced context building for multi-turn autonomous discussions
    """
    role_instruction = ROLE_PROMPTS[agent_name]
    
    # Get recent conversation for context WITHOUT agent names
    recent_messages = conversation_history[-15:]  # Focus on recent discussion
    history_text = ""
    for msg in recent_messages:
        if msg['role'] == "user":
            history_text += f"User: {msg['content']}\n"
        else:
            # Don't include agent names in history to prevent self-labeling
            history_text += f"Previous response: {msg['content']}\n"
    
    # Phase-specific instructions
    if conversation_phase == "final_round":
        phase_instruction = CONVERSATION_PROMPTS["final_round"]
    else:
        phase_instruction = f"{CONVERSATION_PROMPTS['autonomous_discussion']} (Discussion round {round_number})"
    
    return f"{role_instruction}\n\nRecent conversation:\n{history_text}\n{phase_instruction}"

def call_claude_with_personality(agent_name: str, prompt: str, temperature: float):
    """
    Call Claude with agent-specific parameters to ensure distinct personalities
    """
    # Different temperature settings for each agent to create variety
    agent_temperatures = {
        "catalyst": min(temperature + 0.2, 1.0),  # Higher creativity for bold ideas
        "anchor": max(temperature - 0.1, 0.1),    # Lower creativity for practical responses
        "weaver": temperature                      # Balanced for synthesis
    }
    
    # Different max tokens for varied response lengths
    agent_max_tokens = {
        "catalyst": 300,  # Shorter, punchier responses
        "anchor": 350,    # Longer for detailed analysis
        "weaver": 320     # Balanced for integration
    }
    
    # Natural system messages that don't encourage self-labeling
    system_messages = {
        "catalyst": "You are bold and visionary. Always think big and push for transformative action. Be direct and inspiring.",
        "anchor": "You are practical and grounded. Always focus on feasibility and concrete execution. Be thorough and realistic.",
        "weaver": "You are a strategic synthesizer. Always find connections between ideas and propose balanced integration. Be collaborative."
    }
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=agent_max_tokens[agent_name],
        temperature=agent_temperatures[agent_name],
        system=system_messages[agent_name],
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()

def call_claude(prompt: str, temperature: float):
    # For backward compatibility, use default agent
    return call_claude_with_personality("weaver", prompt, temperature)

def run_orchestration(user_message: str, temperature: float = 0.7):
    conversation_history.append({"role": "user", "agent": "user", "content": user_message})
    results = []
    for agent in AGENTS:
        prompt = build_context(agent)
        reply = call_claude_with_personality(agent, prompt, temperature)
        conversation_history.append({"role": "agent", "agent": agent, "content": reply})
        results.append({"agent": agent, "reply": reply})
    return results

async def run_streaming_orchestration(user_message: str, temperature: float = 0.7):
    """
    Streaming version with personality-aware Claude calls
    """
    conversation_history.append({"role": "user", "agent": "user", "content": user_message})
    
    agents_order = AGENTS.copy()
    random.shuffle(agents_order)
    
    for agent in agents_order:
        typing_event = {
            "role": "agent",
            "agent": agent,
            "content": None,
            "status": "typing"
        }
        yield typing_event
        
        # Use personality-aware Claude call
        prompt = build_context(agent, "initial_response")
        reply = call_claude_with_personality(agent, prompt, temperature)
        
        conversation_history.append({"role": "agent", "agent": agent, "content": reply})
        
        done_event = {
            "role": "agent",
            "agent": agent,
            "content": reply,
            "status": "done"
        }
        yield done_event

def check_for_user_input_request(content: str) -> bool:
    """
    Check if an agent's response naturally requests user input
    """
    request_indicators = [
        "what do you think", "your thoughts", "what are your", "how do you feel",
        "what's your view", "your perspective", "what would you", "your opinion",
        "user input", "user's thoughts", "hear from you", "what do you see"
    ]
    content_lower = content.lower()
    return any(indicator in content_lower for indicator in request_indicators)

