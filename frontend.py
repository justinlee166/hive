import streamlit as st
import requests
import json

API_URL = "http://127.0.0.1:8000/chat-stream"

st.set_page_config(page_title="Hive", layout="centered")

st.title("Hive – Multi-Agent Collective")

AGENT_COLORS = {
    "catalyst": "#FFB347",  # orange
    "anchor": "#77DD77",    # green
    "weaver": "#779ECB",    # blue
    "user": "#D3D3D3"       # light gray
}

if st.button("Reset Conversation"):
    st.session_state.history = []

# Sidebar controls
st.sidebar.header("Controls")
temperature = st.sidebar.slider("Creativity (temperature)", 0.0, 1.0, 0.7, 0.05)

# Store chat history in Streamlit session
if "history" not in st.session_state:
    st.session_state.history = []

# Initialize streaming state
if "streaming" not in st.session_state:
    st.session_state.streaming = False

# Chat input
user_input = st.text_input("Type a message", "", disabled=st.session_state.streaming)

if st.button("Send", disabled=st.session_state.streaming):
    if user_input.strip():
        st.session_state.streaming = True
        
        payload = {
            "message": user_input,
            "temperature": temperature
        }
        
        try:
            # Send streaming request to FastAPI backend
            with requests.post(API_URL, json=payload, stream=True) as response:
                response.raise_for_status()
                
                # Process each line from the stream
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        # Parse Server-Sent Events format
                        if line_str.startswith('data: '):
                            try:
                                event_data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                                
                                # Check if it's the completion event
                                if event_data.get('event') == 'complete':
                                    break
                                
                                # Handle typing and done events
                                status = event_data.get('status')
                                agent = event_data.get('agent')
                                
                                if status == 'typing':
                                    # Add typing placeholder to history
                                    typing_message = {
                                        "role": "agent",
                                        "agent": agent,
                                        "content": "is typing...",
                                        "is_typing": True
                                    }
                                    st.session_state.history.append(typing_message)
                                    st.rerun()
                                
                                elif status == 'done':
                                    # Find and replace the typing placeholder with actual content
                                    for i in range(len(st.session_state.history) - 1, -1, -1):
                                        msg = st.session_state.history[i]
                                        if (msg.get("agent") == agent and 
                                            msg.get("is_typing") == True):
                                            # Replace typing placeholder with actual message
                                            st.session_state.history[i] = {
                                                "role": event_data["role"],
                                                "agent": event_data["agent"],
                                                "content": event_data["content"]
                                            }
                                            break
                                    st.rerun()
                                
                                else:
                                    # Handle user messages and other events without status
                                    if not status:  # No status means it's a user message
                                        st.session_state.history.append(event_data)
                                        st.rerun()
                                
                            except json.JSONDecodeError:
                                continue
                            except Exception as e:
                                st.error(f"Error processing stream: {e}")
                                break
                                
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
        finally:
            st.session_state.streaming = False
            st.rerun()

# Display streaming status
if st.session_state.streaming:
    st.info("🤖 Agents are responding...")

# Display conversation with color-coded messages
for msg in st.session_state.history:
    speaker = msg["agent"]
    text = msg["content"]
    color = AGENT_COLORS.get(speaker, "#FFFFFF")
    is_typing = msg.get("is_typing", False)

    # Style typing messages differently
    if is_typing:
        st.markdown(
            f"""
            <div style="background-color:{color}; padding:10px; border-radius:10px; margin-bottom:5px; opacity:0.7">
                <b>{speaker.title()}:</b> <em>{text}</em> 💭
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # Use HTML for colored chat bubbles
        st.markdown(
            f"""
            <div style="background-color:{color}; padding:10px; border-radius:10px; margin-bottom:5px">
                <b>{speaker.title()}:</b> {text}
            </div>
            """,
            unsafe_allow_html=True
        )

