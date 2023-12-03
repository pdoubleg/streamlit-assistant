import streamlit as st
import os
import io
import base64
from dotenv import load_dotenv
load_dotenv()
import openai
from openai import OpenAI
from metaphor_python import Metaphor

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


st.set_page_config(page_title="PropertyImageInspect", layout="centered", initial_sidebar_state="auto")

# Streamlit page setup
st.title("`πi` | PropertyImageInspector\n\nPowered by: `GPT-4 Turbo with Vision`")


# Create a sidebar for API key configuration and additional features
st.sidebar.header("Configuration")
api_key_ = st.sidebar.text_input("Enter your OpenAI API key", type="password")

if not api_key_:
    st.warning('Please input an api key')
    st.stop()
st.success('Thank you for inputting an api key!')

lock = st.secrets["SECRET_API_KEY"]

if api_key_:

    if api_key_ == lock:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    else:
        client = OpenAI(api_key=api_key_)
    metaphor = Metaphor(st.secrets["METAPHOR_API_KEY"])


    # Function to encode the image to base64
    def encode_image(image_file):
        return base64.b64encode(image_file.getvalue()).decode("utf-8")


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
        
        
    def get_llm_response(system='You are a helpful assistant.', user = '', temperature = 1, model = 'gpt-3.5-turbo'):
        completion = openai.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ]
        )
        return completion.choices[0].message.content


    def create_base_item_generation_prompt(vision_output):
        return f"""The following is a detailed description of a user-supplied image of an item they want to buy. Take the description, and distill it down to a concise, but descriptive internet search query that will help empower them as a buyer:\n\nITEM_ANALYSIS:\n{vision_output}\n\nHELPFUL_ANSWER: """

    def generate_base_query(vision_output):
        user_prompt = create_base_item_generation_prompt(vision_output)
        completion = get_llm_response(
            system='The user will ask you to help generate a search query. Respond with only the query in plain text with no extra formatting.',
            user=user_prompt,
            temperature=0.3
        )
        return completion


    def create_keyword_query_generation_prompt(topic, n):
        return f"""I'm conducting research on {topic} and need help coming up with Google keyword search queries.
    Google keyword searches should just be a few words long. It should not be a complete sentence.
    Please generate a diverse list of {n} Google keyword search queries that would be useful for researching ${topic}. Do not add any formatting or numbering to the queries."""

    def generate_search_queries(topic, n):
        user_prompt = create_keyword_query_generation_prompt(topic, n)
        completion = get_llm_response(
            system='The user will ask you to help generate some search queries. Respond with only the suggested queries in plain text with no extra formatting, each on it\'s own line.',
            user=user_prompt,
            temperature=1
        )
        queries = [s for s in completion.split('\n') if s.strip()][:n]
        return queries

    def get_search_results(queries, type, linksPerQuery=1):
        results = []
        for query in queries:
            search_response = metaphor.search(query, type=type, num_results=linksPerQuery, use_autoprompt=False)
            results.extend(search_response.results)
        return results

    def display_search(search_results):
        for result in search_results:
            st.write(f"Title: {result.title}")
            st.write(f"URL: {result.url}")
            st.markdown("___")


    def get_page_contents(search_results):
        contents_response = metaphor.get_contents(search_results)
        return contents_response.contents

    # def synthesize_report(topic, search_contents, content_slice = 3000):
    #     inputData = ''.join([
    #         f'--START ITEM--\nURL: {item.url}\nCONTENT: {item.extract[:content_slice]}\n--END ITEM--\n'
    #         for item in search_contents
    #     ])
    #     return get_llm_response(
    #         system='You are a helpful internet research assistant specializing in empowering buyers. You help sift through raw search results to find the most relevant and interesting findings for user topic of interest. ',
    #         user='Input Data:\n' + inputData + f'Write a two paragraph research report about **{topic}** based on the provided search results. One paragraph summarizing the Input Data, and another focusing on the main Research Topic. Include as many sources as possible. Provide citations in the text using footnote notation ([#]). First provide the report, followed by a markdown table of all the URLs used, in the format [#] .',
    #         model='gpt-4' # want a better report? use gpt-4
    #     ), inputData

    def synthesize_report(topic, search_contents, content_slice = 10000):
        content_slice = int(content_slice)
        inputData = ''.join([
            f'--START ITEM--\nURL: {item.url}\nCONTENT: {item.extract[:content_slice]}\n--END ITEM--\n'
            for item in search_contents
        ])
        full_report = ""
        for completion in openai.chat.completions.create(
            model='gpt-4-1106-preview',
            temperature=1,
            messages=[
                {'role': 'system', 'content': 'You are a helpful internet research assistant specializing in empowering buyers. You help sift through raw search results to find the most relevant and interesting findings for user topic of interest.'},
                {'role': 'user', 'content': 'Input Data:\n' + inputData + f'Write a two paragraph research report about **{topic}** based on the provided search results. One paragraph summarizing the Input Data, and another focusing on the main Research Topic. Include as many sources as possible. Provide citations in the text using footnote notation ([#]). First provide the report, followed by a markdown table of all the URLs used, in the format [#] .'},
            ],
            stream=True
        ):
            # Check if there is content to display
            if completion.choices[0].delta.content is not None:
                full_report += completion.choices[0].delta.content
                report_placeholder.markdown(full_report + "▌")
        # Final update to placeholder after the stream ends
        report_placeholder.markdown(full_report)
        return full_report, inputData


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


    def create_pdf(image_path, text, research, content, pdf_path):
        max_width, max_height = 500, 500    
        image_size = normalize_image_size(image_path, max_width, max_height)
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        story.append(ReportLabImage(image_path, image_size[0], image_size[1]))
        text = markdown_to_text(text)
        story.append(Preformatted(text, styles["BodyText"]))
        research = markdown_to_text(research)
        story.append(Preformatted(research, styles["BodyText"]))
        content = markdown_to_text(content)
        story.append(Preformatted(content, styles["BodyText"]))
        doc.build(story)
        
        
    # Convert base64 to file format
    def base64_to_image(base64_image):
        image_data = base64.b64decode(base64_image)
        image = PILImage.open(io.BytesIO(image_data))
        image.save("image.jpg")
        return "image.jpg"

    # File uploader allows user to add their own image
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        # Display the uploaded image
        with st.expander("Image", expanded = True):
            st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
        

    # Create two columns for the toggles
    col1, col2 = st.columns(2)

    # Toggle for showing additional details input in the first column
    with col1:
        show_details = st.toggle("Add details about the image", value=False)

        if show_details:
            # Text input for additional details about the image, shown only if toggle is True
            additional_details = st.text_area(
                "Add any additional details or context about the image here:",
                disabled=not show_details,
                height=125,
            )

    # Toggle for including audio in the second column
    with col2:
        include_audio = st.toggle("Include audio report", value=False)

        if include_audio:
            # Radio button for selecting audio type, shown only if toggle is True
            audio_type = st.radio(
                "Choose the type of audio:",
                ("alloy", "echo", "fable", "onyx", "nova", "shimmer"),
                index=4
            )

    # Add a radio button for the prompt type
    prompt_type = st.radio(
        "Choose the type of item for analysis:",
        ("Personal Property", "Structural Items", "Diagram Inspector")
    )

    # Button to trigger the analysis
    analyze_button = st.button("Inspect the Image", type="secondary")

    if analyze_button:
        st.session_state.analyze_button_clicked = True

    # Check if an image has been uploaded, if the API key is available, and if the button has been pressed
    if uploaded_file is not None and st.session_state.analyze_button_clicked:

        with st.spinner("Inspecting the image ..."):
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
                    "Begin with a descriptive title caption in bold. "
                    "Provide a comprehensive, factual, and price-focused explanation of what the image depicts. "
                    "Highlight key elements and their significance, and present your analysis in clear, well-structured markdown format. "
                    "If applicable, include any relevant facts to enhance the explanation. "
                    "TITLE: "
                )
                
            elif prompt_type == "Structural Items":
                prompt_text = (
                    "You are a highly knowledgeable structural damage appraiser. "
                    "Your task is to examine the following image in detail. "
                    "Begin with a descriptive title caption in bold. "
                    "Provide a comprehensive, scope-of-repair-focused explanation of what the image depicts. "
                    "Itemize key repair scope items, and present your analysis in clear, well-structured markdown format. "
                    "If applicable, include any relevant considerations such as demolition, or mitigation to enhance the scope explanation. "
                    "If possible, include rough approximations of time and material for each scope item. "
                    "TITLE: "
                )
                
            elif prompt_type == "Diagram Inspector":
                prompt_text = (
                    "You are a highly knowledgeable diagram interpreter specializing in deciphering analytical plots and technical diagrams. "
                    "Your task is to examine the following image in detail. "
                    "Begin with a descriptive title caption in bold. "
                    "Provide a comprehensive and clear explanation of what the image depicts. "
                    "Itemize key observations, and present your analysis in clear, well-structured markdown format. "
                    "If applicable, include any relevant considerations such as the image's context or motivations. "
                    "If possible, include rough approximations of any quantifyable features of the image. "
                    "TITLE: "
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
                    
                    if include_audio:
                        with st.spinner(text="Please hold for audio..."):
                            response = client.audio.speech.create(
                                model="tts-1",
                                voice=audio_type,
                                input=full_response,
                            )
                            response.stream_to_file("output.mp3")
                            audio_file = open('output.mp3', 'rb')
                            audio_bytes = audio_file.read()
                            st.success("Audio is Ready")
                        st.audio(audio_bytes)
                    

                    st.markdown("___")
                    st.markdown("## Internet Research:")
                    
                    item_title = generate_base_query(full_response)         
                    
                    search_queries = generate_search_queries(item_title, 3)
                    st.markdown("Running suggested searches:")
                    st.markdown(f"* {search_queries[0]}")
                    st.markdown(f"* {search_queries[1]}")
                    st.markdown(f"* {search_queries[2]}")
                    
                    with st.status("Links to suggested research material", state='running') as status:
                        search_result_links = get_search_results(search_queries, 'keyword', 2)
                        display_search(search_result_links)
                        status.update()
                    st.markdown("___")
                
                    # Define the placeholder for the report outside the container
                    report_placeholder = st.empty()
                    
                    st.markdown("___")

                    with st.status("Inspecting the suggested sites...", state='running') as status:
                        search_result_contents = get_page_contents([link.id for link in search_result_links])
                        full_report, content = synthesize_report(item_title, search_result_contents)
                        st.markdown(content, unsafe_allow_html=True)
                        status.update(label="Source content")

                    # The final report will be displayed outside the container
                    report_placeholder.markdown(full_report)
                    
                    if include_audio:
                        with st.spinner(text="Please hold again..."):
                            response_ = client.audio.speech.create(
                                model="tts-1",
                                voice=audio_type,
                                input=full_report,
                            )
                            response_.stream_to_file("report.mp3")
                            audio_file_ = open('report.mp3', 'rb')
                            audio_bytes_ = audio_file_.read()
                        st.success("Audio is Ready")
                        st.audio(audio_bytes_)
                    
                    st.session_state["last_processed_message"] = messages
                    st.session_state["last_full_response"] = full_response

                    st.session_state.analyze_button_clicked = False         
                    # Create the PDF
                    st.session_state.pdf_path = "report.pdf"
                    # report_text = str(full_response)
                    create_pdf(image_path, full_response, full_report, content, st.session_state.pdf_path)
                    st.markdown("___")
                    # Provide the download button
                    with open(st.session_state.pdf_path, "rb") as file:
                        btn = st.download_button(
                            label="Download Report & Reset App",
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