import os
import psycopg2
from config import DATABASE_URL
from psycopg2.extras import RealDictCursor

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

        cur.execute("DROP TABLE IF EXISTS meal_logs CASCADE;")
        cur.execute("DROP TABLE IF EXISTS insulin_doses CASCADE;")
        cur.execute("DROP TABLE IF EXISTS glucose_readings CASCADE;")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        print("Dropped existing tables.")

        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL, 
                password_hash VARCHAR(256) NOT NULL,
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

        cur.execute("""
            CREATE TABLE glucose_readings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                glucose_value REAL NOT NULL
            );
        """)
        print("Created 'glucose_readings' table.")

        cur.execute("""
            CREATE TABLE insulin_doses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                dose_amount REAL NOT NULL,
                dose_type VARCHAR(50)
            );
        """)
        print("Created 'insulin_doses' table.")

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

        conn.commit()
        print("Database initialized successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

def find_user_by_username(username: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_recent_glucose_readings(user_id: int, limit: int = 100):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT glucose_value FROM glucose_readings WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s;", (user_id,))
    readings = cur.fetchall()
    cur.close()
    conn.close()
    if not readings: return []
    return [r['glucose_value'] for r in reversed(readings)]

def get_dashboard_data_for_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT timestamp, glucose_value FROM glucose_readings WHERE user_id = %s AND timestamp > NOW() - INTERVAL '24 hours' ORDER BY timestamp ASC;", (user_id,))
    glucose = cur.fetchall()
    cur.execute("SELECT timestamp, dose_amount, dose_type FROM insulin_doses WHERE user_id = %s AND timestamp > NOW() - INTERVAL '24 hours' ORDER BY timestamp ASC;", (user_id,))
    insulin = cur.fetchall()
    cur.execute("SELECT timestamp, meal_description, carb_count FROM meal_logs WHERE user_id = %s AND timestamp > NOW() - INTERVAL '24 hours' ORDER BY timestamp ASC;", (user_id,))
    meals = cur.fetchall()
    cur.close()
    conn.close()
    return {"glucose_readings": glucose, "insulin_doses": insulin, "meal_logs": meals}

if __name__ == '__main__':
    print("Initializing database...")
    init_db()