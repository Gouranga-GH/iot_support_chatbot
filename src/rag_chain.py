"""
RAG Chain module for the IOT Product Support Chatbot

This module handles:
- RAG pipeline with ChatGroq LLM integration
- History-aware retrieval and conversation management
- Product-specific document retrieval
- Response generation with context
"""

import logging
from typing import Dict, List, Optional, Any

# LangChain imports
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.runnables.history import RunnableWithMessageHistory

# Local imports
from config.settings import (
    LLM_MODEL, CONTEXTUALIZE_Q_SYSTEM_PROMPT, QA_SYSTEM_PROMPT,
    GROQ_API_KEY
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGChain:
    """
    Handles the RAG pipeline and conversational AI functionality
    
    This class manages:
    - LLM setup with ChatGroq integration
    - History-aware document retrieval
    - Conversational chain with memory
    - Product-specific response generation
    """
    
    def __init__(self, api_key: str):
        """
        Initialize RAG chain with ChatGroq LLM
        
        Args:
            api_key (str): ChatGroq API key for LLM access
        """
        try:
            # Initialize ChatGroq LLM with specified model
            self.llm = ChatGroq(
                groq_api_key=api_key,
                model_name=LLM_MODEL,
                temperature=0.1  # Low temperature for consistent responses
            )
            
            # Initialize chain components
            self.rag_chain = None
            self.conversational_rag_chain = None
            self.current_retriever = None
            
            logger.info(f"RAG Chain initialized with model: {LLM_MODEL}")
            
        except Exception as e:
            logger.error(f"Error initializing RAG Chain: {e}")
            raise
    
    def create_rag_chain(self, retriever):
        """
        Create the RAG chain with history-aware retriever and QA chain
        
        Args:
            retriever: Document retriever for semantic search
        """
        try:
            # Create prompt for reformulating user questions with chat history
            contextualize_q_prompt = ChatPromptTemplate.from_messages([
                ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])
            
            # Create history-aware retriever
            history_aware_retriever = create_history_aware_retriever(
                self.llm, 
                retriever, 
                contextualize_q_prompt
            )
            
            # Create prompt for the main QA task
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", QA_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])
            
            # Create chain for combining retrieved documents and generating answers
            question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
            
            # Create the main retrieval-augmented generation chain
            self.rag_chain = create_retrieval_chain(
                history_aware_retriever, 
                question_answer_chain
            )
            
            self.current_retriever = retriever
            logger.info("RAG chain created successfully")
            
        except Exception as e:
            logger.error(f"Error creating RAG chain: {e}")
            raise
    
    def create_conversational_chain(self, get_session_history_func):
        """
        Create a conversational RAG chain that maintains message history
        
        Args:
            get_session_history_func: Function to get session history for a session ID
        """
        try:
            if not self.rag_chain:
                raise ValueError("RAG chain not initialized. Call create_rag_chain first.")
            
            # Wrap the RAG chain with message history for context-aware conversations
            self.conversational_rag_chain = RunnableWithMessageHistory(
                self.rag_chain,
                get_session_history_func,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )
            
            logger.info("Conversational RAG chain created successfully")
            
        except Exception as e:
            logger.error(f"Error creating conversational chain: {e}")
            raise
    
    def get_response(self, user_input: str, session_id: str, language: str = "English") -> Dict[str, Any]:
        """
        Get a smart response using intelligent document retrieval and LLM reasoning
        
        Args:
            user_input (str): User's question
            session_id (str): Session identifier for chat history
            language (str): Language for response ("English" or "Malay")
            
        Returns:
            Dict[str, Any]: Response from the chain with answer and metadata
        """
        try:
            # Import document processor for intelligent retrieval
            from src.document_processor import document_processor
            
            # Get session history for context
            from src.session_manager import session_manager
            history = session_manager.get_session_history(session_id)
            
            # Create intelligent prompt for the LLM with language control
            language_instruction = "IMPORTANT: You must respond ONLY in " + language + ". Do not use any other language in your response."
            
            intelligent_prompt = f"""
You are a smart IOT product support assistant. You have access to information about 4 IOT products:
1. Smart Home Hub - Central control unit for smart home devices
2. Security Camera System - Wireless security camera with AI detection  
3. Smart Thermostat - AI-powered temperature control system
4. Smart Lighting System - Automated lighting control with voice commands

{language_instruction}

User Question: {user_input}

Previous conversation context: {history[-4:] if history else 'No previous context'}

Please provide a helpful, accurate response in {language}. If the user asks to list products, mention all 4 products with brief descriptions.
If they ask about a specific product, provide detailed, helpful information.
If you need more specific information, ask follow-up questions.

Response in {language}:
"""
            
            # Get response from LLM
            response = self.llm.invoke(intelligent_prompt)
            
            # If we have document retrievers, enhance with document context
            if document_processor.product_vectorstores:
                try:
                    # Try to get relevant documents for the query
                    combined_retriever = document_processor.get_combined_retriever()
                    if combined_retriever:
                        # Get relevant documents
                        docs = combined_retriever.get_relevant_documents(user_input)
                        
                        if docs:
                            # Create enhanced prompt with document context and language control
                            doc_context = "\n\n".join([doc.page_content for doc in docs[:3]])
                            enhanced_prompt = f"""
Based on the following IOT product documentation and the user's question, provide a helpful response:

{language_instruction}

Documentation Context:
{doc_context}

User Question: {user_input}

Previous conversation: {history[-2:] if history else 'No previous context'}

Provide a comprehensive, accurate response in {language} using the documentation context:

"""
                            enhanced_response = self.llm.invoke(enhanced_prompt)
                            return {
                                "response": enhanced_response.content,
                                "source_documents": docs,
                                "session_id": session_id
                            }
                except Exception as e:
                    logger.warning(f"Could not retrieve documents: {e}")
            
            return {
                "response": response.content,
                "source_documents": [],
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "source_documents": [],
                "session_id": session_id
            }
    
    def get_direct_response(self, user_input: str) -> str:
        """
        Get a direct response without session history (for simple queries)
        
        Args:
            user_input (str): User's question
            
        Returns:
            str: Direct response from LLM
        """
        try:
            if not self.llm:
                raise ValueError("LLM not initialized")
            
            # Create a simple prompt for direct responses
            prompt = f"""
            You are a helpful IOT product support assistant. 
            Please provide a helpful response to the following question:
            
            Question: {user_input}
            
            Response:
            """
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Error getting direct response: {e}")
            return "I apologize, but I'm having trouble processing your request right now."
    
    def validate_api_key(self) -> bool:
        """
        Validate that the ChatGroq API key is working
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            if not GROQ_API_KEY:
                logger.error("No ChatGroq API key provided")
                return False
            
            # Test the API key with a simple request
            test_prompt = "Hello, this is a test message."
            response = self.llm.invoke(test_prompt)
            
            if response and response.content:
                logger.info("ChatGroq API key validated successfully")
                return True
            else:
                logger.error("Invalid response from ChatGroq API")
                return False
                
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the current LLM model
        
        Returns:
            Dict[str, str]: Model information
        """
        return {
            "model_name": LLM_MODEL,
            "provider": "ChatGroq",
            "temperature": "0.1",
            "max_tokens": "4096"
        }
    
    def switch_retriever(self, new_retriever):
        """
        Switch to a different retriever (e.g., for different products)
        
        Args:
            new_retriever: New document retriever
        """
        try:
            # Create new RAG chain with the new retriever
            self.create_rag_chain(new_retriever)
            
            # Recreate conversational chain if it exists
            if hasattr(self, '_get_session_history_func'):
                self.create_conversational_chain(self._get_session_history_func)
            
            logger.info("Switched to new retriever successfully")
            
        except Exception as e:
            logger.error(f"Error switching retriever: {e}")
            raise
    
    def _store_session_history_func(self, func):
        """
        Store the session history function for recreating conversational chain
        
        Args:
            func: Function to get session history
        """
        self._get_session_history_func = func

# Global RAG chain instance
rag_chain = None

def initialize_rag_chain(api_key: str):
    """Initialize the global RAG chain instance"""
    global rag_chain
    try:
        rag_chain = RAGChain(api_key)
        logger.info("Global RAG chain initialized successfully")
        return rag_chain
    except Exception as e:
        logger.error(f"Failed to initialize global RAG chain: {e}")
        return None 