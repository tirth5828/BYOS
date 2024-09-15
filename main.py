import openai
import streamlit as st
import requests
from fpdf import FPDF
import requests
from io import BytesIO
from PIL import Image


# Initialize OpenAI API key (replace 'your-api-key' with your actual API key)
key = st.secrets["openai_api_key"]

# Streamlit app setup
st.title("Create Your Own Interactive Story")

# Global variables to store conversation history and story progress
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = [
        {"role": "system", "content": "You are a Indian story writer that helps users create interactive stories. You will create 2 - 3 paragraphs for the story introduction and then provide 3 - 4 options for the user to choose from. Based on the user's choice, you will continue the story with more 3 - 4 paras and with a new set of options. Let's start creating a story together!"}
    ]
if 'story_started' not in st.session_state:
    st.session_state.story_started = False
if 'story_parts' not in st.session_state:
    st.session_state.story_parts = []
if 'options' not in st.session_state:
    st.session_state.options = []
if 'images' not in st.session_state:
    st.session_state.images = []
    
def save_story_as_pdf():
    # Create a PDF instance
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add title page
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(200, 10, txt="Your Interactive Story", ln=True, align='C')
    pdf.ln(10)

    # Loop through each part of the story
    for idx, part in enumerate(st.session_state.story_parts):
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, part)  # Add the text part of the story
        
        # Add corresponding image if it exists
        if idx < len(st.session_state.images):
            image_url = st.session_state.images[idx]
            if image_url:
                try:
                    # Fetch the image from the URL
                    response = requests.get(image_url)
                    image = Image.open(BytesIO(response.content))
                    
                    # Resize image if necessary (adjust width to fit PDF)
                    image_width = 100  # Set image width
                    aspect_ratio = image.size[1] / image.size[0]  # Calculate aspect ratio
                    image_height = aspect_ratio * image_width
                    
                    # Convert the image to a format that FPDF can use (JPEG or PNG in memory)
                    img_buffer = BytesIO()
                    image.save(img_buffer, format="PNG")  # Save image to buffer
                    img_buffer.seek(0)  # Go back to the beginning of the buffer

                    # Add the image to the PDF using the in-memory image
                    pdf.image(img_buffer, x=None, y=None, w=image_width, h=image_height)
                except Exception as e:
                    print(f"Failed to add image to PDF: {e}")
                    
        pdf.ln(10)  # Add space after each part of the story

    # Output the PDF to a byte stream
    pdf_output = BytesIO()
    pdf.output(pdf_output, 'F')

    # Serve the PDF for download
    st.download_button(
        label="Download Story as PDF",
        data=pdf_output.getvalue(),
        file_name="interactive_story.pdf",
        mime="application/pdf"
    ) 
    
def clean_text(text):
    output = ""
    for line in text.split('\n'):
        if not line.startswith(('1.', '2.', '3.', '4.' , 'Options:')):
            output += line + '\n'
    
def generate_image(story_text):
    response = requests.post(st.secrets["lemmebuild_url"], json={'story': story_text })
    print(st.secrets["lemmebuild_url"])
    print(response)
    print(response.status_code)
    print(response.json())
    image_url = response.json()['foo']
    st.session_state.images.append(image_url)

        
def extract_options(response):
    # Reset options
    st.session_state.options = []
    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith(('1.', '2.', '3.', '4.')):
            st.session_state.options.append(line)

def generate_story_response():
    # Get a response from the OpenAI API
    client = openai.OpenAI(api_key=key)
    
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.conversation_history,
        stream=True
    )
    
    assistant_response = ""
    for chunk in completion:
        delta = chunk.choices[0].delta.content
        if delta:
            assistant_response += delta
    
    # Save the assistant response
    st.session_state.story_parts.append(assistant_response)
    
    # Add the assistant's response to the conversation history
    st.session_state.conversation_history.append({"role": "assistant", "content": assistant_response})
    
    # Extract options from the assistant's response
    extract_options(assistant_response)
    
    generate_image(clean_text(assistant_response))



# Step 1: Ask for the type of story if the story hasn't started yet
if not st.session_state.story_started:
    story_type = st.text_input("What kind of story would you like to create? (e.g., fantasy, sci-fi, mystery, etc.)")
    if st.button("Start Story") and story_type:
        st.session_state.conversation_history.append({"role": "user", "content": f"I want to create a {story_type} story."})
        st.session_state.story_started = True
        generate_story_response()
        st.experimental_rerun()

# Display the story parts with images
for idx, part in enumerate(st.session_state.story_parts):
    st.write(part)
    print(st.session_state.images)
    if idx < len(st.session_state.images):
        image = st.session_state.images[idx]
        if image:
            st.image(image)
    st.write("---")  # Separator between story parts

# Present options if available
if st.session_state.options:
    st.write("Here are some options for what happens next:")
    for i, option in enumerate(st.session_state.options):
        if st.button(option):
            st.session_state.conversation_history.append({"role": "user", "content": f"I choose option {i+1}."})
            generate_story_response()
            st.experimental_rerun()
elif st.session_state.story_started:
    st.write("No options available.")

# add button to save the story 
if st.button("Save Story"):
    # convert it into a pdf story book with both text and images 
    pass

# Optionally, you can add a condition to end the story if an ending is reached
if st.session_state.story_parts and "The End" in st.session_state.story_parts[-1]:
    st.write("Your story has reached an ending!")
