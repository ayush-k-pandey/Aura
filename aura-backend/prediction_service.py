# file: enhanced_prediction_service.py
import numpy as np
import joblib
from keras.models import load_model
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# --- Load artifacts ONCE when the server starts ---
print("Loading enhanced LSTM model and scaler for prediction service...")
MODEL = load_model('glucose_predictor.h5')
SCALER = joblib.load('scaler.gz')
LOOK_BACK = 12  # Must match training configuration

# Glucose physiological constraints
MIN_GLUCOSE = 40   # mg/dL - physiological minimum
MAX_GLUCOSE = 400  # mg/dL - physiological maximum
MAX_CHANGE_RATE = 4  # mg/dL per 5min - maximum realistic change rate

class GlucosePredictionError(Exception):
    """Custom exception for prediction errors"""
    pass

def validate_glucose_history(glucose_history: list) -> list:
    """
    Validates and cleans glucose history data.
    
    Args:
        glucose_history: List of glucose readings
        
    Returns:
        Cleaned list of glucose values
        
    Raises:
        GlucosePredictionError: If validation fails
    """
    if not glucose_history:
        raise GlucosePredictionError("Empty glucose history provided")
    
    if len(glucose_history) < LOOK_BACK:
        raise GlucosePredictionError(f"Insufficient history: need at least {LOOK_BACK} readings, got {len(glucose_history)}")
    
    # Convert to float and validate range
    cleaned_history = []
    for i, value in enumerate(glucose_history):
        try:
            glucose_val = float(value)
            if not (MIN_GLUCOSE <= glucose_val <= MAX_GLUCOSE):
                raise GlucosePredictionError(f"Glucose value {glucose_val} at index {i} outside valid range ({MIN_GLUCOSE}-{MAX_GLUCOSE})")
            cleaned_history.append(glucose_val)
        except (ValueError, TypeError):
            raise GlucosePredictionError(f"Invalid glucose value at index {i}: {value}")
    
    # Check for unrealistic changes
    for i in range(1, len(cleaned_history)):
        change_rate = abs(cleaned_history[i] - cleaned_history[i-1])
        if change_rate > MAX_CHANGE_RATE * 3:  # Allow some flexibility for historical data
            print(f"Warning: Large glucose change detected: {change_rate:.1f} mg/dL between readings {i-1} and {i}")
    
    return cleaned_history

def apply_physiological_constraints(predictions: list, last_known_value: float) -> list:
    """
    Applies physiological constraints to predictions to ensure realistic values.
    
    Args:
        predictions: Raw model predictions
        last_known_value: Last known glucose value
        
    Returns:
        Constrained predictions
    """
    constrained = []
    prev_value = last_known_value
    
    for pred in predictions:
        # Limit rate of change
        max_change = MAX_CHANGE_RATE
        if pred > prev_value + max_change:
            pred = prev_value + max_change
        elif pred < prev_value - max_change:
            pred = prev_value - max_change
        
        # Ensure within physiological bounds
        pred = max(MIN_GLUCOSE, min(MAX_GLUCOSE, pred))
        
        constrained.append(pred)
        prev_value = pred
    
    return constrained

def add_prediction_noise(predictions: list, noise_factor: float = 0.02) -> list:
    """
    Adds realistic noise to predictions to account for natural glucose variability.
    
    Args:
        predictions: Clean predictions
        noise_factor: Amount of noise to add (fraction of value)
        
    Returns:
        Predictions with added variability
    """
    noisy_predictions = []
    for pred in predictions:
        # Add small random variation (typically 1-3 mg/dL)
        noise = np.random.normal(0, pred * noise_factor)
        noisy_pred = pred + noise
        noisy_predictions.append(max(MIN_GLUCOSE, min(MAX_GLUCOSE, noisy_pred)))
    
    return noisy_predictions

def calculate_trend_confidence(glucose_history: list) -> dict:
    """
    Calculates trend information and prediction confidence.
    
    Args:
        glucose_history: Recent glucose readings
        
    Returns:
        Dictionary with trend analysis
    """
    recent_values = glucose_history[-LOOK_BACK:]
    
    # Calculate linear trend
    x = np.arange(len(recent_values))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_values)
    
    # Calculate variability
    glucose_std = np.std(recent_values)
    glucose_range = max(recent_values) - min(recent_values)
    
    # Determine trend direction
    if abs(slope) < 0.5:
        trend = "stable"
    elif slope > 0.5:
        trend = "rising"
    else:
        trend = "falling"
    
    # Calculate confidence based on data quality
    confidence = min(100, max(30, 100 - (glucose_std * 2) - (abs(slope) * 5)))
    
    return {
        "trend": trend,
        "slope": round(slope, 2),
        "confidence": round(confidence, 1),
        "variability": round(glucose_std, 2),
        "r_squared": round(r_value**2, 3)
    }

