import openai
import streamlit as st
from bs4 import BeautifulSoup
import requests
import html2text
from PIL import Image, ImageEnhance
import base64
import io
import time
import random
import string
from openai import OpenAI

# Set up the Streamlit page with a title and icon
st.set_page_config(page_title="Scattergories AI Hosted", page_icon=":speech_balloon:", layout="centered")

# Create a dictionary to map the readable names to the assistant_id
assistant_dict = {
    "Honorable AI BurgunGPT": "asst_GevnO6e0JGfljII2xs4nIdHh",
    "Scattergories Host": "asst_0KwJLc8sNLz2HVwc7yx9T2zt",  
}

# Initialize session state for last API key
if "last_api_key" not in st.session_state:
    st.session_state["last_api_key"] = ""
    
# Create a sidebar for API key configuration and additional features
st.sidebar.header("OpenAI API Key")
api_key_ = st.sidebar.text_input("Enter your OpenAI API key", type="password", label_visibility="collapsed")

if not api_key_:
    st.warning('Please input an api key')
    st.stop()
    
if api_key_ and api_key_ != st.session_state["last_api_key"]:
    st.toast(':+1: Thank you for inputting a new api key!')
    st.session_state["last_api_key"] = api_key_

lock = st.secrets["SECRET_API_KEY"]

if api_key_:

    if api_key_ == lock:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    else:
        client = OpenAI(api_key=api_key_)

# Create a sidebar for Assistant Selection
st.sidebar.header("Assistant Selection")
selected_assistant = st.sidebar.selectbox("Select an Assistant", list(assistant_dict.keys()), key='assistant', label_visibility="collapsed")

# Check if the selected assistant has changed
if "prev_assistant" in st.session_state and st.session_state.prev_assistant != selected_assistant:
    # Reset the session state (or specific variables) here
    st.session_state.clear()

# Update the previous assistant
st.session_state.prev_assistant = selected_assistant

# Get the assistant_id from the selected assistant
assistant_id = assistant_dict[selected_assistant]

st.sidebar.markdown("---")
st.sidebar.markdown("---")
st.sidebar.markdown("---")

