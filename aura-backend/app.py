# file: app.py (Final, Streamlined Version)

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import database as db
import simulator

# --- The ONLY AI import you need ---
from intelligent_core import process_user_intent

app = Flask(__name__)
CORS(app) 

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return "Project Aura Backend is running!"

# ==================================================================
# === THE PRIMARY & ONLY AI ENDPOINT ===============================
# ==================================================================
@app.route("/api/chat", methods=['POST'])
def handle_chat_intent():
    """
    This single endpoint handles all user conversational input.
    """
    print("\n--- Received request at /api/chat ---")
    data = request.get_json()
    
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "No 'message' key provided"}), 400

    # --- Database Integration Point ---
    # In a real app, you get the user_id from their auth token.
    # user_id = get_user_from_token(request) 
    
    # Then, you fetch their REAL glucose history from the database.
    # real_glucose_history = db.get_recent_glucose_readings(user_id, limit=12)

    # For the hackathon, we use a mock list which is perfectly fine for the demo.
    mock_glucose_history = [120, 122, 125, 126, 128, 129, 130, 131, 130, 128, 126, 124]
        
    print(f"-> User Message: '{user_message}'")
    
    # This one line runs your entire AI system.
    ai_response = process_user_intent(
        user_text=user_message,
        glucose_history=mock_glucose_history
    )
    
    print("--- AI Core processed intent successfully ---")
    # The frontend receives a single, powerful JSON object to update the entire UI.
    return jsonify(ai_response)
# ==================================================================
# ==================================================================

# --- Other essential routes can stay ---
# (Login, Register, and Dev tools are fine)

@app.route('/dev/add-test-user')
def add_test_user():
    # ... (no changes needed)
    pass # Keep existing code

@app.route('/api/dev/simulate-data', methods=['POST'])
def simulate_data_endpoint():
    # ... (no changes needed)
    pass # Keep existing code

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Use standard port 5000