def predict_future_glucose(recent_glucose_history: list, include_analysis: bool = False) -> dict:
    """
    Enhanced glucose prediction with validation, constraints, and analysis.
    
    Args:
        recent_glucose_history: List of recent glucose readings
        include_analysis: Whether to include trend analysis
    
    Returns:
        Dictionary containing predictions and optional analysis
        
    Raises:
        GlucosePredictionError: If prediction fails
    """
    try:
        # Step 1: Validate input data
        cleaned_history = validate_glucose_history(recent_glucose_history)
        
        # Step 2: Prepare model input
        input_data = np.array(cleaned_history[-LOOK_BACK:]).reshape(-1, 1)
        scaled_input = SCALER.transform(input_data)
        
        predictions = []
        current_sequence = scaled_input.reshape((1, LOOK_BACK, 1))
        
        # Step 3: Generate predictions with improved methodology
        for step in range(12):
            # Predict next value
            pred_scaled = MODEL.predict(current_sequence, verbose=0)
            
            # Convert back to glucose units
            pred_glucose = SCALER.inverse_transform(pred_scaled)[0][0]
            predictions.append(pred_glucose)
            
            # Update sequence for next prediction
            new_sequence = np.append(current_sequence[0][1:], pred_scaled)
            current_sequence = new_sequence.reshape((1, LOOK_BACK, 1))
        
        # Step 4: Apply physiological constraints
        last_known = cleaned_history[-1]
        constrained_predictions = apply_physiological_constraints(predictions, last_known)
        
        # Step 5: Add realistic variability
        final_predictions = add_prediction_noise(constrained_predictions)
        
        # Convert to integers
        int_predictions = [int(round(pred)) for pred in final_predictions]
        
        # Prepare response
        response = {
            "prediction": int_predictions,
            "status": "success",
            "input_length": len(cleaned_history),
            "last_known_glucose": int(last_known)
        }
        
        # Add analysis if requested
        if include_analysis:
            analysis = calculate_trend_confidence(cleaned_history)
            response["analysis"] = analysis
            
            # Add prediction metadata
            response["metadata"] = {
                "prediction_horizon_minutes": 60,
                "time_step_minutes": 5,
                "model_confidence": analysis["confidence"],
                "notes": [
                    f"Current trend: {analysis['trend']}",
                    f"Variability: {analysis['variability']:.1f} mg/dL",
                    "Predictions include physiological constraints"
                ]
            }
        
        return response
        
    except GlucosePredictionError as e:
        return {
            "prediction": [],
            "status": "error",
            "error_message": str(e)
        }
    except Exception as e:
        return {
            "prediction": [],
            "status": "error", 
            "error_message": f"Unexpected error: {str(e)}"
        }

# Backward compatibility function
def predict_future_glucose_simple(recent_glucose_history: list) -> list:
    """
    Simple version maintaining backward compatibility.
    Returns empty list on error (original behavior).
    """
    result = predict_future_glucose(recent_glucose_history)
    return result.get("prediction", [])

# Additional utility functions for API endpoints
def get_prediction_with_confidence(recent_glucose_history: list) -> dict:
    """Get prediction with full analysis and confidence metrics."""
    return predict_future_glucose(recent_glucose_history, include_analysis=True)

def validate_model_health() -> dict:
    """Basic health check for the prediction service."""
    try:
        # Test with dummy data
        test_data = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122]
        result = predict_future_glucose(test_data)
        
        return {
            "status": "healthy",
            "model_loaded": MODEL is not None,
            "scaler_loaded": SCALER is not None,
            "test_prediction_success": result["status"] == "success"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
def generate_hybrid_prediction(
    recent_glucose_history: list,
    future_events: dict = None
) -> dict:
    """
    This is the new master function that the intelligent_core will call.
    It combines the LSTM model's prediction with logical adjustments for
    real-world events like meals and exercise.
    
    Args:
        recent_glucose_history: List of recent glucose readings.
        future_events: A dictionary describing upcoming events, e.g.,
                       {'carbs': 50, 'activity_type': 'walk', 'activity_duration': 30}
                       
    Returns:
        A complete prediction dictionary, adjusted for real-world context.
    """
    
    # 1. Get the baseline prediction from your powerful, constrained model.
    baseline_response = predict_future_glucose(recent_glucose_history, include_analysis=True)
    
    if baseline_response["status"] == "error":
        return baseline_response # If the base prediction fails, just return the error.
        
    adjusted_predictions = list(baseline_response["prediction"]) # Start with the model's prediction
    
    if future_events:
        # 2. Apply Meal Logic (Heuristic Adjustment)
        if future_events.get("carbs", 0) > 0:
            carbs = future_events["carbs"]
            # Simple model: a meal's effect starts after 15 mins (3 steps) and peaks around 1 hour (12 steps).
            # Each 10g of carbs might raise BG by ~30-40 mg/dL over an hour.
            carb_impact_per_step = (carbs / 10) * 3.5 / 12 # Distribute the rise over the hour
            
            for i in range(len(adjusted_predictions)):
                if i >= 3: # Effect starts after 15 mins
                    adjusted_predictions[i] += carb_impact_per_step * (i - 2) # Gradual rise

        # 3. Apply Exercise Logic (Heuristic Adjustment)
        if future_events.get("activity_type"):
            # Simple model: a walk's effect starts after 10 mins (2 steps) and lowers BG.
            # A 30-min walk might lower BG by 20-30 mg/dL.
            activity_impact_per_step = 25 / 12 # Distribute the drop over the hour
            
            for i in range(len(adjusted_predictions)):
                if i >= 2: # Effect starts after 10 mins
                    adjusted_predictions[i] -= activity_impact_per_step

    # 4. Re-apply constraints to the adjusted curve and finalize
    last_known = baseline_response["last_known_glucose"]
    final_predictions = apply_physiological_constraints(adjusted_predictions, last_known)
    final_predictions = [int(round(p)) for p in final_predictions]
    
    # 5. Update the response object with the new, adjusted prediction
    baseline_response["adjusted_prediction"] = final_predictions
    baseline_response["original_prediction"] = baseline_response.pop("prediction") # Rename for clarity
    
    if future_events:
        baseline_response["metadata"]["notes"].append(
            f"Prediction adjusted for upcoming events: {future_events}"
        )
        
    return baseline_response