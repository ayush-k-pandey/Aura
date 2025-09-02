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

if __name__ == '__main__':
    print("Initializing database...")
    init_db()