"""
Database configuration and setup for the IOT Product Support Chatbot

This module handles MySQL database connection, schema creation,
and database operations for storing chat history and feedback.
"""

import mysql.connector
from mysql.connector import Error
import logging
from config.settings import MYSQL_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages MySQL database operations for the IOT chatbot
    
    This class handles:
    - Database connection and initialization
    - Table creation and schema management
    - Chat history storage and retrieval
    - Feedback data management
    """
    
    def __init__(self):
        """Initialize the database manager"""
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """
        Establish connection to MySQL database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection to MySQL server
            self.connection = mysql.connector.connect(
                host=MYSQL_CONFIG['host'],
                user=MYSQL_CONFIG['user'],
                password=MYSQL_CONFIG['password'],
                port=MYSQL_CONFIG['port']
            )
            
            self.cursor = self.connection.cursor()
            
            # Create database if it doesn't exist
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
            self.cursor.execute(f"USE {MYSQL_CONFIG['database']}")
            
            logger.info("Database connection established successfully")
            return True
            
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return False
    
    def create_tables(self):
        """
        Create necessary tables for the chatbot
        
        Creates:
        - users: Store user information (email, phone)
        - chat_sessions: Store chat session metadata
        - chat_messages: Store individual chat messages
        - feedback: Store user feedback and satisfaction ratings
        """
        try:
            # Users table
            users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                language_preference VARCHAR(10) DEFAULT 'English',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user (email, phone)
            )
            """
            
            # Chat sessions table
            sessions_table = """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                session_id VARCHAR(255) NOT NULL,
                product_involved VARCHAR(100),
                language VARCHAR(10) DEFAULT 'English',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE KEY unique_session (session_id)
            )
            """
            
            # Chat messages table
            messages_table = """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                message_type ENUM('user', 'assistant') NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            )
            """
            
            # Feedback table
            feedback_table = """
            CREATE TABLE IF NOT EXISTS feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                satisfaction_rating ENUM('satisfied', 'unsatisfied') NOT NULL,
                expert_contacted BOOLEAN DEFAULT FALSE,
                feedback_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            )
            """
            
            # Execute table creation
            tables = [users_table, sessions_table, messages_table, feedback_table]
            
            for table_sql in tables:
                self.cursor.execute(table_sql)
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            return True
            
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def get_user_id(self, email, phone):
        """
        Get or create user ID for given email and phone
        
        Args:
            email (str): User's email address
            phone (str): User's phone number
            
        Returns:
            int: User ID
        """
        try:
            # Ensure connection is active
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            # Check if user exists
            self.cursor.execute(
                "SELECT id FROM users WHERE email = %s AND phone = %s",
                (email, phone)
            )
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Create new user
                self.cursor.execute(
                    "INSERT INTO users (email, phone) VALUES (%s, %s)",
                    (email, phone)
                )
                self.connection.commit()
                return self.cursor.lastrowid
                
        except Error as e:
            logger.error(f"Error getting user ID: {e}")
            return None
    
    def create_session(self, user_id, session_id, language="English"):
        """
        Create a new chat session
        
        Args:
            user_id (int): User ID
            session_id (str): Unique session identifier
            language (str): Session language
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure connection is active
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(
                "INSERT INTO chat_sessions (user_id, session_id, language) VALUES (%s, %s, %s)",
                (user_id, session_id, language)
            )
            self.connection.commit()
            return True
            
        except Error as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    def add_message(self, session_id, message_type, content):
        """
        Add a message to the chat history
        
        Args:
            session_id (str): Session identifier
            message_type (str): 'user' or 'assistant'
            content (str): Message content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                "INSERT INTO chat_messages (session_id, message_type, content) VALUES (%s, %s, %s)",
                (session_id, message_type, content)
            )
            self.connection.commit()
            return True
            
        except Error as e:
            logger.error(f"Error adding message: {e}")
            return False
    
    def get_session_history(self, session_id):
        """
        Get chat history for a session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            list: List of (message_type, content) tuples
        """
        try:
            self.cursor.execute(
                "SELECT message_type, content FROM chat_messages WHERE session_id = %s ORDER BY timestamp",
                (session_id,)
            )
            return self.cursor.fetchall()
            
        except Error as e:
            logger.error(f"Error getting session history: {e}")
            return []
    
    def save_feedback(self, session_id, satisfaction_rating, expert_contacted=False):
        """
        Save user feedback
        
        Args:
            session_id (str): Session identifier
            satisfaction_rating (str): 'satisfied' or 'unsatisfied'
            expert_contacted (bool): Whether expert was contacted
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute("""
                INSERT INTO feedback (session_id, satisfaction_rating, expert_contacted)
                VALUES (%s, %s, %s)
            """, (session_id, satisfaction_rating, expert_contacted))
            
            self.connection.commit()
            return True
            
        except Error as e:
            logger.error(f"Error saving feedback: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager() 