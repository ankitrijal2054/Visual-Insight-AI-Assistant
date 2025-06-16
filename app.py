import streamlit as st
from pathlib import Path
import base64
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io

from ai_api import ask_gemini_chat, create_gemini_chat
from utils.image_utils import image_to_base64

import base64

def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_image_base64("logo.png")

# --- Page Config & CSS Injection ---
st.set_page_config(
    page_title="Visual Insights Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)
css_file = Path(__file__).with_name("style.css")
if css_file.is_file():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

# --- State Management Initialization ---
if "view" not in st.session_state:
    st.session_state.view = "Analyze / Chat"

# Define all keys that need to be managed in session state
keys_to_init = [
    "uploaded_file", "base64_image", "prev_file_name",
    "chat_session", "chat_history",  # For main "Analyze / Chat"
    "caption_chat", "caption_history",
    "recipe_chat", "recipe_history",
    "fashion_chat", "fashion_history",
    "travel_chat", "travel_history",
    "document_chat", "document_history",
    "funfact_chat", "funfact_history",
]
for key in keys_to_init:
    if key not in st.session_state:
        st.session_state[key] = None
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("### 🚀 AI Visual Assistant")
    PAGES = {
        "Analyze / Chat": "💬", "Get a caption": "📝", "Recipe Generator": "🍳",
        "Fashion mode": "👗", "Travel mode": "🌍", "Document mode": "📄", "Fun fact mode": "🎉",
    }


    def set_view(view_name):
        st.session_state.view = view_name


    for page, icon in PAGES.items():
        is_active = (st.session_state.view == page)
        button_type = "primary" if is_active else "secondary"
        st.button(f"{icon} {page}", on_click=set_view, args=(page,), use_container_width=True, type=button_type)

    st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

    if st.button("🔄 New Analysis", use_container_width=True, type="secondary"):
        keys_to_clear = list(st.session_state.keys())
        for key in keys_to_clear:
            if key != "uploader_key":
                del st.session_state[key]
        st.session_state["uploader_key"] += 1
        st.rerun()

# --- Main Content Area ---

st.markdown(f"""
    <div style="text-align: center; padding-top: 10px;">
        <img src="data:image/png;base64,{logo_base64}" style="height: 200px;">
    </div>
""", unsafe_allow_html=True)
st.markdown(f"<div class='hero'><h1>{st.session_state.view}</h1></div>", unsafe_allow_html=True)

uploader_key = st.session_state.get("uploader_key", 0)
uploaded_file = st.file_uploader("📤 Upload an image to begin", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key=uploader_key)

if uploaded_file and uploaded_file.name != st.session_state.get("prev_file_name"):
    # Clear all session state except the view when a new image is uploaded
    current_view = st.session_state.view
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.view = current_view

    st.session_state.uploaded_file = uploaded_file
    st.session_state.prev_file_name = uploaded_file.name

    file_bytes = uploaded_file.read()
    with st.spinner("Processing image..."):
        st.session_state.base64_image = image_to_base64(file_bytes)

if st.session_state.get("base64_image"):
    st.markdown(
        f"<div class='uploaded-image-container'><img src='data:image/jpeg;base64,{st.session_state.base64_image}' class='uploaded-image'></div>",
        unsafe_allow_html=True)


# --- REUSABLE CHAT UI FUNCTION ---
def render_chat_mode_ui(mode_name, subheader, initial_prompt, chat_input_placeholder):
    """
    A generic function to render a chat interface for any specialized mode.

    Args:
        mode_name (str): The base name for session state keys (e.g., "recipe").
        subheader (str): The subheader text to display (e.g., "🍳 Suggested Dish & Recipe").
        initial_prompt (str): The first prompt to send to the AI to kick off the chat.
        chat_input_placeholder (str): Placeholder text for the chat input box.
    """
    st.subheader(subheader)

    history_key = f"{mode_name}_history"
    chat_session_key = f"{mode_name}_chat"
    guardrail_prompt = (
        "For any follow-up chat message, respond only if it is clearly and directly related to the uploaded image content. "
        "If the question is off-topic or cannot be answered using the image, say: 'This question is not related to the image content.' Do not guess."
    )
    final_initial_prompt = f"{initial_prompt} {guardrail_prompt}"

    # Initialize chat session and history on first run for this mode
    if st.session_state.get(history_key) is None:
        with st.spinner("Analyzing image..."):
            st.session_state[chat_session_key] = create_gemini_chat(st.session_state.base64_image)
            if st.session_state[chat_session_key]:
                response = ask_gemini_chat(st.session_state[chat_session_key], final_initial_prompt)
                st.session_state[history_key] = [("assistant", response)]
                st.session_state[f"{mode_name}_out_of_context"] = "Out of context image" in response
            else:
                st.session_state[history_key] = []
                st.session_state[f"{mode_name}_out_of_context"] = False

    # Display chat messages
    for sender, msg in st.session_state.get(history_key, []):
        with st.chat_message(sender):
            st.markdown(msg)

    # Disable chat input if image is out of context (except in "chat" mode)
    is_out_of_context = st.session_state.get(f"{mode_name}_out_of_context", False)
    if mode_name != "chat" and is_out_of_context:
        return

    # Handle user input
    if prompt := st.chat_input(chat_input_placeholder):
        st.session_state[history_key].append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Thinking..."):
            response = ask_gemini_chat(st.session_state[chat_session_key], prompt)
            st.session_state[history_key].append(("assistant", response))
            st.rerun()



# --- Mode Handler ---
# This block checks the active view and calls the correct rendering function.
if st.session_state.get("base64_image"):
    view = st.session_state.view

    if view == "Analyze / Chat":
        # This mode is slightly different, so it keeps its original function
        render_chat_mode_ui("chat", "💬 Chat with your Image",
                            "Analyze the image and provide a brief description of what you see.",
                            "Ask any question about the image...")
    elif view == "Get a caption":
        render_chat_mode_ui("caption", "📝 Image Caption",
                            "You are an image captioning expert for social media. Analyze the uploaded image and provide five short, engaging, and accurate caption only if the image contains a clear, captionable subject. If the image is blurry, irrelevant, blank, or does not contain recognizable or meaningful visual content, respond with: 'Out of context image: The image does not contain content suitable for captioning.'",
                            "Ask for different versions, hashtags, etc.")
    elif view == "Recipe Generator":
        render_chat_mode_ui("recipe", "🍳 Suggested Dish & Recipe",
                            "You are a culinary expert. Based on the food image, suggest a dish and provide a detailed recipe. If no food is found, say 'Out of context image: No food found to generate a recipe.'",
                            "Ask for substitutions, serving size, etc.")
    elif view == "Fashion mode":
        render_chat_mode_ui("fashion", "👗 Outfit Insight",
                            "You are a fashion expert. Describe the outfit, style, and potential brands. If not a fashion image, respond with 'Out of context image: No fashion-related items found.'",
                            "Ask where to buy items, for styling tips, etc.")
    elif view == "Travel mode":
        render_chat_mode_ui("travel", "🌍 Travel Suggestion",
                            "You are a travel expert. Identify the location/region in the image and suggest travel tips. If it's not a travel scene, say 'Out of context image: Unable to identify a travel location.'",
                            "Ask about nearby attractions, best time to visit, etc.")
    elif view == "Document mode":
        render_chat_mode_ui("document", "📄 Document Analysis",
                            "You are a document analysis assistant. Extract any visible text and provide a concise summary. If no readable text is found, say 'Out of context image' and state that clearly.",
                            "Ask for specific details, to translate, etc.")
    elif view == "Fun fact mode":
        render_chat_mode_ui("funfact", "🎉 Fun Fact",
                            "You're a trivia expert. Generate one surprising or educational fun fact related to the image. If you can't, respond with 'Out of context image: No fun fact could be generated.'",
                            "Ask for another fact, or more details...")
else:
    if not uploaded_file:
        st.info("👆 Please upload an image to get started.")