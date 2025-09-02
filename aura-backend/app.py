import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash
import database as db
import simulator

# --- ALL AI IMPORTS ---
# Import the individual services for their dedicated endpoints
import prediction_service
import recommendation_service
# Import the master function for the new consolidated endpoint
from intelligent_core import process_user_intent

app = Flask(__name__)
CORS(app) 

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return "Project Aura Backend is running!"

# --- Authentication and User Management ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get('username') == 'testuser' and data.get('password') == 'password123':
        return jsonify({'message': 'Login successful (mock response)', 'token': 'mock_jwt_token_string'})
    return jsonify({'error': 'Invalid credentials'}), 401


# --- THE NEW CONSOLIDATED AI ENDPOINT ---
@app.route("/api/chat", methods=['POST'])
def handle_chat_intent():
    """ The new main entry point for the AI system. """
    data = request.get_json()
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
        
    mock_glucose_history = [120, 122, 125, 126, 128, 129, 130, 131, 130, 128, 126, 124]
    
    ai_response = process_user_intent(
        user_text=user_message, 
        glucose_history=mock_glucose_history
    )
    
    return jsonify(ai_response)


# --- ORIGINAL AI & UTILITY ENDPOINTS (Kept for direct access and testing) ---

@app.route('/api/glucose/prediction', methods=['POST'])
def get_glucose_prediction():
    data = request.get_json()
    if not data or 'recent_glucose' not in data:
        return jsonify({'error': 'Missing "recent_glucose" in request body'}), 400
    predictions = prediction_service.predict_future_glucose(data['recent_glucose'])
    return jsonify({'predictions': predictions})

@app.route('/api/dose/recommendation', methods=['POST'])
def get_dose_recommendation():
    data = request.get_json()
    if not data or 'current_glucose' not in data:
        return jsonify({'error': 'Missing "current_glucose" in request body'}), 400
    
    recommendation = recommendation_service.get_insulin_recommendation(
        glucose=data['current_glucose'],
        carbs=data.get('meal_carbs', 0)
    )
    
    if "error" in recommendation:
        return jsonify(recommendation), 500
    return jsonify(recommendation)

@app.route('/api/meal/upload-image', methods=['POST'])
def upload_meal_image():
    if 'meal_image' not in request.files:
        return jsonify({'error': 'No meal_image file part in the request'}), 400
    file = request.files['meal_image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        mock_carb_count = 55.0
        return jsonify({ 'message': 'File uploaded successfully', 'filename': filename, 'carb_count': mock_carb_count })

@app.route('/api/dev/simulate-data', methods=['POST'])
def simulate_data_endpoint():
    try:
        simulator.generate_and_insert_data(user_id=1, days_of_data=3)
        return jsonify({'message': 'Successfully generated and inserted 3 days of new data for user 1.'}), 200
    except Exception as e:
        return jsonify({'error': 'An internal error occurred while generating data.'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)