import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"

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

# Chat input
user_input = st.text_input("Type a message", "")

if st.button("Send"):
    if user_input.strip():
        payload = {
            "message": user_input,
            "temperature": temperature  # send slider value
        }
        # Send to FastAPI backend
        resp = requests.post(API_URL, json=payload)
        data = resp.json()

        # Update local history
        st.session_state.history = data["history"]


# Display conversation with color-coded messages
for msg in st.session_state.history:
    speaker = msg["agent"]
    text = msg["content"]
    color = AGENT_COLORS.get(speaker, "#FFFFFF")

    # Use HTML for colored chat bubbles
    st.markdown(
        f"""
        <div style="background-color:{color}; padding:10px; border-radius:10px; margin-bottom:5px">
            <b>{speaker.title()}:</b> {text}
        </div>
        """,
        unsafe_allow_html=True
    )

