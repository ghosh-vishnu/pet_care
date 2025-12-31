# setup_database.py - Database Setup Script

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from database import Base, engine
from models.database_models import *

def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="root",
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'dog_health_ai'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute('CREATE DATABASE dog_health_ai')
            print("[SUCCESS] Database 'dog_health_ai' created successfully!")
        else:
            print("[INFO] Database 'dog_health_ai' already exists!")
        
        cur.close()
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Error connecting to PostgreSQL: {e}")
        print("Please check:")
        print("  1. PostgreSQL is running")
        print("  2. Password is correct (currently set to 'root')")
        print("  3. PostgreSQL is accessible on localhost:5432")
        return False

def create_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("[SUCCESS] Database tables created successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        return False

if __name__ == "__main__":
    print("Setting up database...")
    print("-" * 50)
    
    if create_database():
        print("-" * 50)
        create_tables()
        print("-" * 50)
        print("[SUCCESS] Database setup complete!")
    else:
        print("[ERROR] Database setup failed!")

