import random
import psycopg2
from datetime import datetime, timedelta, timezone
from database import get_db_connection

def clear_user_data(user_id):
    """Deletes all non-user data for a specific user to ensure a clean slate."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM meal_logs WHERE user_id = %s;", (user_id,))
        cur.execute("DELETE FROM insulin_doses WHERE user_id = %s;", (user_id,))
        cur.execute("DELETE FROM glucose_readings WHERE user_id = %s;", (user_id,))
        conn.commit()
        print(f"Cleared existing data for user_id: {user_id}")
    except Exception as e:
        print(f"An error occurred while clearing data: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

def generate_and_insert_data(user_id, days_of_data=3):
    """
    Generates and inserts realistic time-series glucose, meal, and insulin data
    for a specified user over a number of days.
    """
    clear_user_data(user_id) # Start with a clean slate
    conn = get_db_connection()
    cur = conn.cursor()

    # Simulation parameters
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days_of_data)
    current_time = start_time
    
    current_glucose = random.randint(90, 120) 
    
    glucose_readings_to_insert = []

    print(f"Generating data from {start_time} to {now}...")
    while current_time < now:
        current_glucose += random.uniform(-1.5, 1.5)
        if current_glucose < 40:
            current_glucose = 40
        
        if (7 <= current_time.hour <= 9 or 12 <= current_time.hour <= 14 or 18 <= current_time.hour <= 20):
            if random.random() < 0.30:
                meal_carbs = random.randint(30, 80)
                meal_description = "Simulated Meal"
                cur.execute(
                    "INSERT INTO meal_logs (user_id, timestamp, meal_description, carb_count) VALUES (%s, %s, %s, %s)",
                    (user_id, current_time, meal_description, meal_carbs)
                )
                
                insulin_dose = round(meal_carbs / 15, 1)
                cur.execute(
                    "INSERT INTO insulin_doses (user_id, timestamp, dose_amount, dose_type) VALUES (%s, %s, %s, %s)",
                    (user_id, current_time, insulin_dose, 'bolus')
                )
                current_glucose += meal_carbs * 0.5 

        if current_glucose > 140:
            current_glucose -= random.uniform(1, 3)

        glucose_readings_to_insert.append((user_id, current_time, round(current_glucose, 2)))
        current_time += timedelta(minutes=5)

    # --- CODE CHANGE HERE: Using a simple loop for insertion ---
    print(f"Inserting {len(glucose_readings_to_insert)} glucose readings one by one...")
    try:
        # Loop through our collected data and insert it row by row
        for reading in glucose_readings_to_insert:
            cur.execute(
                "INSERT INTO glucose_readings (user_id, timestamp, glucose_value) VALUES (%s, %s, %s)",
                reading
            )
        
        # Commit all the changes at once after the loop finishes
        conn.commit()
        print(f"Successfully inserted {len(glucose_readings_to_insert)} glucose readings.")
    except Exception as e:
        print(f"An error occurred during insert: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    print("Running data simulator standalone...")
    generate_and_insert_data(user_id=1, days_of_data=3)
    print("Simulator finished.")