"""
Session management module for the IOT Product Support Chatbot

This module handles:
- User session creation and management
- Chat history tracking and retrieval
- Session state management
- Integration with database for persistence
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Local imports
from config.settings import SESSION_TIMEOUT, FEEDBACK_INTERVAL
from config.database import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages user sessions and chat history for the IOT chatbot
    
    This class handles:
    - Session creation and validation
    - Chat history management
    - Session state tracking
    - Database integration for persistence
    """
    
    def __init__(self):
        """Initialize the session manager"""
        self.active_sessions = {}  # In-memory session storage
        self.session_counters = {}  # Track question count for feedback
        self.feedback_shown = {}  # Track if feedback has been shown for each session
        
        # Initialize database connection
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            if db_manager.connect():
                db_manager.create_tables()
                logger.info("Database initialized successfully")
            else:
                logger.error("Failed to connect to database")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def create_session(self, email: str, phone: str, language: str = "English") -> str:
        """
        Create a new chat session for a user
        
        Args:
            email (str): User's email address
            phone (str): User's phone number
            language (str): Session language (English/Malay)
            
        Returns:
            str: Unique session ID
        """
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Get or create user ID
            user_id = db_manager.get_user_id(email, phone)
            if not user_id:
                logger.error(f"Failed to get user ID for {email}")
                return None
            
            # Create session in database
            if db_manager.create_session(user_id, session_id, language):
                # Store session in memory
                self.active_sessions[session_id] = {
                    "email": email,
                    "phone": phone,
                    "language": language,
                    "created_at": datetime.now(),
                    "last_activity": datetime.now(),
                    "question_count": 0,
                    "product_involved": None,
                    "expert_contacted": False
                }
                
                # Initialize question counter and feedback flag
                self.session_counters[session_id] = 0
                self.feedback_shown[session_id] = False
                
                logger.info(f"Created session {session_id} for user {email}")
                return session_id
            else:
                logger.error(f"Failed to create session for user {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about a session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Optional[Dict]: Session information or None
        """
        try:
            if session_id in self.active_sessions:
                session_info = self.active_sessions[session_id].copy()
                session_info["question_count"] = self.session_counters.get(session_id, 0)
                return session_info
            else:
                logger.warning(f"Session {session_id} not found in active sessions")
                return None
                
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    def update_session_activity(self, session_id: str):
        """
        Update session's last activity timestamp
        
        Args:
            session_id (str): Session identifier
        """
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["last_activity"] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    def increment_question_count(self, session_id: str) -> int:
        """
        Increment question count for a session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            int: Current question count
        """
        try:
            current_count = self.session_counters.get(session_id, 0)
            new_count = current_count + 1
            self.session_counters[session_id] = new_count
            
            # Update session info
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["question_count"] = new_count
            
            logger.info(f"Question count for session {session_id}: {new_count}")
            return new_count
            
        except Exception as e:
            logger.error(f"Error incrementing question count: {e}")
            return 0
    
    def should_show_feedback(self, session_id: str) -> bool:
        """
        Check if session should end after 3 questions (shows expert contact and ends session)
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            bool: True if session should end (after 3 questions)
        """
        try:
            question_count = self.session_counters.get(session_id, 0)
            feedback_already_shown = self.feedback_shown.get(session_id, False)
            
            # End session after 3 questions, but only once
            should_end = question_count >= FEEDBACK_INTERVAL and not feedback_already_shown
            
            if should_end:
                logger.info(f"Session should end for session {session_id} (question count: {question_count})")
                # Mark feedback as shown to prevent repeated triggers
                self.feedback_shown[session_id] = True
            
            return should_end
            
        except Exception as e:
            logger.error(f"Error checking session end condition: {e}")
            return False
    
    def should_end_session(self, session_id: str) -> bool:
        """
        Check if session should end after 3 questions
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            bool: True if session should end
        """
        return self.should_show_feedback(session_id)  # Same logic for now
    
    def force_end_session(self, session_id: str):
        """
        Force end a session immediately
        
        Args:
            session_id (str): Session identifier
        """
        try:
            logger.info(f"Force ending session {session_id}")
            self.end_session(session_id)
            return True
        except Exception as e:
            logger.error(f"Error force ending session {session_id}: {e}")
            return False
    
    def add_message_to_history(self, session_id: str, message_type: str, content: str) -> bool:
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
            # Add to database
            success = db_manager.add_message(session_id, message_type, content)
            
            if success:
                # Update session activity
                self.update_session_activity(session_id)
                
                # Increment question count for user messages
                if message_type == "user":
                    self.increment_question_count(session_id)
                
                logger.info(f"Added {message_type} message to session {session_id}")
                return True
            else:
                logger.error(f"Failed to add message to database for session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding message to history: {e}")
            return False
    
    def get_session_history(self, session_id: str) -> List[tuple]:
        """
        Get chat history for a session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            List[tuple]: List of (message_type, content) tuples
        """
        try:
            history = db_manager.get_session_history(session_id)
            logger.info(f"Retrieved {len(history)} messages for session {session_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []
    
    def update_session_product(self, session_id: str, product_name: str):
        """
        Update the product involved in the session
        
        Args:
            session_id (str): Session identifier
            product_name (str): Name of the IOT product
        """
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["product_involved"] = product_name
                
                # Update in database
                # Note: This would require adding a method to update session product
                logger.info(f"Updated session {session_id} with product: {product_name}")
                
        except Exception as e:
            logger.error(f"Error updating session product: {e}")
    
    def mark_expert_contacted(self, session_id: str):
        """
        Mark that expert has been contacted for this session
        
        Args:
            session_id (str): Session identifier
        """
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["expert_contacted"] = True
                logger.info(f"Marked expert contacted for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error marking expert contacted: {e}")
    
    def is_session_active(self, session_id: str) -> bool:
        """
        Check if a session is still active
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            bool: True if session is active, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session_info = self.active_sessions[session_id]
            last_activity = session_info["last_activity"]
            
            # Check if session has timed out
            timeout_threshold = datetime.now() - timedelta(seconds=SESSION_TIMEOUT)
            
            if last_activity < timeout_threshold:
                logger.info(f"Session {session_id} has timed out")
                self.end_session(session_id)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking session activity: {e}")
            return False
    
    def end_session(self, session_id: str):
        """
        End a session and clean up resources
        
        Args:
            session_id (str): Session identifier
        """
        try:
            if session_id in self.active_sessions:
                # Remove from memory
                del self.active_sessions[session_id]
                
                # Remove question counter
                if session_id in self.session_counters:
                    del self.session_counters[session_id]
                
                # Remove feedback flag
                if session_id in self.feedback_shown:
                    del self.feedback_shown[session_id]
                
                logger.info(f"Ended session {session_id}")
                
        except Exception as e:
            logger.error(f"Error ending session: {e}")
    
    def reset_feedback_flag(self, session_id: str):
        """
        Reset feedback flag for testing purposes
        
        Args:
            session_id (str): Session identifier
        """
        try:
            if session_id in self.feedback_shown:
                self.feedback_shown[session_id] = False
                logger.info(f"Reset feedback flag for session {session_id}")
            else:
                logger.warning(f"Session {session_id} not found in feedback tracking")
                
        except Exception as e:
            logger.error(f"Error resetting feedback flag: {e}")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_info in self.active_sessions.items():
                last_activity = session_info["last_activity"]
                timeout_threshold = current_time - timedelta(seconds=SESSION_TIMEOUT)
                
                if last_activity < timeout_threshold:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.end_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about active sessions
        
        Returns:
            Dict[str, Any]: Session statistics
        """
        try:
            total_sessions = len(self.active_sessions)
            total_questions = sum(self.session_counters.values())
            
            # Calculate average questions per session
            avg_questions = total_questions / total_sessions if total_sessions > 0 else 0
            
            return {
                "active_sessions": total_sessions,
                "total_questions": total_questions,
                "average_questions_per_session": round(avg_questions, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {}

# Global session manager instance
session_manager = SessionManager() 