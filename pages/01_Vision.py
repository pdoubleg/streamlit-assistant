import streamlit as st
import os
import io
import base64
from dotenv import load_dotenv
load_dotenv()
import openai
from openai import OpenAI
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
# from PIL import Image
from PIL import Image as PILImage
import markdown
import textwrap
from html2text import html2text
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image as ReportLabImage
from reportlab.platypus import Preformatted
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup


# Function to encode the image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode("utf-8")


st.set_page_config(page_title="PropertyImageInspect", layout="centered", initial_sidebar_state="collapsed")

# Streamlit page setup
st.title("`πi` | PropertyImageInspector\n\nPowered by: `GPT-4 Turbo with Vision`")

with st.expander(":camera:**Introduction**:camera:"):
    st.markdown("""
        ## Welcome to Property Image Inspector!
        
        This app uses the power of GPT-4 Turbo with Vision to inspect and evaluate property images.\n\n 
        Here's how to use it:
        
        1. Upload an image of some property.
        2. Tell the app if your image contains "Personal Property" or "Structural Items".
        3. Optionally, add instructions or more info about the image. Change this as much as you'd like!
        4. Click the 'Analyze the Image' button.
        5. Wait for the analysis to complete.
        6. View the results and (optionally) download a PDF report.
        7. Sit back and think about all the time you just saved :sunglasses:
    """)


# Initialize session state for app re-run
if "analyze_button_clicked" not in st.session_state:
    st.session_state["analyze_button_clicked"] = False
    
st.session_state["analyze_button_clicked"] = False
    
# Initialize session state for last processed message
if "last_processed_message" not in st.session_state:
    st.session_state["last_processed_message"] = None
    
if "last_full_response" not in st.session_state:
    st.session_state["last_full_response"] = ""
    
if "pdf_path" not in st.session_state:
    st.session_state["pdf_path"] = ""

# Generate PDF report with the uploaded image and model output
def markdown_to_text(markdown_string):
    # Convert markdown to html
    html = markdown.markdown(markdown_string)
    # Convert html to plain text while preserving line breaks
    soup = BeautifulSoup(html, features="html.parser")
    text = ''
    for string in soup.stripped_strings:
        # Wrap the text after 80 characters
        wrapped_string = textwrap.fill(string, width=90)
        text += wrapped_string + '\n'
    return text


def normalize_image_size(image_path, max_width, max_height):
    with PILImage.open(image_path) as img:
        width, height = img.size
        aspect_ratio = width / height

        if width > max_width:
            width = max_width
            height = width / aspect_ratio

        if height > max_height:
            height = max_height
            width = height * aspect_ratio

        return int(width), int(height)


def create_pdf(image_path, text, pdf_path):
    max_width, max_height = 500, 500    
    image_size = normalize_image_size(image_path, max_width, max_height)
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    story.append(ReportLabImage(image_path, image_size[0], image_size[1]))
    text = markdown_to_text(text)
    story.append(Preformatted(text, styles["BodyText"]))
    doc.build(story)
    
    
# Convert base64 to file format
def base64_to_image(base64_image):
    image_data = base64.b64decode(base64_image)
    image = PILImage.open(io.BytesIO(image_data))
    image.save("image.jpg")
    return "image.jpg"

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)

# File uploader allows user to add their own image
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Display the uploaded image
    with st.expander("Image", expanded = True):
        st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
    

# Toggle for showing additional details input
show_details = st.toggle("Add details about the image", value=False)

if show_details:
    # Text input for additional details about the image, shown only if toggle is True
    additional_details = st.text_area(
        "Add any additional details or context about the image here:",
        disabled=not show_details
    )

# Add a radio button for the prompt type
prompt_type = st.radio(
    "Choose the type of item for analysis:",
    ("Personal Property", "Structural Items")
)

# Button to trigger the analysis
analyze_button = st.button("Analyse the Image", type="secondary", help="Clicking this button will display the prior report if nothing has changed.")

if analyze_button:
    st.session_state.analyze_button_clicked = True

# Check if an image has been uploaded, if the API key is available, and if the button has been pressed
if uploaded_file is not None and st.session_state.analyze_button_clicked:

    with st.spinner("Analysing the image ..."):
        # Encode the image
        base64_image = encode_image(uploaded_file)
        
        # Save the uploaded image to a file
        image_path = base64_to_image(base64_image)
        with open(image_path, "wb") as img_file:
            img_file.write(uploaded_file.getvalue())

        # Set the prompt text based on the selected type
        if prompt_type == "Personal Property":
            prompt_text = (
                "You are a highly knowledgeable eBay power seller. "
                "Your task is to examine the following image in detail. "
                "Provide a comprehensive, factual, and price-focused explanation of what the image depicts. "
                "Highlight key elements and their significance, and present your analysis in clear, well-structured markdown format. "
                "If applicable, include any relevant facts to enhance the explanation. "
                "Create a detailed image caption in bold explaining in short."
            )
            
        elif prompt_type == "Structural Items":
            prompt_text = (
                "You are a highly knowledgeable structural damage appraiser. "
                "Your task is to examine the following image in detail. "
                "Provide a comprehensive, scope-of-repair-focused explanation of what the image depicts. "
                "Itemize key repair scope items, and present your analysis in clear, well-structured markdown format. "
                "If applicable, include any relevant considerations such as demolition, or mitigation to enhance the scope explanation. "
                "If possible, include rough approximations of time and material for each scope item. "
                "Create a detailed image caption in bold explaining in short."
            )
    
        if show_details and additional_details:
            prompt_text += (
                f"\n\nAdditional Context or Instructions Provided by the User:\n{additional_details}"
            )
    
        # Create the payload for the completion request
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ]
        
        # Check if the current message is different from the last processed message
        if messages != st.session_state["last_processed_message"]:
    
            # Make the request to the OpenAI API
            try:
                # Without Stream
                
                # response = client.chat.completions.create(
                #     model="gpt-4-vision-preview", messages=messages, max_tokens=500, stream=False
                # )
        
                # Stream the response
                full_response = ""
                message_placeholder = st.empty()
                for completion in client.chat.completions.create(
                    model="gpt-4-vision-preview", messages=messages, 
                    max_tokens=1200, stream=True
                ):
                    # Check if there is content to display
                    if completion.choices[0].delta.content is not None:
                        full_response += completion.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                # Final update to placeholder after the stream ends
                message_placeholder.markdown(full_response)
                # Update the last processed message and response in the session state
                st.session_state["last_processed_message"] = messages
                st.session_state["last_full_response"] = full_response
                st.session_state.analyze_button_clicked = False         
                # Create the PDF
                st.session_state.pdf_path = "report.pdf"
                # report_text = str(full_response)
                create_pdf(image_path, full_response, st.session_state.pdf_path)

                # Provide the download button
                with open(st.session_state.pdf_path, "rb") as file:
                    btn = st.download_button(
                        label="Download Report",
                        data=file,
                        file_name="report.pdf",
                        mime="application/pdf",
                    )
        
                # Display the response in the app
                # st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"An error occurred: {e}")
                
        else:
            # Display the last stored response
            message_placeholder = st.empty()
            message_placeholder.markdown(st.session_state["last_full_response"])
            st.info("Displaying previous report as the image and details have not changed.")
            # Provide the download button
            with open(st.session_state.pdf_path, "rb") as file:
                btn = st.download_button(
                    label="Download Report",
                    data=file,
                    file_name="report.pdf",
                    mime="application/pdf",
                )
else:
    # Warnings for user action required
    if not uploaded_file and analyze_button:
        st.warning("Please upload an image.")