# Inject custom CSS for grey-black fade border effect
st.markdown(
    """
    <style>
    .cover-glow {
        width: 100%;
        height: auto;
        padding: 3px;
        box-shadow: 
            0 0 5px #000000,
            0 0 10px #111111,
            0 0 15px #222222,
            0 0 20px #333333,
            0 0 25px #444444,
            0 0 30px #555555,
            0 0 35px #666666;
        position: relative;
        z-index: -1;
        border-radius: 30px;  /* Rounded corners */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Load and display sidebar image with glowing effect
img_path = "./images/ai_burgungpt.png"
img_base64 = img_to_base64(img_path)
st.sidebar.markdown(
    f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# Initialize session state variables for file IDs and chat control
if "file_id_list" not in st.session_state:
    file_list = client.beta.assistants.files.list(assistant_id=assistant_id)
    file_ids = [file.id for file in file_list.data]
    st.session_state.file_id_list = file_ids
     
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
    
if "letter" not in st.session_state:
    st.session_state.letter = None
    
def generate_random_letter():
    allowed_letters = [letter for letter in string.ascii_uppercase if letter not in ["Q", "U", "V", "X", "Y", "Z"]]
    return random.choice(allowed_letters)

def count_down(ts):
    with st.empty():
        while ts:
            mins, secs = divmod(ts, 60)
            time_now = '{:02d}:{:02d}'.format(mins, secs)
            st.markdown(f"<h1 style='text-align: center; font-weight: bold; font-size: 150;'>{time_now}</h1>", unsafe_allow_html=True)
            # st.markdown(f"{time_now}")
            time.sleep(1)
            ts -= 1
        # st.markdown("TIME UP!")
        st.markdown(f"<h1 style='text-align: center; font-weight: bold; font-size: 150;'>TIME UP!</h1>", unsafe_allow_html=True)

def timer():
    time_minutes = st.number_input('Enter the time in minutes ', min_value=1, max_value=5, value=2)
    time_in_seconds = time_minutes * 60
    if st.button("START TIMER", use_container_width=True):
        count_down(int(time_in_seconds))
        st.balloons()

# Button to start the chat session
if st.sidebar.button("Start Game", use_container_width=True, type="primary"):
    # Check if files are uploaded before starting chat
    st.session_state.start_chat = True
    # Create a thread once and store its ID in session state
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    # st.write("thread id: ", thread.id)
    
if st.sidebar.button("Random Letter Generator", use_container_width=True) or not st.session_state.get('letter'):
    letter = generate_random_letter()
    st.session_state.letter = letter

st.sidebar.markdown(f"<h1 style='text-align: center; font-weight: bold; font-size: 100px;'>{st.session_state.letter}</h1>", unsafe_allow_html=True)

st.sidebar.markdown("---")

with st.sidebar:
    timer()

st.sidebar.markdown("---")

# Define the function to process messages with citations
def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    try:
        message_content = message.content[0].text
        annotations = message_content.annotations if hasattr(message_content, 'annotations') else []
        citations = []

        # Iterate over the annotations and add footnotes
        for index, annotation in enumerate(annotations):
            # Replace the text with a footnote
            message_content.value = message_content.value.replace(annotation.text, f' [{index + 1}]')

            # Gather citations based on annotation attributes
            if (file_citation := getattr(annotation, 'file_citation', None)):                
                cited_file = client.files.retrieve(file_citation.file_id)
                citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
            elif (file_path := getattr(annotation, 'file_path', None)):
                cited_file = client.files.retrieve(file_path.file_id)
                citations.append(f'[{index}] Click <here> to download {cited_file.filename}')

        # Add footnotes to the end of the message content
        full_response = message_content.value + '\n\n' + '\n'.join(citations)
    except:
        # If the message contains an image file
        if message.content[0].type == "image_file":
            image_id = message.content[0].image_file.file_id
            # Retrieve the image file content as bytes
            image_data = client.files.content(image_id)
            full_response = image_data.read()
    return full_response

# Main chat interface setup
st.title("`Scattergories | AI Edition`")
st.markdown("_Hosted by:_ **`The Honorable AI BurgunGPT`**")

# Only show the chat interface if the chat has been started
if st.session_state.start_chat:
    # Initialize the model and messages list if not already in session state
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-1106-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages in the chat
    for message in st.session_state.messages:
        avatar_path = "./images/stuser.png" if message["role"] == "user" else "./images/ai_burgungpt.png"
        with st.chat_message(message["role"], avatar=avatar_path):
            if "image_data" in message:
                st.image(message["image_data"])
            else:
                st.markdown(message["content"])

    # Chat input for the user
    if prompt := st.chat_input("Send a message"):
        # Add user message to the state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="./images/stuser.png"):
            st.markdown(prompt)

        # Add the user's message to the existing thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # Create a run with additional instructions
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
        )

        # Poll for the run to complete and retrieve the assistant's messages
        while run.status != 'completed':
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
        
        # Retrieve messages added by the assistant
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages 
            if message.run_id == run.id and message.role == "assistant"
        ]
        
        # Sort the messages by their creation timestamp
        assistant_messages_for_run.sort(key=lambda message: message.created_at)

        for message in assistant_messages_for_run:
            full_response = process_message_with_citations(message)
            with st.chat_message("assistant", avatar="./images/ai_burgungpt.png"):
                try:
                    # Check if the message is an image
                    if isinstance(full_response, bytes):
                        st.image(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": "<image>", "image_data": full_response})
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        st.markdown(full_response, unsafe_allow_html=True)
                except ValueError:
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.markdown(full_response, unsafe_allow_html=True)
else:
    # Prompt to start the chat
    st.write("Click 'Start Game' to begin!")
    
    