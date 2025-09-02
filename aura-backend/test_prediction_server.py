# file: test_prediction_server.py

from flask import Flask, request, jsonify

# IMPORTANT: We import the function you created in the previous step
from prediction_service import predict_future_glucose

# Initialize a new Flask application
app = Flask(__name__)

# Define the API endpoint. We'll access it at http://localhost:5001/api/predict
# methods=['POST'] means this endpoint only accepts POST requests.
@app.route("/api/predict", methods=['POST'])
def handle_prediction():
    print("Received a request at /api/predict")
    
    # 1. Get the JSON data sent from the request
    data = request.get_json()
    
    # 2. Basic validation: Check if data exists and has the 'history' key
    if not data or 'history' not in data:
        # Return an error message with a 400 Bad Request status code
        return jsonify({"error": "Invalid request. 'history' key is missing."}), 400
        
    history_data = data['history']
    print(f"Received glucose history: {history_data}")

    # 3. Call your AI function with the provided data
    # This is the moment of truth!
    predictions = predict_future_glucose(history_data)
    
    print(f"Model generated predictions: {predictions}")

    # 4. Return the predictions as a JSON response
    # The jsonify function correctly formats our dictionary into a JSON response
    return jsonify({"prediction": predictions})


# This block makes the server runnable directly from the command line
if __name__ == '__main__':
    # We use port 5001 to avoid conflicts with your teammate's main app.py (usually on port 5000)
    print("Starting Flask test server on http://127.0.0.1:5001")
    app.run(debug=True, port=5001)