"""
Main entry point for the IOT Product Support Chatbot

This application provides:
- User registration with email and phone number
- Language selection (English/Malay)
- Intelligent IOT product support chat
- Feedback collection and expert contact
- Session management and chat history

To run the application:
    streamlit run main.py
"""

from src.app import main

if __name__ == "__main__":
    main() 