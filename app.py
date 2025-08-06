"""
Flask application for the IOT Product Support Chatbot

This application provides:
- User registration with email and phone number
- Language selection (English/Malay)
- Intelligent IOT product support chat
- Feedback collection and expert contact
- Session management and chat history

To run the application:
    python app.py
"""

from flask import Flask, render_template, request, jsonify, session
import logging
import os
from typing import Dict, Optional, Any

# Local imports
from config.settings import validate_config, GROQ_API_KEY, FEEDBACK_INTERVAL
from config.database import db_manager
from src.document_processor import document_processor
from src.rag_chain import RAGChain, initialize_rag_chain
from src.session_manager import session_manager
from src.feedback_manager import feedback_manager
from src.product_router import product_router
from src.ui_components import ui_components

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

class IOTChatbotApp:
    """
    Main application class for the IOT Product Support Chatbot
    
    This class orchestrates:
    - Application initialization and configuration
    - User session management
    - Document processing and RAG pipeline
    - Chat interface and feedback handling
    """
    
    def __init__(self):
        """Initialize the IOT chatbot application"""
        self.rag_chain = None
        self.current_session_id = None
        self.user_registration_data = None
        
        # Initialize application
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize the application and validate configuration"""
        try:
            # Validate configuration
            if not validate_config():
                logger.error("Configuration validation failed. Please check your .env file.")
                return False
            
            # Initialize database connection
            if not db_manager.connect():
                logger.error("Failed to connect to database. Please check your MySQL configuration.")
                return False
            
            # Create database tables
            if not db_manager.create_tables():
                logger.error("Failed to create database tables.")
                return False
            
            # Initialize document processor
            try:
                # Try to load existing vector databases
                document_processor.load_existing_vectorstores()
                logger.info("Loaded existing vector databases")
            except Exception as e:
                logger.warning(f"Could not load existing vector databases: {e}")
                logger.info("You'll need to process IOT product documents first.")
            
            # Initialize RAG chain if API key is available
            if GROQ_API_KEY:
                try:
                    self.rag_chain = initialize_rag_chain(GROQ_API_KEY)
                    if self.rag_chain:
                        logger.info("Smart RAG chain initialized successfully")
                    else:
                        logger.warning("RAG chain not available. Some features may be limited.")
                except Exception as e:
                    logger.error(f"Failed to initialize RAG chain: {e}")
                    logger.warning("RAG chain not available. Some features may be limited.")
            else:
                logger.warning("ChatGroq API key not found. Please add it to your .env file.")
            
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing application: {e}")
            return False

# Global application instance
chatbot_app = IOTChatbotApp()

@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register_user():
    """Handle user registration"""
    try:
        data = request.get_json()
        email = data.get('email')
        phone = data.get('phone')
        language = data.get('language', 'English')
        
        if not email or not phone:
            return jsonify({'error': 'Email and phone are required'}), 400
        
        logger.info(f"Creating session for user: {email}")
        
        # Create new session
        session_id = session_manager.create_session(email, phone, language)
        
        if session_id:
            logger.info(f"Session created successfully: {session_id}")
            session['user_registered'] = True
            session['session_id'] = session_id
            session['user_data'] = {
                'email': email,
                'phone': phone,
                'language': language
            }
            return jsonify({'success': True, 'session_id': session_id})
        else:
            logger.error(f"Failed to create session for user: {email}")
            return jsonify({'error': 'Failed to create session'}), 500
            
    except Exception as e:
        logger.error(f"Error in user registration: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get('message')
        session_id = session.get('session_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        # Check if session is still active
        if not session_manager.is_session_active(session_id):
            return jsonify({'error': 'Session expired'}), 401
        
        # Get user language from session
        user_data = session.get('user_data', {})
        language = user_data.get('language', 'English')
        
        logger.info(f"Processing chat message for session {session_id}: {message[:50]}...")
        
        # Add user message to history and increment question count
        message_saved = session_manager.add_message_to_history(session_id, "user", message)
        if not message_saved:
            logger.warning(f"Failed to save user message to database for session {session_id}")
        
        # Check if session should end (after 3 questions)
        should_end = session_manager.should_show_feedback(session_id)
        
        # Process the message through RAG chain
        if chatbot_app.rag_chain:
            try:
                # Use the correct method from RAG chain
                response_data = chatbot_app.rag_chain.get_response(message, session_id, language)
                response = response_data.get('response', 'I apologize, but I encountered an error processing your request.')
            except Exception as e:
                logger.error(f"Error processing message with RAG chain: {e}")
                response = "I'm sorry, I encountered an error processing your request. Please try again."
        else:
            # Fallback response if RAG chain is not available
            response = "I'm sorry, the AI assistant is not available at the moment. Please try again later."
        
        # Add assistant response to history
        response_saved = session_manager.add_message_to_history(session_id, "assistant", response)
        if not response_saved:
            logger.warning(f"Failed to save assistant response to database for session {session_id}")
        
        # Prepare response data
        response_data = {
            'response': response,
            'should_end_session': should_end,
            'question_count': session_manager.session_counters.get(session_id, 0)
        }
        
        # If session should end, include feedback modal data
        if should_end:
            feedback_data = feedback_manager.create_feedback_modal_data(session_id)
            response_data['feedback_modal'] = feedback_data
            logger.info(f"Session {session_id} will end after this response")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({'error': 'Chat failed'}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback submission"""
    try:
        data = request.get_json()
        session_id = session.get('session_id')
        rating = data.get('rating')
        
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        if not rating:
            return jsonify({'error': 'Rating is required'}), 400
        
        logger.info(f"Processing feedback for session {session_id}: {rating}")
        
        # Process feedback using the proper feedback manager
        feedback_result = feedback_manager.process_feedback_response(session_id, rating)
        
        if feedback_result.get('success'):
            logger.info(f"Feedback saved successfully for session {session_id}")
            # End the session after feedback
            session_manager.end_session(session_id)
            session.clear()  # Clear Flask session
            
            return jsonify({
                'success': True,
                'template': feedback_result.get('template'),
                'expert_contact': feedback_result.get('expert_contact'),
                'show_expert_contact': feedback_result.get('show_expert_contact'),
                'product_name': feedback_result.get('product_name')
            })
        else:
            logger.error(f"Failed to save feedback for session {session_id}")
            return jsonify({'error': 'Failed to submit feedback'}), 500
            
    except Exception as e:
        logger.error(f"Error in feedback submission: {e}")
        return jsonify({'error': 'Feedback submission failed'}), 500

@app.route('/api/session-status', methods=['GET'])
def session_status():
    """Get current session status"""
    try:
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'No active session'}), 401
        
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'question_count': session_info.get('question_count', 0),
            'should_show_feedback': session_manager.should_show_feedback(session_id),
            'language': session_info.get('language', 'English'),
            'product_involved': session_info.get('product_involved')
        })
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': 'Failed to get session status'}), 500

@app.route('/api/status')
def status():
    """Return application status"""
    try:
        status_data = {
            'database': 'Connected' if db_manager.connection else 'Disconnected',
            'rag_chain': 'Available' if chatbot_app.rag_chain else 'Not Available',
            'document_processor': 'Ready' if document_processor.embeddings else 'Not Ready'
        }
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500

if __name__ == '__main__':
    if chatbot_app._initialize_app():
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        logger.error("Failed to initialize application") 