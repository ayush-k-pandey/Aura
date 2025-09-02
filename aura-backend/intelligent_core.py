# file: intelligent_core.py

# --- Import all the AI components you have built ---

# Your enhanced NLP class is inside this file
from natural_language_processor import EnhancedNLPProcessor

# The function from your first trained model
from prediction_service import predict_future_glucose

# The function from your second trained model (the RL agent)
from recommendation_service import get_insulin_recommendation


# --- Initialize the AI components ---
# We create one instance of your NLP processor to use everywhere.
# This is efficient as it builds the lookup maps only once.
print("Initializing Enhanced NLP Processor...")
NLP_PROCESSOR = EnhancedNLPProcessor()
print("NLP Processor ready.")


def process_user_intent(user_text: str, glucose_history: list) -> dict:
    """
    The main brain of the Aura AI system.
    This function takes the user's raw text and current glucose data,
    and returns a complete situational analysis and set of recommendations.
    This is the only function the main server (app.py) needs to call.
    """
    
    print(f"--- [AI Core] Processing new intent: '{user_text}' ---")
    
    # 1. UNDERSTAND: Use your enhanced NLP to convert raw text into structured data.
    parsed_entities = NLP_PROCESSOR.parse_user_text(user_text)
    carbs = parsed_entities.get("carbs", 0)
    activity_detected = len(parsed_entities.get("activities_detected", [])) > 0
    
    # 2. RECOMMEND: Get a dose recommendation from the RL agent service.
    # We use the parsed carbs and activity to provide context.
    current_glucose = glucose_history[-1] if glucose_history else 120 # Use last known glucose or a default
    dose_recommendation = get_insulin_recommendation(
        glucose=current_glucose,
        carbs=carbs,
        exercise_recent=activity_detected
    )
    
    # 3. PREDICT: Get the future glucose forecast from the LSTM model service.
    # This shows the user what might happen if they do nothing.
    predicted_curve = predict_future_glucose(glucose_history)
    
    # 4. ADVISE: Get contextual advice from the NLP module's advanced logic.
    contextual_advice = NLP_PROCESSOR.get_insulin_adjustment_suggestion(parsed_entities)
    
    # 5. ASSEMBLE: Package everything into a single, clean JSON object.
    # This object has everything the frontend needs to update the entire user interface.
    response = {
        "parsed_info": parsed_entities,
        "dose_recommendation": dose_recommendation,
        "glucose_prediction": predicted_curve,
        "contextual_advice": contextual_advice
    }
    
    print(f"--- [AI Core] Intent processed successfully. ---")
    return response