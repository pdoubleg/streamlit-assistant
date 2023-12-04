import openai
import streamlit as st
from bs4 import BeautifulSoup
import requests
import html2text
import io
import time
from openai import OpenAI

# Set up the Streamlit page with a title and icon
st.set_page_config(page_title="OpenAI Assistant App", page_icon=":speech_balloon:")

# Create a dictionary to map the readable names to the assistant_id
assistant_dict = {
    "Advanced Data Analytics": 'asst_6L1ZkOKmETV2Bdpq90eesdtg',
    "Policy Guide": 'asst_dOJ1xKHvQZMHSGdq0A0kbBJ9',
    "Scattergories Host": "asst_0KwJLc8sNLz2HVwc7yx9T2zt"
}

# Initialize session state for last API key
if "last_api_key" not in st.session_state:
    st.session_state["last_api_key"] = ""
    
# Create a sidebar for API key configuration and additional features
st.sidebar.header("Configuration")
api_key_ = st.sidebar.text_input("Enter your OpenAI API key", type="password")

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
selected_assistant = st.sidebar.selectbox("Select an Assistant", list(assistant_dict.keys()), key='assistant')

# Check if the selected assistant has changed
if "prev_assistant" in st.session_state and st.session_state.prev_assistant != selected_assistant:
    # Reset the session state (or specific variables) here
    st.session_state.clear()

# Update the previous assistant
st.session_state.prev_assistant = selected_assistant

# Get the assistant_id from the selected assistant
assistant_id = assistant_dict[selected_assistant]

# Initialize session state variables for file IDs and chat control
if "file_id_list" not in st.session_state:
    file_list = client.beta.assistants.files.list(assistant_id=assistant_id)
    file_ids = [file.id for file in file_list.data]
    st.session_state.file_id_list = file_ids
     
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

def scrape_website(url):
    """Scrape text from a website URL and convert to markdown."""
    response = requests.get(url)
    html_converter = html2text.HTML2Text()
    html_converter.ignore_links = True
    markdown_text = html_converter.handle(response.text)
    return markdown_text

def upload_to_openai(markdown_text):
    """Upload a markdown text to OpenAI and return its file ID."""
    bytes_like_object = io.BytesIO(markdown_text.encode('utf-8'))
    response = openai.files.create(file=bytes_like_object.read(), purpose="assistants")
    return response.id

# Additional features in the sidebar for web scraping and file uploading
st.sidebar.header("Additional Features")
website_url = st.sidebar.text_input("Enter a website URL to scrape", key="website_url")

# Button to scrape a website and upload to OpenAI
if st.sidebar.button("Scrape and Upload"):
    # Scrape and upload process
    scraped_text = scrape_website(website_url)
    file_id = upload_to_openai(scraped_text)
    st.session_state.file_id_list.append(file_id)
    st.sidebar.write(f"File ID: {file_id}")

# Sidebar option for users to upload their own files
uploaded_file = st.sidebar.file_uploader("Upload a file to OpenAI", key="file_uploader")

# Button to upload a user's file and store the file ID
if st.sidebar.button("Upload File"):
    # Upload file provided by user
    if uploaded_file:
        with open(f"{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())
        additional_file_id = upload_to_openai(f"{uploaded_file.name}")
        st.session_state.file_id_list.append(additional_file_id)
        st.sidebar.write(f"Additional File ID: {additional_file_id}")

# Display all file IDs
if st.session_state.file_id_list:
    st.sidebar.write("Uploaded File IDs:")
    for file_id in st.session_state.file_id_list:
        st.sidebar.write(file_id)
        # Associate files with the assistant
        assistant_file = client.beta.assistants.files.create(
            assistant_id=assistant_id, 
            file_id=file_id
        )

# Button to start the chat session
if st.sidebar.button("Start Chat"):
    # Check if files are uploaded before starting chat
    st.session_state.start_chat = True
    # Create a thread once and store its ID in session state
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    # st.write("thread id: ", thread.id)


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
st.title("`OpenAI Assistant`")
# st.write("This is a simple chat application based on OpenAI's Assistants API")

# Only show the chat interface if the chat has been started
if st.session_state.start_chat:
    # Initialize the model and messages list if not already in session state
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-1106-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages in the chat
    for message in st.session_state.messages:
        avatar_path = "./images/stuser.png" if message["role"] == "user" else "./images/stbot.png"
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
            # instructions="Please answer the queries using the knowledge provided in the files. When writing code always display it for the user."
        )

        # Poll for the run to complete and retrieve the assistant's messages
        while run.status != 'completed':
            time.sleep(1)
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
            with st.chat_message("assistant", avatar="./images/stbot.png"):
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
    st.write("Please upload files or click 'Start Chat' to begin the conversation.")
    
    