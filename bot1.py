import openai
import streamlit as st
import time
import json
import os

assistant_id = "asst_SWDs3AXdOfnU3Ki6TYHSiNMw"

client = openai

# Path to save chat history
CHAT_HISTORY_PATH = "chat_history.json"

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_PATH):
        with open(CHAT_HISTORY_PATH, "r") as file:
            return json.load(file)
    return []

def save_chat_history(chat_history):
    with open(CHAT_HISTORY_PATH, "w") as file:
        json.dump(chat_history, file)

# Initialize session state variables
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

st.set_page_config(page_title="GroupGPT", page_icon=":speech_balloon:")

openai.api_key = st.secrets["OPENAI_API_KEY"]

if st.sidebar.button("Start Chat"):
    st.session_state.start_chat = True
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

st.title("Thematic Analysis Chatbot")
st.write("I am a thematic analysis chatbot")

if st.button("Exit Chat"):
    st.session_state.messages = []  # Clear the chat history
    st.session_state.start_chat = False  # Reset the chat state
    st.session_state.thread_id = None
    save_chat_history(st.session_state.messages)  # Save the cleared chat history

if st.session_state.start_chat:
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4o"
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Let's discuss an issue."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=prompt
            )
        
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            instructions="You are a social scientist with expertise in qualitative data and thematic analysis. See the attached file for guides, steps, procedures on thematic analysis. You will perform three steps in conducting a thematic analysis. First, ask users to upload a data file. After locating the data file, generate initial codes after reviewing the data multiple times. The naming of the initial codes should be accurate, data-based, and thoughtful. For each initial code, provide 2 verbatim quotes to support your codes. Remember the quotes should be 100% verbatim, direct quotes. Do not change any single words or punctautions marks. Ask feedback and comments from users before proceeding. Next, you will cluster the generated codes into thematic groups (i.e., themes) based on their similarity and deeper connections. Ask feedback and comments from users before proceeding. Last, ask users whether they have a research question, and if so, provide the research question. Then you will develop specific codes addressing this research question."
        )

        while run.status != 'completed':
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages_for_run:
            st.session_state.messages.append({"role": "assistant", "content": message.content[0].text.value})
            with st.chat_message("assistant"):
                st.markdown(message.content[0].text.value)
        
        save_chat_history(st.session_state.messages)  # Save chat history after each interaction

else:
    st.write("Click 'Start Chat' to begin.")
