import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import database as db
import simulator
from intelligent_core import process_user_intent

app = Flask(__name__)

# --- UPGRADED CORS CONFIGURATION ---
# This explicitly allows your frontend's origin to access the backend API.
# NOTE: Update the origin port if your frontend runs on a different one (e.g., 3000 for React)
CORS(app, origins="http://127.0.0.1:5500")
# ------------------------------------

@app.route('/')
def home():
    return "Project Aura Backend is running!"

@app.route("/register", methods=['POST'])
def register():
    data = request.get_json()
    username, password, name = data.get('username'), data.get('password'), data.get('name')
    age, gender, phone, weight, height = data.get('age'), data.get('gender'), data.get('phone_number'), data.get('weight_kg'), data.get('height_cm')

    if not all([username, password, name]):
        return jsonify({"error": "Username, password, and name are required"}), 400

    if db.find_user_by_username(username):
        return jsonify({"error": "Username already taken"}), 409

    hashed_password = generate_password_hash(password)
    conn = db.get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, name, age, gender, phone_number, weight_kg, height_cm) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (username, hashed_password, name, age, gender, phone, weight, height)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "User registered successfully!"}), 201

@app.route("/login", methods=['POST'])
def login():
    data = request.get_json()
    username, password = data.get('username'), data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = db.find_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"message": "Login successful", "token": "mock_jwt_for_hackathon", "user_id": user['id']})

@app.route("/api/chat", methods=['POST'])
def handle_chat_intent():
    data = request.get_json()
    user_message, user_id = data.get('message'), data.get('user_id')
    if not user_message or not user_id:
        return jsonify({"error": "A 'message' and 'user_id' are required"}), 400
        
    glucose_history = db.get_recent_glucose_readings(user_id, limit=12)
    ai_response = process_user_intent(user_text=user_message, glucose_history=glucose_history)
    return jsonify(ai_response)

@app.route("/api/dashboard", methods=['GET'])
def get_dashboard():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "A 'user_id' query parameter is required"}), 400

    dashboard_data = db.get_dashboard_data_for_user(user_id)
    return jsonify(dashboard_data)

@app.route('/api/dev/simulate-data', methods=['POST'])
def simulate_data_endpoint():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "A 'user_id' is required"}), 400
    try:
        simulator.generate_and_insert_data(user_id=user_id, days_of_data=3)
        return jsonify({'message': f'Successfully generated 3 days of data for user {user_id}.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)