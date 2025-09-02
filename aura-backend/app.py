from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash
import database as db
import simulator # <-- IMPORT THE SIMULATOR

app = Flask(__name__)
CORS(app) 

@app.route('/')
def home():
    return "Project Aura Backend is running!"

# --- Authentication and User Management ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if data and data.get('username') and data.get('password'):
        print(f"Received registration for user: {data.get('username')}")
        return jsonify({'message': 'User registered successfully (mock response)'}), 201
    return jsonify({'error': 'Missing username or password'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get('username') == 'testuser' and data.get('password') == 'password123':
        print(f"User 'testuser' logged in.")
        return jsonify({'message': 'Login successful (mock response)', 'token': 'mock_jwt_token_string'})
    return jsonify({'error': 'Invalid credentials'}), 401

# --- API Endpoints ---

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    print("Dashboard data requested.")
    mock_data = { 'glucose_readings': [ {'timestamp': '2025-09-01T08:00:00Z', 'value': 110} ] } # Abridged for clarity
    return jsonify(mock_data)

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

# --- THIS IS THE NEW ENDPOINT ---
@app.route('/api/dev/simulate-data', methods=['POST'])
def simulate_data_endpoint():
    """
    An endpoint to trigger the data simulator for the test user (user_id=1).
    This is a critical tool for frontend development.
    """
    try:
        print("Simulator endpoint called. Generating data for user 1...")
        simulator.generate_and_insert_data(user_id=1, days_of_data=3)
        return jsonify({'message': 'Successfully generated and inserted 3 days of new data for user 1.'}), 200
    except Exception as e:
        print(f"An error occurred in the simulator endpoint: {e}")
        return jsonify({'error': 'An internal error occurred while generating data.'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)