"""
Configuration settings for the IOT Product Support Chatbot

This file contains all the constants, settings, and configuration
parameters used throughout the application.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# LLM Model Settings
LLM_MODEL = "Gemma2-9b-It"  # ChatGroq model for fast inference
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # HuggingFace embedding model

# Text Processing Configuration
CHUNK_SIZE = 5000  # Size of text chunks for processing
CHUNK_OVERLAP = 500  # Overlap between chunks for context continuity

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# MySQL Database Settings
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))

MYSQL_CONFIG = {
    'host': MYSQL_HOST,
    'user': MYSQL_USER,
    'password': MYSQL_PASSWORD,
    'database': MYSQL_DATABASE,
    'port': MYSQL_PORT
}

# Debug: Print MySQL configuration (without password)
print(f"MySQL Configuration - Host: {MYSQL_HOST}, User: {MYSQL_USER}, Database: {MYSQL_DATABASE}, Port: {MYSQL_PORT}")

# =============================================================================
# API KEYS
# =============================================================================

# External API Keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# Language Support
SUPPORTED_LANGUAGES = ["English", "Malay"]
DEFAULT_LANGUAGE = "English"

# Feedback Settings
FEEDBACK_INTERVAL = int(os.getenv('FEEDBACK_INTERVAL', 3))  # Show feedback after N questions

# Session Settings
SESSION_TIMEOUT = 3600  # Session timeout in seconds (1 hour)

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

# Contextualization Prompt (for history-aware retrieval)
CONTEXTUALIZE_Q_SYSTEM_PROMPT = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

# Main QA System Prompt
QA_SYSTEM_PROMPT = (
    "You are a smart, helpful IOT product support assistant with expertise in 4 IOT products:\n"
    "1. Smart Home Hub - Central control unit for smart home devices\n"
    "2. Security Camera System - Wireless security camera with AI detection\n"
    "3. Smart Thermostat - AI-powered temperature control system\n"
    "4. Smart Lighting System - Automated lighting control with voice commands\n\n"
    "Your capabilities:\n"
    "- Answer questions about any of the 4 IOT products intelligently\n"
    "- When asked to list products, provide comprehensive information about all 4\n"
    "- Use the provided documentation context to give accurate, detailed answers\n"
    "- Ask follow-up questions when needed for better assistance\n"
    "- Be conversational, helpful, and professional\n\n"
    "Use the following context to answer the user's question:\n\n"
    "{context}"
)

# Language Selection Prompt
LANGUAGE_SELECTION_PROMPT = (
    "Would you like to chat in English or Malay? "
    "Type 'Exit' anytime to end the chat."
)

# =============================================================================
# PRODUCT CONFIGURATION
# =============================================================================

# IOT Product Information
IOT_PRODUCTS = [
    {
        "name": "Smart Home Hub",
        "description": "Central control unit for smart home devices",
        "expert": {
            "name": "John Smith",
            "email": "john.smith@company.com",
            "phone": "+1-555-0101"
        }
    },
    {
        "name": "Security Camera System",
        "description": "Wireless security camera with AI detection",
        "expert": {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@company.com",
            "phone": "+1-555-0102"
        }
    },
    {
        "name": "Smart Thermostat",
        "description": "AI-powered temperature control system",
        "expert": {
            "name": "Mike Chen",
            "email": "mike.chen@company.com",
            "phone": "+1-555-0103"
        }
    },
    {
        "name": "Smart Lighting System",
        "description": "Automated lighting control with voice commands",
        "expert": {
            "name": "Lisa Wang",
            "email": "lisa.wang@company.com",
            "phone": "+1-555-0104"
        }
    }
]

# Overall IOT Product Experts (for general support and fallback)
OVERALL_EXPERTS = [
    {
        "name": "Dr. Emily Rodriguez",
        "title": "Senior IOT Technical Lead",
        "email": "emily.rodriguez@company.com",
        "phone": "+1-555-0201",
        "specialties": ["All IOT Products", "System Integration", "Technical Architecture"]
    },
    {
        "name": "Alex Thompson",
        "title": "IOT Customer Success Manager",
        "email": "alex.thompson@company.com",
        "phone": "+1-555-0202",
        "specialties": ["Customer Support", "Product Training", "Troubleshooting"]
    }
]

# =============================================================================
# FILE PATHS
# =============================================================================

# Data directories
DATA_DIR = "data"
PRODUCT_DOCS_DIR = os.path.join(DATA_DIR, "iot_products")
TEMP_DIR = "temp"

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_config():
    """
    Validate that all required configuration is present
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    required_vars = [
        'GROQ_API_KEY',
        'MYSQL_HOST',
        'MYSQL_USER',
        'MYSQL_PASSWORD',
        'MYSQL_DATABASE'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {value[:10]}{'...' if len(value) > 10 else ''}")
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please check your .env file or Kubernetes environment variables")
        return False
    
    print("✅ All required environment variables are set")
    return True 