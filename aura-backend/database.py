import os
import psycopg2
from config import DATABASE_URL
from psycopg2.extras import RealDictCursor # We will need this later for the login

def get_db_connection():
    """Establishes a connection to the database."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Initializes the database by creating all necessary tables."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Drop tables if they exist for a clean slate during development
        cur.execute("DROP TABLE IF EXISTS meal_logs CASCADE;")
        cur.execute("DROP TABLE IF EXISTS insulin_doses CASCADE;")
        cur.execute("DROP TABLE IF EXISTS glucose_readings CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        print("Dropped existing tables.")

        # --- THIS IS THE UPGRADED USERS TABLE ---
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                
                -- Login Credentials (we can rename 'username' to 'email' later if needed)
                username VARCHAR(80) UNIQUE NOT NULL, 
                password_hash VARCHAR(256) NOT NULL,
                
                -- New Profile Information from the form
                name VARCHAR(100) NOT NULL,
                age INTEGER,
                gender VARCHAR(50),
                phone_number VARCHAR(20),
                weight_kg REAL,
                height_cm REAL,

                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Created UPGRADED 'users' table.")

        # --- OTHER TABLES ARE THE SAME ---
        # Create glucose_readings table
        cur.execute("""
            CREATE TABLE glucose_readings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                glucose_value REAL NOT NULL
            );
        """)
        print("Created 'glucose_readings' table.")

        # Create insulin_doses table
        cur.execute("""
            CREATE TABLE insulin_doses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                dose_amount REAL NOT NULL,
                dose_type VARCHAR(50) -- e.g., 'bolus', 'basal'
            );
        """)
        print("Created 'insulin_doses' table.")

        # Create meal_logs table
        cur.execute("""
            CREATE TABLE meal_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                meal_description TEXT,
                carb_count REAL
            );
        """)
        print("Created 'meal_logs' table.")

        # Commit the changes
        conn.commit()
        print("Database initialized successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# We still need the user lookup function for login
def find_user_by_username(username: str):
    """Finds a user in the database by their username."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor) # RealDictCursor is great for this
    cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# In database.py, add these two new functions at the bottom

def get_recent_glucose_readings(user_id: int, limit: int = 12) -> list:
    """
    Fetches the most recent glucose readings for a user.
    This is CRITICAL for the AI model.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT glucose_value FROM glucose_readings
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT %s;
        """,
        (user_id, limit)
    )
    readings = cur.fetchall()
    cur.close()
    conn.close()
    
    # The AI model needs a simple list of numbers, e.g., [120, 125, 130]
    # The query returns a list of dictionaries, e.g., [{'glucose_value': 120}, ...]
    # So we extract just the values.
    # We also reverse the list because the query gets them newest-first, but the model needs them oldest-first.
    return [reading['glucose_value'] for reading in reversed(readings)]


def get_dashboard_data_for_user(user_id: int) -> dict:
    """
    Fetches all necessary data for the user's dashboard.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Fetch user profile info
    cur.execute("SELECT name, age, weight_kg, height_cm FROM users WHERE id = %s;", (user_id,))
    user_profile = cur.fetchone()
    
    # Fetch last 24 hours of glucose readings
    cur.execute(
        """
        SELECT timestamp, glucose_value FROM glucose_readings
        WHERE user_id = %s AND timestamp >= NOW() - INTERVAL '24 hours'
        ORDER BY timestamp ASC;
        """,
        (user_id,)
    )