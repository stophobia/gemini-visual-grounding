import streamlit as st
import google.generativeai as genai
import json
from PIL import ImageDraw, Image, ImageFont

model = None
chat_model = None

GEMINI_API_KEY = st.sidebar.text_input('Gemini API Key',
                                       type='password')


@st.cache_resource
def initialize_model(GEMINI_API_KEY):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    chat_model = model.start_chat(history=[])
    return chat_model

# if GEMINI_API_KEY:
chat_model = initialize_model(GEMINI_API_KEY)
# print("Initialized model")


def gemini_model_response(prompt):
    global chat_model
    # print(chat_model.history)
    return chat_model.send_message(prompt)


col1, col2 = st.columns(2)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# all_responses = []

with col1:
    uploaded_file = st.file_uploader("Upload an image")

    if uploaded_file is not None:
        if "initiated_image" not in st.session_state:
            # To read file as bytes:
            bytes_data = uploaded_file.getvalue()
            # show_image = st.image(bytes_data)
            image = Image.open(uploaded_file)
            initial_instruction = """
            You are chatbot who can answer user questions based on an image with visual grounding. So the first step
            is to output coordinates of the objects that you identify in the image and answer user
            questions with reference to the object_name in the json that you have generated.

            Keep your answers concise, and accept user suggestions if they respond that you have identified
            the wrong object.

            First step, Give a json output of 
            {object_name : {x : <x_coordinates>, y: <y_coordinates>}} coordinates of centroid where x,y is
            (in a standardized format (0-1) with 4 digit precision)
            of all the objects identified in the input image? In case you find multiple instances of same objects,
            use _1, _2 to differentiate them.
            """
            prompt = [initial_instruction, image]
            # all_responses.extend(prompt)
            model_response = gemini_model_response(prompt)
            print(model_response.text)
            # all_responses.append(model_response.text)
            coord_dict = json.loads("".join(model_response.text.strip().split("\n")[1:-1]))        
            width, height = image.width, image.height
            # Specify the font size
            font_size = 36
            font = ImageFont.load_default(size=font_size)
            # Create a font object with the specified size
            # font = ImageFont.truetype(font.path, font_size)

            for key, value in coord_dict.items():
                r = 50
                x = float(value['x']) * width
                y = float(value['y']) * height
                draw = ImageDraw.Draw(image)
                draw.ellipse((x-r, y-r, x+r, y+r), fill=(0, 0, 0, 0))
                draw.text((x, y), key, fill=(255, 0, 255, 0), font=font)
            st.session_state.initiated_image = image
        
        # show_image.empty()
        show_image = st.image(st.session_state.initiated_image)


with col2:
    messages = st.container(height=300)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        messages.chat_message(message["role"]).write(message["content"])

    if prompt := st.chat_input("What is up?"):
        # with st.chat_message("user"):
        messages.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user",
                                          "content": prompt})
        
        model_response = gemini_model_response(prompt)
        messages.chat_message("system").write(model_response.text)
        st.session_state.messages.append({"role": "system",
                                          "content": model_response.text})