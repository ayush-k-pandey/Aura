import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import database as db
import simulator

# --- The main AI import ---
from intelligent_core import process_user_intent

app = Flask(__name__)
CORS(app) 

@app.route('/')
def home():
    return "Project Aura Backend is running!"

# ==================================================================
# === REAL AUTHENTICATION ENDPOINTS ================================
# ==================================================================

@app.route("/register", methods=['POST'])
def register():
    """
    Handles new user registration with complete profile information from the form.
    """
    data = request.get_json()
    
    # Extract all data from the frontend's request
    username = data.get('username') # The user ID or email
    password = data.get('password')
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')
    phone_number = data.get('phone_number')
    weight_kg = data.get('weight_kg')
    height_cm = data.get('height_cm')

    # Validate the essential data
    if not username or not password or not name:
        return jsonify({"error": "Username, password, and name are required"}), 400

    if db.find_user_by_username(username):
        return jsonify({"error": "Username already taken. Please choose another."}), 409

    hashed_password = generate_password_hash(password)
    
    conn = db.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (username, password_hash, name, age, gender, phone_number, weight_kg, height_cm)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (username, hashed_password, name, age, gender, phone_number, weight_kg, height_cm)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "User registered successfully!"}), 201


@app.route("/login", methods=['POST'])
def login():
    """
    Handles user login by checking credentials against the database.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = db.find_user_by_username(username)

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid username or password"}), 401

    # On successful login, send the user's ID back to the frontend.
    # The frontend will store this ID and use it for all future API calls.
    return jsonify({
        "message": "Login successful",
        "token": "mock_jwt_for_hackathon",
        "user_id": user['id'] # This is CRITICAL for the frontend
    })

# ==================================================================
# === THE PRIMARY AI ENDPOINT ======================================
# ==================================================================
@app.route("/api/chat", methods=['POST'])
def handle_chat_intent():
    """
    This single endpoint handles all user conversational input.
    """
    data = request.get_json()
    
    user_message = data.get('message')
    # NOTE: A real app gets this from a secure token. For the demo, frontend will send it.
    user_id = data.get('user_id')

    if not user_message or not user_id:
        return jsonify({"error": "A 'message' and 'user_id' are required"}), 400
        
    # --- THIS IS NO LONGER MOCK DATA ---
    # We now fetch the REAL, most recent glucose history for THIS specific user.
    # Note: If a new user has no data, this will be an empty list, which is okay.
    glucose_history = db.get_recent_glucose_readings(user_id, limit=12)

    ai_response = process_user_intent(
        user_text=user_message,
        glucose_history=glucose_history
    )
    
    return jsonify(ai_response)

# ==================================================================
# === DATA RETRIEVAL & DEV TOOLS ===================================
# ==================================================================

@app.route("/api/dashboard", methods=['GET'])
def get_dashboard():
    """
    Provides all dashboard data for a specific user.
    """
    user_id = request.args.get('user_id') # e.g., /api/dashboard?user_id=1
    if not user_id:
        return jsonify({"error": "A 'user_id' query parameter is required"}), 400

    dashboard_data = db.get_dashboard_data_for_user(user_id)
    return jsonify(dashboard_data)

@app.route('/api/dev/simulate-data', methods=['POST'])
def simulate_data_endpoint():
    """
    Generates data for a specific user. Frontend needs to provide the user_id.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "A 'user_id' is required in the request body"}), 400
    try:
        # NOTE: Your simulator.py might need a small update to accept user_id.
        simulator.generate_and_insert_data(user_id=user_id, days_of_data=3)
        return jsonify({'message': f'Successfully generated 3 days of data for user {user_id}.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Using port 5001 is good practice to avoid conflicts
    app.run(debug=True, port=5001)