import streamlit as st
import requests
import base64
from PIL import Image
import io

# Set page configuration
st.set_page_config(page_title="Make Your Own Story", page_icon="📖", layout="wide")

# Hide default Streamlit style elements to make the design cleaner
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Title of the app
st.title("📖 Make Your Own Story")

# API endpoint and headers
API_URL = st.secrets["lemmebuild_url"]
HEADERS = {'Content-Type': 'application/json'}

# Initialize session state variables
if 'past_story' not in st.session_state:
    st.session_state.past_story = ""
if 'image' not in st.session_state:
    st.session_state.image = None
if 'options' not in st.session_state:
    st.session_state.options = []
if 'history' not in st.session_state:
    st.session_state.history = []
    

def get_story(past_story, next_step=None):
    """
    Function to get the story from the API based on the past_story and next_step.
    """
    data = {'past_story': past_story}
    if next_step:
        data['next_step'] = next_step
    response = requests.post(API_URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        st.error("Failed to get a response from the API. Please try again.")
        return None

def display_story():
    """
    Function to display the story so far along with images.
    """
    st.write("## Your Story So Far")
    for part in st.session_state.history:
        st.write(part['story'])
        if part['image']:
            st.image(part['image'], use_column_width=True)
    st.write("---")

def main():
    """
    Main function that controls the flow of the app.
    """
    if st.session_state.past_story == "":
        st.write("Start your story by entering a line or a word:")
        user_input = st.text_input("Your starting line or word", "")
        if st.button("Start Story"):
            if user_input.strip() != "":
                result = get_story(user_input)
                if result:
                    st.session_state.past_story = result['story']
                    # Decode base64 image
                    base64_image = result['taa']
                    image = None
                    if base64_image:
                        image_data = base64.b64decode(base64_image)
                        image = Image.open(io.BytesIO(image_data))
                    st.session_state.image = image
                    st.session_state.options = result['options']
                    st.session_state.history.append({'story': result['story'], 'image': image})
                    st.rerun()
            else:
                st.warning("Please enter a starting line or word to begin your story.")
    else:
        display_story()
        st.write("## Choose the Next Step:")
        for idx, option in enumerate(st.session_state.options):
            if st.button(option, key=idx):
                # User selected an option
                result = get_story(st.session_state.past_story, option)
                if result:
                    # Update the past story
                    st.session_state.past_story += " " + result['story']
                    # Decode base64 image
                    base64_image = result['taa']
                    image = None
                    if base64_image:
                        image_data = base64.b64decode(base64_image)
                        image = Image.open(io.BytesIO(image_data))
                    st.session_state.image = image
                    st.session_state.options = result['options']
                    st.session_state.history.append({'story': result['story'], 'image': image})
                    st.rerun()
                else:
                    st.error("Failed to get the next part of the story. Please try again.")
                    break

# Run the main function
if __name__ == "__main__":
    main()
