import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def create_gemini_chat(base64_image):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat(history=[])
        chat.send_message([
            {"text": "This image will be the context for our conversation."},
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_image
                }
            }
        ])
        return chat
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Gemini chat: {e}")

def ask_gemini_chat(chat, user_input):
    try:
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        return f"⚠️ Error from Gemini: {e}"
