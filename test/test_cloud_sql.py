#!/usr/bin/env python3
"""
Test script to verify Google Cloud SQL connection
"""

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

def test_cloud_sql_connection():
    """Test connection to Google Cloud SQL"""
    
    print("🔍 Testing Google Cloud SQL Connection")
    print("=" * 50)
    
    # Try to load environment variables from different sources
    env_files = ['.env', 'local_test.env']
    env_loaded = False
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"📁 Loading environment from {env_file}")
            load_dotenv(env_file)
            env_loaded = True
            break
    
    if not env_loaded:
        print("⚠️  No .env file found. Using system environment variables.")
    
    # Get environment variables
    host = os.getenv('MYSQL_HOST')
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    database = os.getenv('MYSQL_DATABASE')
    port = int(os.getenv('MYSQL_PORT', 3306))
    
    print(f"Host: {host}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print(f"Port: {port}")
    
    if not all([host, user, password, database]):
        print("❌ Missing environment variables")
        print("💡 Please update your .env or local_test.env file with Cloud SQL details")
        return False
    
    try:
        # Test connection
        print("\n🔌 Attempting to connect...")
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        
        if connection.is_connected():
            print("✅ Connected to MySQL server successfully!")
            
            # Test database creation
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            print(f"✅ Database '{database}' ready")
            
            # Test table creation
            cursor.execute(f"USE {database}")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Test table created successfully")
            
            # Test insert
            cursor.execute("INSERT INTO test_table (message) VALUES (%s)", ("Test message",))
            connection.commit()
            print("✅ Test insert successful")
            
            # Test select
            cursor.execute("SELECT * FROM test_table")
            result = cursor.fetchone()
            print(f"✅ Test select successful: {result}")
            
            cursor.close()
            connection.close()
            print("✅ All tests passed! Cloud SQL is working correctly.")
            return True
            
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False

if __name__ == "__main__":
    success = test_cloud_sql_connection()
    if success:
        print("\n🎉 Cloud SQL setup is complete!")
        print("💡 You can now deploy your application.")
    else:
        print("\n❌ Cloud SQL setup failed.")
        print("💡 Please check your configuration.") 