import streamlit as st
from ai_api import create_gemini_chat, ask_gemini_chat
from utils.image_utils import image_to_base64
from PIL import Image
import io
import base64

def get_logo_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- Page Config ---
st.set_page_config(page_title="Image Assistant", layout="wide")

# --- Custom CSS ---
def inject_custom_css():
    with open("style.css") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

inject_custom_css()

# --- App Title ---
col1, col2, col3 = st.columns([1, 2.5, 1])
with col2:
    logo_base64 = get_logo_base64("logo.png")

    st.markdown(
        f"""
        <div style='text-align: center;'>
            <img src='data:image/png;base64,{logo_base64}' width='400'>
        </div>
        """,
        unsafe_allow_html=True
    )


# --- Session State Init ---
for key in ["uploaded_file", "base64_image", "chat", "chat_history", "caption_text", "caption_chat", 
            "recipe_text", "recipe_chat","fashion_text", "fashion_chat", "travel_text", "travel_chat",
            "document_text", "document_chat", "funfact_text", "funfact_chat"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
if "prev_file_name" not in st.session_state:
    st.session_state["prev_file_name"] = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Top Bar with Reset + Mode Toggle ---
left_col, mid_col, right_col = st.columns([1, 5, 1])

with left_col:
    if st.button("🔄 New Chat"):
        keys_to_clear = [
                "uploaded_file", "base64_image", "chat", "chat_history", 
                "caption_text", "caption_chat", "recipe_text", "recipe_chat",
                "fashion_text", "fashion_chat", "travel_text", "travel_chat",
                "document_text", "document_chat", "funfact_text", "funfact_chat"
                ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["uploader_key"] += 1
        st.session_state["image_bytes"] = None
        st.rerun()

with right_col:
    available_modes = [
    "Analyze/Chat",
    "Get a caption",
    "Recipe mode",
    "Fashion mode",
    "Travel mode",
    "Document mode",
    "Fun fact mode"
]

    selected_mode = st.selectbox("🎛️ Select Mode", options=available_modes, index=available_modes.index(st.session_state.get("mode", "Analyze/Chat")))

    if selected_mode != st.session_state.get("mode"):
        st.session_state.mode = selected_mode
        st.rerun()
mode = st.session_state.mode

with mid_col:
    st.markdown(
        f"<div style='text-align:center; font-size:18px;'>🧭 <b>Current Mode:</b> {mode}</div>",
        unsafe_allow_html=True
    )


# --- File Upload ---
uploader_key = st.session_state.get("uploader_key", 0)
uploaded_file = st.file_uploader("📤 Upload an image", type=["jpg", "jpeg", "png"], key=uploader_key)

if uploaded_file:
    if uploaded_file.type not in ["image/jpeg", "image/png"]:
        st.error("❌ Invalid file type! Please upload JPG or PNG.")
    else:
        if uploaded_file.name != st.session_state["prev_file_name"]:
            st.session_state["caption_text"] = None
            st.session_state["caption_chat"] = None
            st.session_state["chat"] = None
            st.session_state["recipe_text"] = None
            st.session_state["recipe_chat"] = None
            st.session_state["fashion_text"] = None
            st.session_state["fashion_chat"] = None
            st.session_state["travel_text"] = None
            st.session_state["travel_chat"] = None
            st.session_state["document_text"] = None
            st.session_state["document_chat"] = None
            st.session_state["funfact_text"] = None
            st.session_state["funfact_chat"] = None
            st.session_state["chat_history"] = []
            st.session_state["prev_file_name"] = uploaded_file.name

        st.session_state.uploaded_file = uploaded_file
        file_bytes = uploaded_file.read()
        st.session_state.base64_image = image_to_base64(file_bytes, max_size=(1024, 1024))
        st.session_state["image_bytes"] = file_bytes  #Save raw image bytes

        if mode == "Analyze/Chat" and st.session_state.chat is None:
            st.session_state.chat = create_gemini_chat(st.session_state.base64_image)
            
# --- Display Image (even after rerun) ---
if st.session_state.get("base64_image"):
    st.markdown(f"""
    <div class="uploaded-image" style="text-align: center; max-width: 500px; margin: auto;">
        <img src='data:image/jpeg;base64,{st.session_state.base64_image}' width='100%' style="border-radius: 10px;" />
        <div style="margin-top: 10px; color: #666;">📷 Uploaded Image</div>
    </div>
""", unsafe_allow_html=True)


# --- UI Modular Functions ---
def render_caption_ui():
    st.subheader("📝 Image Caption:")
    if st.session_state.caption_text is None:
        with st.spinner("Generating..."):
            if st.session_state.caption_chat is None:
                st.session_state.caption_chat = create_gemini_chat(st.session_state.base64_image)
            st.session_state.caption_text = ask_gemini_chat(
                st.session_state.caption_chat,
                "You are an image captioning expert for social media. Provide a short, accurate caption for the uploaded image."
            )
    st.write(st.session_state.caption_text)
    if st.button("🔁 Generate another caption"):
        with st.spinner("Regenerating..."):
            st.session_state.caption_text = ask_gemini_chat(
                st.session_state.caption_chat,
                "Generate 5 more captions for this image."
            )
        st.rerun()

def render_chat_ui():
    chat_container = st.container()

    # If there's no chat history yet, show automatic image insight
    if len(st.session_state.chat_history) == 0:
        with st.spinner("Analyzing image..."):
            insight_prompt = "Analyze the uploaded image and provide a brief description of what it contains. Include any relevant objects, scenes, or possible context."
            insight_response = ask_gemini_chat(st.session_state.chat, insight_prompt)
            st.session_state.chat_history.append(("assistant", insight_response))

    # Display chat history
    with chat_container:
        for sender, msg in st.session_state.chat_history:
            with st.chat_message(sender):
                st.markdown(msg)

    st.divider()

    # Input prompt from user
    user_prompt = st.chat_input("Type your question about the image...")
    if user_prompt:
        st.session_state.chat_history.append(("user", user_prompt))
        with st.spinner("Thinking..."):
            reply = ask_gemini_chat(st.session_state.chat, user_prompt)
        st.session_state.chat_history.append(("assistant", reply))
        st.rerun()
        
def render_recipe_ui():
    st.subheader("🍽️ Suggested Dish & Recipe:")

    if st.session_state.get("recipe_text") is None:
        with st.spinner("Analyzing food image and generating recipe..."):
            if st.session_state.get("recipe_chat") is None:
                st.session_state.recipe_chat = create_gemini_chat(st.session_state.base64_image)

            response = ask_gemini_chat(
                st.session_state.recipe_chat,
                "You are a culinary expert. Based on the uploaded food image, suggest a dish that could be made and provide a detailed recipe including ingredients and steps. If the uploaded image does not contain any recognizable food items, respond with 'No food found to generate a recipe.'"
            )

            # Check for "no food found" response
            if "no food found" in response.lower():
                st.session_state.recipe_text = "❌ **No food items found to generate a recipe. Please upload different image.**"
            else:
                st.session_state.recipe_text = response

    st.markdown(st.session_state.recipe_text)

    if "no food items found" not in st.session_state.recipe_text.lower():
        if st.button("🔁 Suggest a different dish"):
            with st.spinner("Generating another dish idea..."):
                st.session_state.recipe_text = ask_gemini_chat(
                    st.session_state.recipe_chat,
                    "Suggest another different dish from the uploaded food image and provide its full recipe."
                )
            st.rerun()

def render_fashion_ui():
    st.subheader("👗 Outfit Insight:")
    if st.session_state.get("fashion_text") is None:
        with st.spinner("Analyzing fashion image..."):
            if st.session_state.get("fashion_chat") is None:
                st.session_state.fashion_chat = create_gemini_chat(st.session_state.base64_image)
            response = ask_gemini_chat(
                st.session_state.fashion_chat,
                "You are a fashion expert. Based on the uploaded image, describe the outfit and suggest a potential brand, style category, or how it could be styled. If this is not a fashion image, respond with 'No fashion-related items found.'"
            )
            if "no fashion" in response.lower():
                st.session_state.fashion_text = "❌ **No fashion-related items found. Please upload a different image.**"
            else:
                st.session_state.fashion_text = response
    st.markdown(st.session_state.fashion_text)

def render_travel_ui():
    st.subheader("🌍 Travel Suggestion:")
    if st.session_state.get("travel_text") is None:
        with st.spinner("Analyzing scenery image..."):
            if st.session_state.get("travel_chat") is None:
                st.session_state.travel_chat = create_gemini_chat(st.session_state.base64_image)
            response = ask_gemini_chat(
                st.session_state.travel_chat,
                "You are a travel expert. Based on the uploaded image, identify the possible location or region, and suggest travel tips or nearby tourist destinations. If it's not a travel-related scene, say 'Unable to identify a travel location.'"
            )
            if "unable to identify" in response.lower():
                st.session_state.travel_text = "❌ **Unable to identify a travel location. Please upload a scenic or landmark image.**"
            else:
                st.session_state.travel_text = response
    st.markdown(st.session_state.travel_text)

def render_document_ui():
    st.subheader("📄 Document Summary:")
    if st.session_state.get("document_text") is None:
        with st.spinner("Extracting and summarizing text..."):
            if st.session_state.get("document_chat") is None:
                st.session_state.document_chat = create_gemini_chat(st.session_state.base64_image)
            response = ask_gemini_chat(
                st.session_state.document_chat,
                "You are a document analysis assistant. Extract any visible text from the uploaded image and provide a concise summary. If the document has no readable text, reply 'No readable text found.'"
            )
            if "no readable text" in response.lower():
                st.session_state.document_text = "❌ **No readable text found. Please upload a clear document or form image.**"
            else:
                st.session_state.document_text = response
    st.markdown(st.session_state.document_text)

def render_funfact_ui():
    st.subheader("🎉 Fun Fact:")
    if st.session_state.get("funfact_text") is None:
        with st.spinner("Generating fun fact..."):
            if st.session_state.get("funfact_chat") is None:
                st.session_state.funfact_chat = create_gemini_chat(st.session_state.base64_image)
            response = ask_gemini_chat(
                st.session_state.funfact_chat,
                "You're a trivia expert. Based on the uploaded image, generate a surprising or educational fun fact related to what is shown in the picture. If you can't detect anything, respond with 'No fun fact could be generated.'"
            )
            if "no fun fact" in response.lower():
                st.session_state.funfact_text = "❌ **No fun fact could be generated. Try uploading a different image.**"
            else:
                st.session_state.funfact_text = response
    st.markdown(st.session_state.funfact_text)

    if "no fun fact" not in st.session_state.funfact_text.lower():
        if st.button("🎲 Generate another fun fact"):
            with st.spinner("Thinking..."):
                st.session_state.funfact_text = ask_gemini_chat(
                    st.session_state.funfact_chat,
                    "Generate another fun fact based on the uploaded image."
                )
            st.rerun()



# --- Mode Handler ---
if st.session_state.get("image_bytes"):
    if st.session_state.uploaded_file:
        if mode == "Get a caption":
            render_caption_ui()
        elif mode == "Analyze/Chat":
            render_chat_ui()
        elif mode == "Recipe mode":
            render_recipe_ui()
        elif mode == "Fashion mode":
            render_fashion_ui()
        elif mode == "Travel mode":
            render_travel_ui()
        elif mode == "Document mode":
            render_document_ui()
        elif mode == "Fun fact mode":
            render_funfact_ui()

else:
    st.info("👆 Please upload an image to get started.")


