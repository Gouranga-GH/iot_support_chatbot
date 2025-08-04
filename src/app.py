"""
Main application module for the IOT Product Support Chatbot

This module orchestrates all components and manages the application flow:
- User registration and session management
- Document processing and RAG pipeline
- Chat interface and feedback handling
- Database integration and error handling
"""

import streamlit as st
import logging
from typing import Dict, Optional, Any

# Local imports
from config.settings import validate_config, GROQ_API_KEY
from config.database import db_manager
from src.document_processor import document_processor
from src.rag_chain import RAGChain
from src.session_manager import session_manager
from src.feedback_manager import feedback_manager
from src.product_router import product_router
from src.ui_components import ui_components

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                st.error("Configuration validation failed. Please check your .env file.")
                st.stop()
            
            # Initialize database connection
            if not db_manager.connect():
                st.error("Failed to connect to database. Please check your MySQL configuration.")
                st.stop()
            
            # Create database tables
            if not db_manager.create_tables():
                st.error("Failed to create database tables.")
                st.stop()
            
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
                    from src.rag_chain import initialize_rag_chain
                    self.rag_chain = initialize_rag_chain(GROQ_API_KEY)
                    if self.rag_chain:
                        logger.info("Smart RAG chain initialized successfully")
                    else:
                        st.warning("RAG chain not available. Some features may be limited.")
                except Exception as e:
                    logger.error(f"Failed to initialize RAG chain: {e}")
                    st.warning("RAG chain not available. Some features may be limited.")
            else:
                st.warning("ChatGroq API key not found. Please add it to your .env file.")
            
            logger.info("Application initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing application: {e}")
            st.error("Failed to initialize application. Please check the logs.")
            st.stop()
    
    def run(self):
        """Main application loop"""
        try:
            # Display header
            ui_components.display_header()
            
            # Check if user is already registered
            if "user_registered" not in st.session_state:
                st.session_state.user_registered = False
            
            if not st.session_state.user_registered:
                self._handle_user_registration()
            else:
                self._handle_chat_session()
            
            # Display footer
            ui_components.display_footer()
            
        except Exception as e:
            logger.error(f"Error in main application loop: {e}")
            st.error("An error occurred. Please refresh the page.")
    
    def _handle_user_registration(self):
        """Handle user registration process"""
        try:
            # Display user registration form
            registration_data = ui_components.display_user_registration()
            
            if registration_data:
                # Create new session (treat all users as new)
                session_id = session_manager.create_session(
                    registration_data["email"],
                    registration_data["phone"],
                    registration_data["language"]
                )
                
                if session_id:
                    # Store session data
                    st.session_state.user_registered = True
                    st.session_state.session_id = session_id
                    st.session_state.user_data = registration_data
                    
                    # Rerun to show chat interface
                    st.rerun()
                else:
                    st.error("Failed to create session. Please try again.")
            
        except Exception as e:
            logger.error(f"Error in user registration: {e}")
            st.error("Registration failed. Please try again.")
    
    def _handle_chat_session(self):
        """Handle the main chat session"""
        try:
            # Get session data
            session_id = st.session_state.get("session_id")
            user_data = st.session_state.get("user_data")
            
            if not session_id or not user_data:
                st.error("Session data not found. Please register again.")
                st.session_state.user_registered = False
                st.rerun()
                return
            
            # Check if session is still active
            if not session_manager.is_session_active(session_id):
                st.warning("Session expired. Please register again.")
                st.session_state.user_registered = False
                st.rerun()
                return
            
            # Display session info in sidebar
            ui_components.display_session_info_sidebar(session_id)
            
            # Display chat history in sidebar
            ui_components.display_chat_history_sidebar(session_id)
            
            # Display chat interface
            ui_components.display_chat_interface(session_id)
            
        except Exception as e:
            logger.error(f"Error in chat session: {e}")
            st.error("Chat session error. Please refresh the page.")
    
    def process_documents(self):
        """Process IOT product documents and create vector databases"""
        try:
            st.header("📚 Document Processing")
            st.markdown("Process IOT product PDFs to create searchable vector databases.")
            
            if st.button("🔄 Process Documents"):
                with st.spinner("Processing documents..."):
                    # Process product documents
                    product_vectorstores = document_processor.process_product_documents()
                    
                    if product_vectorstores:
                        # Create combined vector database
                        combined_vectorstore = document_processor.create_combined_vectorstore()
                        
                        st.success(f"✅ Processed {len(product_vectorstores)} product documents")
                        st.info("Vector databases created successfully!")
                        
                        # Display processing results
                        for product_name, vectorstore in product_vectorstores.items():
                            st.markdown(f"• **{product_name}**: Vector database created")
                    else:
                        st.warning("No documents found. Please add IOT product PDFs to the data/iot_products/ directory.")
            
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            st.error("Document processing failed. Please check the logs.")
    
    def display_system_status(self):
        """Display system status and configuration"""
        try:
            st.header("🔧 System Status")
            
            # Database status
            db_status = "✅ Connected" if db_manager.connection else "❌ Disconnected"
            st.markdown(f"**Database:** {db_status}")
            
            # RAG chain status
            rag_status = "✅ Available" if self.rag_chain else "❌ Not Available"
            st.markdown(f"**RAG Chain:** {rag_status}")
            
            # Document processor status
            doc_status = "✅ Ready" if document_processor.embeddings else "❌ Not Ready"
            st.markdown(f"**Document Processor:** {doc_status}")
            
            # Session statistics
            stats = session_manager.get_session_statistics()
            st.markdown(f"**Active Sessions:** {stats.get('active_sessions', 0)}")
            st.markdown(f"**Total Questions:** {stats.get('total_questions', 0)}")
            
        except Exception as e:
            logger.error(f"Error displaying system status: {e}")
            st.error("Failed to display system status.")
    
    def cleanup_resources(self):
        """Clean up application resources"""
        try:
            # Clean up expired sessions
            session_manager.cleanup_expired_sessions()
            
            # Close database connection
            db_manager.close()
            
            logger.info("Application resources cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up resources: {e}")

# Global application instance
app = IOTChatbotApp()

def main():
    """Main entry point for the application"""
    try:
        # Run the application
        app.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("Application error. Please check the logs.")
    # Note: Removed cleanup_resources() from finally block to prevent premature database closure

if __name__ == "__main__":
    main() 