import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.nova import createNova
from agent.router import routeRequest
from agent.routing_log import latestRouteDecision
from tools.rag import ingest_document

st.set_page_config(page_title="NOVA Agentic AI", page_icon="N", layout="centered")
if "session_initialized" not in st.session_state:
    from tools.rag import set_active_document
    set_active_document("")
    st.session_state.session_initialized = True


def visibleMessages(chat: list) -> list:
    return [
        message
        for message in chat
        if message.get("role") in ("user", "assistant") and message.get("content")
    ]


def startChat() -> None:
    if "chat" not in st.session_state:
        st.session_state.chat = createNova()


st.title("NOVA Desktop & Study Agent")
st.caption("Enter your query!")

with st.sidebar:
    st.subheader("Upload Study Material")
    uploaded_file = st.file_uploader(
        "Upload PPTX, PDF, or TXT",
        type=["pptx", "pdf", "txt", "md"],
    )

    if uploaded_file is not None:
        if st.button("Process Document", use_container_width=True):
            with st.spinner("Processing & embedding document..."):
                try:
                    os.makedirs("./temp_uploads", exist_ok=True)
                    save_path = os.path.join("./temp_uploads", uploaded_file.name)
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    result = ingest_document(save_path)
                    if str(result).lower().startswith("failed") or str(result).lower().startswith("error"):
                        st.error(result)
                    else:
                        st.success(result)
                except Exception as error:
                    st.error(f"Upload failed: {error}")

    st.divider()
    st.subheader("Last route")
    lastRoute = st.session_state.get("last_route", {})
    if lastRoute.get("route") == "system_tool" and lastRoute.get("tool"):
        st.write(f"System tool: `{lastRoute['tool']}`")
    elif lastRoute.get("route") == "agent":
        st.write("NOVA agent")
    else:
        st.write("No request yet")

try:
    startChat()
except Exception as error:
    st.error(f"Initialization error: {error}")
    st.info("Check your .env API key / base URL / model settings.")
    st.stop()

for message in visibleMessages(st.session_state.chat):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input("Ask NOVA or query your uploaded document...")
if user_message:
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = routeRequest(
                    user_message,
                    st.session_state.chat,
                    medium="app",
                )
                st.session_state.last_route = latestRouteDecision()
                if not response or not str(response).strip():
                    response = "I couldn't generate a reply just now. Please try again."
                st.markdown(response)
            except Exception as error:
                st.error("NOVA hit an unexpected error, but your session is still alive.")
                st.caption(f"Details: {type(error).__name__}: {error}")