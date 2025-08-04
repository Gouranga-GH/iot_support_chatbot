"""
Source package for the IOT Product Support Chatbot

This package contains all the core components:
- Document processing and vector database management
- Product routing and query analysis
- RAG chain and conversational AI
- Session management and feedback handling
"""

from .document_processor import document_processor
from .product_router import product_router
from .rag_chain import rag_chain
from .session_manager import session_manager
from .feedback_manager import feedback_manager

__all__ = [
    'document_processor',
    'product_router', 
    'rag_chain',
    'session_manager',
    'feedback_manager'
] 