import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.nova import askNova, createNova
from agent.pipeline import prepareMessage

st.set_page_config(page_title="NOVA agentic AI", page_icon="N", layout="centered")


def visibleMessages(chat: list) -> list:
    return [
        message
        for message in chat
        if message.get("role") in ("user", "assistant")
        and message.get("content")
    ]


def startChat() -> None:
    if "chat" not in st.session_state:
        st.session_state.chat = createNova()


st.title("NOVA")
st.caption("Desktop control AI agent")

with st.sidebar:
    st.subheader("Session")
    st.caption("umm idk kuch toh likhdena hai yaha pe hamko.")
    if st.button("New conversation", use_container_width=True):
        st.session_state.pop("chat", None)
        st.rerun()

try:
    startChat()
except Exception as error:
    st.error(str(error))
    st.stop()

for message in visibleMessages(st.session_state.chat):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

userMessage = st.chat_input("Message NOVA")
if userMessage:
    with st.chat_message("user"):
        st.markdown(userMessage)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."): #spinner is so cool maza aagya
            try:
                preparedMessage = prepareMessage(userMessage)
                response = askNova(st.session_state.chat, preparedMessage)
                st.markdown(response)
            except Exception as error:
                st.error(f"NOVA could not complete that request: {error}") # TODO need to change this its giving weird errors. marking it for future 
