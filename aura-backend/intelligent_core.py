# file: intelligent_core.py

# --- Import all the AI components you have built ---

from natural_language_processor import EnhancedNLPProcessor
# --- We now import your NEW master prediction function ---
from prediction_service import generate_hybrid_prediction
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
    This is the only function the main server (app.py) needs to call.
    """
    
    print(f"--- [AI Core] Processing new intent: '{user_text}' ---")
    
    # 1. UNDERSTAND: Use your NLP to get structured data from text.
    parsed_entities = NLP_PROCESSOR.parse_user_text(user_text)
    carbs = parsed_entities.get("carbs", 0)
    activity_info = parsed_entities.get("activities_detected", [])
    activity_detected = len(activity_info) > 0
    
    # 2. RECOMMEND: Get a dose recommendation from the RL agent service.
    current_glucose = glucose_history[-1] if glucose_history else 120
    dose_recommendation = get_insulin_recommendation(
        glucose=current_glucose,
        carbs=carbs,
        exercise_recent=activity_detected
    )
    
    # 3. PREDICT: Use the new HYBRID prediction function.
    # We create the 'future_events' dictionary from the NLP output.
    future_events = {
        "carbs": carbs,
        "activity_type": activity_info[0]['activity'] if activity_info else None,
        "activity_duration": activity_info[0]['duration_minutes'] if activity_info else 0
    }
    
    # Call the new master prediction function with the context.
    hybrid_prediction = generate_hybrid_prediction(
        recent_glucose_history=glucose_history,
        future_events=future_events
    )
    
    # 4. ADVISE: Get contextual advice from the NLP module.
    contextual_advice = NLP_PROCESSOR.get_insulin_adjustment_suggestion(parsed_entities)
    
    # 5. ASSEMBLE: Package everything into a single, clean JSON object.
    response = {
        "parsed_info": parsed_entities,
        "dose_recommendation": dose_recommendation,
        "glucose_prediction": hybrid_prediction, # The frontend gets the full rich object
        "contextual_advice": contextual_advice
    }
    
    print(f"--- [AI Core] Intent processed successfully. ---")
    return response