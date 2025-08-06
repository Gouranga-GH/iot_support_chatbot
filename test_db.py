#!/usr/bin/env python3
"""
Database test script for IoT Support Chatbot

This script tests:
- Database connection
- Table creation
- User creation
- Session creation
- Message saving
- Feedback saving
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import db_manager
from config.settings import validate_config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection"""
    print("🔌 Testing database connection...")
    
    if not validate_config():
        print("❌ Configuration validation failed")
        return False
    
    if not db_manager.connect():
        print("❌ Failed to connect to database")
        return False
    
    print("✅ Database connection successful")
    return True

def test_table_creation():
    """Test table creation"""
    print("\n📋 Testing table creation...")
    
    if not db_manager.create_tables():
        print("❌ Failed to create tables")
        return False
    
    print("✅ Tables created successfully")
    return True

def test_user_creation():
    """Test user creation"""
    print("\n👤 Testing user creation...")
    
    email = "test@example.com"
    phone = "1234567890"
    
    user_id = db_manager.get_user_id(email, phone)
    if user_id:
        print(f"✅ User created/found with ID: {user_id}")
        return user_id
    else:
        print("❌ Failed to create/find user")
        return None

def test_session_creation(user_id):
    """Test session creation"""
    print("\n💬 Testing session creation...")
    
    session_id = "test_session_123"
    language = "English"
    
    if db_manager.create_session(user_id, session_id, language):
        print(f"✅ Session created: {session_id}")
        return session_id
    else:
        print("❌ Failed to create session")
        return None

def test_message_saving(session_id):
    """Test message saving"""
    print("\n💬 Testing message saving...")
    
    # Test user message
    if db_manager.add_message(session_id, "user", "Hello, how can you help me?"):
        print("✅ User message saved")
    else:
        print("❌ Failed to save user message")
        return False
    
    # Test assistant message
    if db_manager.add_message(session_id, "assistant", "Hello! I'm here to help with IoT products."):
        print("✅ Assistant message saved")
        return True
    else:
        print("❌ Failed to save assistant message")
        return False

def test_feedback_saving(session_id):
    """Test feedback saving"""
    print("\n📝 Testing feedback saving...")
    
    if db_manager.save_feedback(session_id, "satisfied", False):
        print("✅ Feedback saved successfully")
        return True
    else:
        print("❌ Failed to save feedback")
        return False

def test_session_history(session_id):
    """Test session history retrieval"""
    print("\n📚 Testing session history...")
    
    history = db_manager.get_session_history(session_id)
    if history:
        print(f"✅ Retrieved {len(history)} messages from session history")
        for msg_type, content in history:
            print(f"   {msg_type}: {content[:50]}...")
        return True
    else:
        print("❌ Failed to retrieve session history")
        return False

def main():
    """Run all database tests"""
    print("🧪 Starting Database Tests\n")
    
    # Test 1: Database connection
    if not test_database_connection():
        return
    
    # Test 2: Table creation
    if not test_table_creation():
        return
    
    # Test 3: User creation
    user_id = test_user_creation()
    if not user_id:
        return
    
    # Test 4: Session creation
    session_id = test_session_creation(user_id)
    if not session_id:
        return
    
    # Test 5: Message saving
    if not test_message_saving(session_id):
        return
    
    # Test 6: Session history
    if not test_session_history(session_id):
        return
    
    # Test 7: Feedback saving
    if not test_feedback_saving(session_id):
        return
    
    print("\n🎉 All database tests passed!")
    print("\n📊 Database is working correctly.")
    print("💡 You can now run the Flask app with confidence.")

if __name__ == "__main__":
    main() 