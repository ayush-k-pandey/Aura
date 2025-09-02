# file: prediction_service.py

import numpy as np
import joblib
from keras.models import load_model

# --- Load artifacts ONCE when the server starts ---
# This is a critical optimization. We load the model into memory only one time
# instead of loading it every time a prediction is requested.
print("Loading LSTM model and scaler for prediction service...")
MODEL = load_model('glucose_predictor.h5')
SCALER = joblib.load('scaler.gz')
LOOK_BACK = 12  # This MUST match the value used during training in Colab

def predict_future_glucose(recent_glucose_history: list) -> list:
    """
    Predicts glucose values for the next hour (12 steps of 5 mins).
    
    This is the only function your teammate will ever need to call.
    
    Args:
        recent_glucose_history: A list of the last 12 (or more) integer glucose readings.
    
    Returns:
        A list of 12 predicted integer glucose values for the next hour.
    """
    if len(recent_glucose_history) < LOOK_BACK:
        # We cannot predict if we don't have enough historical data.
        # Return an empty list so the frontend knows there's no prediction.
        return []

    # 1. Get the most recent data points needed for a single prediction.
    input_data = np.array(recent_glucose_history[-LOOK_BACK:]).reshape(-1, 1)

    # 2. Scale the input data using the loaded scaler. The model was trained on
    #    scaled data, so it expects its input in the same format.
    scaled_input = SCALER.transform(input_data)
    
    predictions = []
    current_sequence = scaled_input.reshape((1, LOOK_BACK, 1))

    # 3. Predict one step at a time, 12 times.
    for _ in range(12): # Predict 12 steps (1 hour) into the future
        # Get the model's prediction (which is scaled)
        pred = MODEL.predict(current_sequence, verbose=0)
        
        # Un-scale the prediction to get a real glucose value (e.g., 150 mg/dL)
        unscaled_pred = SCALER.inverse_transform(pred)
        predictions.append(int(unscaled_pred[0][0]))
        
        # 4. Update the sequence by removing the oldest value and adding the new prediction.
        #    This is how we "look further" into the future, one step at a time.
        new_sequence = np.append(current_sequence[0][1:], pred)
        current_sequence = new_sequence.reshape((1, LOOK_BACK, 1))

    return predictions