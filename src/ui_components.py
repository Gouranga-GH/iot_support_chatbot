"""
UI Components module for the IOT Product Support Chatbot

This module handles:
- User registration and authentication
- Language selection interface
- Chat interface and message display
- Feedback modal components
- Expert contact display
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Local imports
from config.settings import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from src.session_manager import session_manager
from src.feedback_manager import feedback_manager
from src.product_router import product_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UIComponents:
    """
    Handles all Streamlit UI components for the IOT chatbot
    
    This class manages:
    - User registration forms
    - Language selection
    - Chat interface
    - Feedback modals
    - Expert contact display
    """
    
    def __init__(self):
        """Initialize UI components"""
        self.setup_page_config()
    
    def setup_page_config(self):
        """Set up Streamlit page configuration"""
        st.set_page_config(
            page_title="IOT Product Support Chatbot",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def display_header(self):
        """Display the main header"""
        st.title("🤖 IOT Product Support Chatbot")
        st.markdown("""
        Welcome to our IOT Product Support System! 
        
        Get instant help with your IOT devices through our AI-powered assistant.
        """)
    
    def display_user_registration(self) -> Optional[Dict]:
        """
        Display user registration form
        
        Returns:
            Optional[Dict]: User registration data or None
        """
        st.header("📝 User Registration")
        st.markdown("Please provide your contact information to start chatting.")
        
        with st.form("user_registration"):
            email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
            phone = st.text_input("📞 Phone Number", placeholder="+1-555-0123")
            
            # Language selection
            language = st.selectbox(
                "🌐 Language Preference",
                options=SUPPORTED_LANGUAGES,
                index=SUPPORTED_LANGUAGES.index(DEFAULT_LANGUAGE)
            )
            
            submit_button = st.form_submit_button("🚀 Start Chat")
            
            if submit_button:
                if self._validate_registration(email, phone):
                    return {
                        "email": email.strip(),
                        "phone": phone.strip(),
                        "language": language
                    }
                else:
                    st.error("Please provide valid email and phone number.")
        
        return None
    
    def _validate_registration(self, email: str, phone: str) -> bool:
        """
        Validate user registration data
        
        Args:
            email (str): User's email
            phone (str): User's phone number
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not email or not phone:
            return False
        
        # Basic email validation
        if "@" not in email or "." not in email:
            return False
        
        # Basic phone validation (at least 10 digits)
        digits_only = ''.join(filter(str.isdigit, phone))
        if len(digits_only) < 10:
            return False
        
        return True
    
    def display_language_selection(self, language: str) -> str:
        """
        Display language selection interface
        
        Args:
            language (str): Current language
            
        Returns:
            str: Selected language
        """
        st.header("🌐 Language Selection")
        st.markdown(product_router.get_language_selection_prompt())
        
        selected_language = st.selectbox(
            "Choose your preferred language:",
            options=SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(language)
        )
        
        return selected_language
    
    def display_chat_interface(self, session_id: str):
        """
        Display the main chat interface
        
        Args:
            session_id (str): Session identifier
        """
        st.header("💬 Chat with IOT Support")
        
        # Initialize chat history in session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Check if session should end
        should_end = session_manager.should_end_session(session_id)
        
        # Set session end flag in session state
        if should_end:
            st.session_state.session_should_end = True
            logger.info(f"Session {session_id} should end - setting end flag")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # If session should end, show session end modal and disable chat input
        if st.session_state.get("session_should_end", False):
            logger.info(f"Session {session_id} should end - displaying end modal")
            self.display_session_end_modal(session_id)
            # Disable chat input by not showing it
            st.info("Session has ended. Please provide feedback above to start a new session.")
            return
        
        # Additional check: if session is not active, don't allow chat
        if not session_manager.is_session_active(session_id):
            st.warning("Session has expired or ended. Please start a new session.")
            return
        
        # Chat input (only show if session is active)
        if prompt := st.chat_input("Ask about our IOT products..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process the message
            self._process_user_message(prompt, session_id)
    
    def _process_user_message(self, user_input: str, session_id: str):
        """
        Process user message using smart LLM-based approach
        
        Args:
            user_input (str): User's message
            session_id (str): Session identifier
        """
        try:
            # Check if session should end - if so, don't process new messages
            if st.session_state.get("session_should_end", False):
                logger.info(f"Session {session_id} should end - ignoring new message")
                return
            
            # Add user message to session history
            session_manager.add_message_to_history(session_id, "user", user_input)
            
            # Check for exit command
            if user_input.lower().strip() in ["exit", "quit", "bye", "goodbye"]:
                response = "Thank you for using our IOT Product Support Chatbot! Goodbye! 👋"
                self._add_assistant_message(response, session_id)
                return
            
            # Check for language selection
            if any(lang in user_input.lower() for lang in ["english", "malay", "language"]):
                response = "Language preference updated. How can I help you with our IOT products?"
                self._add_assistant_message(response, session_id)
                return
            
            # Use smart LLM-based response
            try:
                from src.rag_chain import rag_chain
                if rag_chain:
                    # Get session language
                    session_info = session_manager.get_session_info(session_id)
                    session_language = session_info.get('language', 'English') if session_info else 'English'
                    
                    # Get intelligent response from LLM with language control
                    rag_response = rag_chain.get_response(user_input, session_id, session_language)
                    response = rag_response.get("response", "I'm here to help with our IOT products. How can I assist you?")
                else:
                    # Fallback response
                    response = "I'm here to help with our IOT products. You can ask me about any of our 4 products: Smart Home Hub, Security Camera System, Smart Thermostat, and Smart Lighting System."
            except Exception as e:
                logger.error(f"Error getting RAG response: {e}")
                response = "I'm here to help with our IOT products. How can I assist you?"
            
            self._add_assistant_message(response, session_id)
                
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            response = "I apologize, but I'm having trouble processing your request. Please try again."
            self._add_assistant_message(response, session_id)
    
    def _add_assistant_message(self, response: str, session_id: str):
        """
        Add assistant message to chat
        
        Args:
            response (str): Assistant's response
            session_id (str): Session identifier
        """
        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Add to session history
        session_manager.add_message_to_history(session_id, "assistant", response)
    
    def display_session_end_modal(self, session_id: str):
        """
        Display session end modal with expert contact details
        
        Args:
            session_id (str): Session identifier
        """
        # Create a prominent session end section with container
        with st.container():
            st.markdown("---")
            st.markdown("## 🎉 Session Complete!")
            
            # Get session info for context
            session_info = session_manager.get_session_info(session_id)
            if session_info:
                st.markdown(f"**Questions Asked:** {session_info.get('question_count', 0)}")
                if session_info.get('product_involved'):
                    st.markdown(f"**Product Discussed:** {session_info['product_involved']}")
            
            # Get session language for appropriate messaging
            session_language = session_info.get('language', 'English') if session_info else 'English'
            
            if session_language == "Malay":
                st.markdown("### Terima kasih kerana menggunakan Chatbot Sokongan Produk IOT kami!")
                st.markdown("Kami berharap kami dapat membantu anda dengan soalan anda. Berikut adalah maklumat hubungan pakar kami untuk bantuan lanjut:")
            else:
                st.markdown("### Thank you for using our IOT Product Support Chatbot!")
                st.markdown("We hope we were able to help you with your questions. Here's our expert contact information for further assistance:")
            
            # Get expert contact information
            product_name = session_info.get('product_involved') if session_info else None
            expert_info = feedback_manager.get_expert_contact(product_name)
            
            if expert_info:
                st.markdown("### 👨‍💼 Expert Contact Information")
                st.markdown(feedback_manager.format_expert_contact(expert_info))
            else:
                st.warning("Expert contact information not available.")
            
            # Add a brief feedback section
            st.markdown("---")
            if session_language == "Malay":
                st.markdown("### 📝 Maklum Balas Pantas")
                st.markdown("Bagaimana kepuasan anda dengan sokongan kami?")
            else:
                st.markdown("### 📝 Quick Feedback")
                st.markdown("How satisfied were you with our support?")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Satisfied", use_container_width=True, type="primary", key="satisfied_feedback"):
                    self._handle_session_end_feedback(session_id, "satisfied")
            with col2:
                if st.button("❌ Not Satisfied", use_container_width=True, key="unsatisfied_feedback"):
                    self._handle_session_end_feedback(session_id, "unsatisfied")
            with col3:
                if st.button("⏭️ Skip Feedback", use_container_width=True, key="skip_feedback"):
                    self._handle_session_end_feedback(session_id, "skipped")
    
    def display_feedback_modal(self, session_id: str):
        """
        Display feedback modal (legacy method - kept for compatibility)
        
        Args:
            session_id (str): Session identifier
        """
        # Create a prominent feedback section
        st.markdown("---")
        st.markdown("## 📝 Session Feedback")
        
        # Get session info for context
        session_info = session_manager.get_session_info(session_id)
        if session_info:
            st.markdown(f"**Questions Asked:** {session_info.get('question_count', 0)}")
            if session_info.get('product_involved'):
                st.markdown(f"**Product Discussed:** {session_info['product_involved']}")
        
        st.markdown("### How satisfied are you with our support?")
        st.markdown("Your feedback helps us improve our service!")
        
        # Create feedback options with better styling
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Satisfied", use_container_width=True, type="primary"):
                self._handle_feedback_response(session_id, "satisfied")
        
        with col2:
            if st.button("❌ Not Satisfied", use_container_width=True):
                self._handle_feedback_response(session_id, "unsatisfied")
    
    def _handle_feedback_response(self, session_id: str, satisfaction_rating: str):
        """
        Handle user feedback response
        
        Args:
            session_id (str): Session identifier
            satisfaction_rating (str): User's satisfaction rating
        """
        try:
            # Process feedback
            result = feedback_manager.process_feedback_response(session_id, satisfaction_rating)
            
            if result["success"]:
                # Display feedback template
                template = result["template"]
                st.success(f"{template['icon']} {template['title']}")
                st.info(template['message'])
                
                # Show expert contact if needed
                if result["show_expert_contact"]:
                    st.markdown("### 👨‍💼 Expert Contact")
                    st.markdown(result["expert_contact"])
                
                # Add a final message and end session
                st.markdown("---")
                st.markdown("## 🎉 Session Completed!")
                st.markdown("### Thank you for using our IOT Product Support Chatbot!")
                st.markdown("Your session has been completed successfully. We hope we were able to help you with your IOT product questions.")
                
                # End the session
                session_manager.end_session(session_id)
                
                # Clear session state to force re-registration
                if "user_registered" in st.session_state:
                    del st.session_state.user_registered
                if "session_id" in st.session_state:
                    del st.session_state.session_id
                if "user_data" in st.session_state:
                    del st.session_state.user_data
                if "messages" in st.session_state:
                    del st.session_state.messages
                
                # Add a button to start new session
                st.markdown("---")
                st.markdown("### Ready for another session?")
                if st.button("🔄 Start New Session", use_container_width=True, type="primary"):
                    st.rerun()
                
            else:
                st.error("Failed to save feedback. Please try again.")
                
        except Exception as e:
            logger.error(f"Error handling feedback response: {e}")
            st.error("An error occurred while processing your feedback.")
    
    def _handle_session_end_feedback(self, session_id: str, satisfaction_rating: str):
        """
        Handle feedback at session end and start new session
        
        Args:
            session_id (str): Session identifier
            satisfaction_rating (str): User's satisfaction rating
        """
        try:
            # Process feedback
            result = feedback_manager.process_feedback_response(session_id, satisfaction_rating)
            
            if result["success"]:
                # Display feedback confirmation
                template = result["template"]
                st.success(f"{template['icon']} {template['title']}")
                st.info(template['message'])
                
                # Force end the session
                session_manager.force_end_session(session_id)
                
                # Clear session state to force re-registration
                if "user_registered" in st.session_state:
                    del st.session_state.user_registered
                if "session_id" in st.session_state:
                    del st.session_state.session_id
                if "user_data" in st.session_state:
                    del st.session_state.user_data
                if "messages" in st.session_state:
                    del st.session_state.messages

                if "session_should_end" in st.session_state:
                    del st.session_state.session_should_end
                
                # Show new session prompt
                st.markdown("---")
                st.markdown("## 🔄 Starting New Session")
                st.markdown("### Ready to start a new chat session?")
                st.markdown("Please register again to begin a new session.")
                
                # Auto-rerun to show registration form
                st.rerun()
                
            else:
                st.error("Failed to save feedback. Please try again.")
                
        except Exception as e:
            logger.error(f"Error handling session end feedback: {e}")
            st.error("An error occurred while processing your feedback.")
    
    def display_chat_history_sidebar(self, session_id: str):
        """
        Display chat history in sidebar
        
        Args:
            session_id (str): Session identifier
        """
        with st.sidebar:
            st.header("📚 Chat History")
            
            # Get session history
            history = session_manager.get_session_history(session_id)
            
            if history:
                for message_type, content in history[-10:]:  # Show last 10 messages
                    if message_type == "user":
                        st.markdown(f"**You:** {content[:50]}...")
                    else:
                        st.markdown(f"**Assistant:** {content[:50]}...")
            else:
                st.info("No chat history yet.")
    
    def display_session_info_sidebar(self, session_id: str):
        """
        Display session information in sidebar
        
        Args:
            session_id (str): Session identifier
        """
        with st.sidebar:
            st.header("ℹ️ Session Info")
            
            session_info = session_manager.get_session_info(session_id)
            if session_info:
                st.markdown(f"""
                **Email:** {session_info['email']}
                **Language:** {session_info['language']}
                **Questions:** {session_info['question_count']}
                """)
    
    def display_expert_contact_modal(self, expert_info: Dict):
        """
        Display expert contact information in a modal
        
        Args:
            expert_info (Dict): Expert contact information
        """
        st.markdown("### 👨‍💼 Expert Contact")
        st.markdown(feedback_manager.format_expert_contact(expert_info))
    
    def display_all_experts(self):
        """
        Display all available experts (product-specific and overall)
        """
        st.markdown("### 👥 All Available Experts")
        
        # Get all experts
        all_experts = feedback_manager.get_all_experts()
        
        if all_experts:
            # Display product-specific experts
            st.markdown("#### 🎯 Product-Specific Experts")
            for expert in all_experts:
                if expert.get("type") == "product_specific":
                    st.markdown(f"""
                    **{expert['product']} Expert:**
                    - **Name:** {expert['name']}
                    - **Email:** {expert['email']}
                    - **Phone:** {expert['phone']}
                    """)
            
            # Display overall experts
            st.markdown("#### 🌟 Overall IOT Experts")
            for expert in all_experts:
                if expert.get("type") == "overall":
                    st.markdown(f"""
                    **{expert['title']}:**
                    - **Name:** {expert['name']}
                    - **Email:** {expert['email']}
                    - **Phone:** {expert['phone']}
                    - **Specialties:** {', '.join(expert['specialties'])}
                    """)
        else:
            st.info("No experts available at the moment.")
    
    def display_error_message(self, message: str):
        """
        Display error message
        
        Args:
            message (str): Error message
        """
        st.error(f"❌ {message}")
    
    def display_success_message(self, message: str):
        """
        Display success message
        
        Args:
            message (str): Success message
        """
        st.success(f"✅ {message}")
    
    def display_warning_message(self, message: str):
        """
        Display warning message
        
        Args:
            message (str): Warning message
        """
        st.warning(f"⚠️ {message}")
    
    def display_info_message(self, message: str):
        """
        Display info message
        
        Args:
            message (str): Info message
        """
        st.info(f"ℹ️ {message}")
    
    def display_loading_spinner(self, message: str = "Processing..."):
        """
        Display loading spinner
        
        Args:
            message (str): Loading message
        """
        with st.spinner(message):
            pass
    
    def display_footer(self):
        """Display application footer"""
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: gray;'>
        <p>IOT Product Support Chatbot | Powered by AI 🤖</p>
        </div>
        """, unsafe_allow_html=True)

# Global UI components instance
ui_components = UIComponents() 