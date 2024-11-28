import streamlit as st
from openai import OpenAI
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()



# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit app title
st.title("Image Generator with OpenAI")

# User input for prompt
user_prompt = st.text_area("Enter your prompt for image generation:")

# Upload reference image
uploaded_image = st.file_uploader("Upload a reference image (optional)", type=["png", "jpg", "jpeg"])

if st.button("Generate Image"):
    if user_prompt:
        # Add reference to prompt if an image is uploaded
        if uploaded_image:
            reference_note = " with inspiration from the uploaded image."
        else:
            reference_note = ""
        
        # Generate the image using the text prompt
        prompt_with_reference = user_prompt + reference_note
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_with_reference,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        st.image(image_url, caption="Generated Image")
    else:
        st.error("Please enter a prompt.")
