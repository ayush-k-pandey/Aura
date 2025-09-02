import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash
import database as db
import simulator

# --- AI INTEGRATION: Import both services from Developer 2 ---
import prediction_service
import recommendation_service

app = Flask(__name__)
CORS(app) 

# Configure the uploads folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def home():
    return "Project Aura Backend is running!"

# --- Authentication and User Management ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if data and data.get('username') and data.get('password'):
        return jsonify({'message': 'User registered successfully (mock response)'}), 201
    return jsonify({'error': 'Missing username or password'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get('username') == 'testuser' and data.get('password') == 'password123':
        return jsonify({'message': 'Login successful (mock response)', 'token': 'mock_jwt_token_string'})
    return jsonify({'error': 'Invalid credentials'}), 401

# --- Core API Endpoints ---

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    # This data is still hardcoded. A future step would be to fetch it from the database.
    mock_data = { 'glucose_readings': [ {'timestamp': '2025-09-01T08:00:00Z', 'value': 110} ] }
    return jsonify(mock_data)

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
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'carb_count': mock_carb_count
        })

# --- AI Integration Endpoints ---

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


# --- Developer / Helper Endpoints ---

@app.route('/dev/add-test-user')
def add_test_user():
    hashed_password = generate_password_hash('password123')
    conn = None
    try:
        conn = db.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s;", ('testuser',))
        if cur.fetchone():
            return jsonify({'message': 'Test user already exists.'})
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", ('testuser', hashed_password))
        conn.commit()
        return jsonify({'message': 'Test user "testuser" added successfully.'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/dev/simulate-data', methods=['POST'])
def simulate_data_endpoint():
    try:
        simulator.generate_and_insert_data(user_id=1, days_of_data=3)
        return jsonify({'message': 'Successfully generated and inserted 3 days of new data for user 1.'}), 200
    except Exception as e:
        return jsonify({'error': 'An internal error occurred while generating data.'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)