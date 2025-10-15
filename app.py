import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# --- Load API Key ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Virtual Tennis Assistant", page_icon="🎾", layout="wide")

# --- Page Title ---
st.markdown(
    """
    <h1 style='text-align: center; color: #2E86C1;'>🎾 Virtual Tennis Assistant</h1>
    <p style='text-align: center; color: gray;'>
    Your AI-powered tennis companion — get match strategies, training tips, and motivation!
    </p>
    <hr>
    """,
    unsafe_allow_html=True,
)

# --- Initialize Session State ---
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"

# --- Helper: Generate Chat Name like ChatGPT ---
def generate_chat_name(user_input: str) -> str:
    if not user_input.strip():
        return "New Chat"
    words = user_input.strip().split()
    title = " ".join(words[:3]).capitalize()
    return f"💬 {title}..."

# --- Sidebar ---
st.sidebar.title("💬 Chat Sessions")
chat_names = list(st.session_state.sessions.keys())

# ➕ Start new chat
if st.sidebar.button("➕ New Chat"):
    st.session_state.current_chat = "New Chat"
    st.rerun()

# If no chat exists yet, initialize one
if st.session_state.current_chat == "New Chat" or st.session_state.current_chat not in st.session_state.sessions:
    st.session_state.sessions["New Chat"] = {
        "memory": ConversationBufferMemory(return_messages=True),
        "messages": [
            {"role": "assistant", "content": "👋 Hi! I'm your Tennis Assistant. How can I help you today?"}
        ],
        "title": "💬 New Chat",
    }

# Refresh chat list
chat_names = list(st.session_state.sessions.keys())

# Sidebar radio for selecting a chat
selected_chat = st.sidebar.radio(
    "Select a chat:",
    chat_names,
    index=chat_names.index(st.session_state.current_chat)
    if st.session_state.current_chat in chat_names
    else 0,
)
st.session_state.current_chat = selected_chat

# 🗑️ Add Delete Chat button
if st.sidebar.button("🗑️ Delete Selected Chat"):
    if st.session_state.current_chat in st.session_state.sessions:
        del st.session_state.sessions[st.session_state.current_chat]
        # If all chats deleted, create a new one
        if not st.session_state.sessions:
            st.session_state.current_chat = "New Chat"
        else:
            st.session_state.current_chat = list(st.session_state.sessions.keys())[0]
        st.rerun()

# --- Get active session ---
session = st.session_state.sessions[st.session_state.current_chat]

# --- Initialize LLM ---
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  # ensure it's available to LangChain

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
)
chain = ConversationChain(llm=llm, memory=session["memory"], verbose=False)

# --- Display Chat Messages ---
for msg in session["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input ---
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message
    session["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking... 🎾"):
            system_prompt = (
                "You are a friendly Virtual Tennis Assistant. "
                "Give concise, practical tennis advice (2–3 sentences) about training, "
                "matches, or improvement. Keep responses simple, helpful, and motivating."
            )
            response = chain.run(input=f"{system_prompt}\nUser: {user_input}")
            st.markdown(response)

    # Save assistant message
    session["messages"].append({"role": "assistant", "content": response})

    # ✅ Auto-generate chat name if still 'New Chat'
    if session["title"] == "💬 New Chat":
        new_name = generate_chat_name(user_input)
        st.session_state.sessions[new_name] = session
        st.session_state.sessions.pop("New Chat", None)  # ✅ Safe deletion (prevents KeyError)
        st.session_state.current_chat = new_name
        st.rerun()

# --- Sidebar Footer ---
st.sidebar.divider()
st.sidebar.info(f"Current Chat: {st.session_state.current_chat}")
