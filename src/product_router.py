"""
Product routing module for the IOT Product Support Chatbot

This module handles:
- Intelligent routing of user queries to relevant IOT products
- Product-specific keyword matching and similarity search
- Handling of general queries and product listing requests
- Expert contact information retrieval
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# Local imports
from config.settings import IOT_PRODUCTS, OVERALL_EXPERTS, LANGUAGE_SELECTION_PROMPT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductRouter:
    """
    Routes user queries to the most relevant IOT product
    
    This class provides intelligent routing based on:
    - Keyword matching and similarity search
    - Product-specific terminology
    - Query context and intent analysis
    - Expert contact information retrieval
    """
    
    def __init__(self):
        """Initialize the product router"""
        # Define product-specific keywords for better routing
        self.product_keywords = {
            "Smart Home Hub": [
                "hub", "central", "control", "smart home", "automation", "central unit",
                "main controller", "home automation", "smart hub", "control center"
            ],
            "Security Camera System": [
                "camera", "security", "surveillance", "monitoring", "recording", "video",
                "cctv", "security camera", "surveillance system", "motion detection",
                "night vision", "recording", "footage", "monitor"
            ],
            "Smart Thermostat": [
                "thermostat", "temperature", "heating", "cooling", "climate", "hvac",
                "smart thermostat", "temperature control", "heating system", "cooling system",
                "climate control", "energy saving", "temperature sensor"
            ],
            "Smart Lighting System": [
                "lighting", "lights", "bulb", "lamp", "illumination", "smart lights",
                "smart lighting", "light control", "dimmer", "color", "brightness",
                "automated lighting", "voice control", "light bulb"
            ]
        }
        
        # Common exit commands
        self.exit_commands = ["exit", "quit", "end", "stop", "bye", "goodbye"]
        
        # Language selection keywords
        self.language_keywords = {
            "english": ["english", "en", "inggris", "bahasa inggris"],
            "malay": ["malay", "malaysian", "melayu", "bahasa melayu", "bm"]
        }
    
    def is_exit_command(self, query: str) -> bool:
        """
        Check if the query is an exit command
        
        Args:
            query (str): User's query
            
        Returns:
            bool: True if it's an exit command, False otherwise
        """
        query_lower = query.lower().strip()
        return query_lower in self.exit_commands
    
    def is_language_selection(self, query: str) -> Optional[str]:
        """
        Check if the query is a language selection
        
        Args:
            query (str): User's query
            
        Returns:
            Optional[str]: Selected language or None
        """
        query_lower = query.lower().strip()
        
        for language, keywords in self.language_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return language.title()
        
        return None
    
    def is_product_listing_request(self, query: str) -> bool:
        """
        Check if the query is asking for a list of all products
        
        Args:
            query (str): User's query
            
        Returns:
            bool: True if asking for product list, False otherwise
        """
        query_lower = query.lower()
        listing_keywords = [
            "list all products", "show all products", "what products", "available products",
            "all products", "product list", "what do you have", "what can you help with",
            "list products", "show products", "available iot", "iot products",
            "list all the products", "list all the products in your company", "what products do you have",
            "show me all products", "what are your products", "list your products",
            "company products", "your products", "all your products"
        ]
        
        return any(keyword in query_lower for keyword in listing_keywords)
    
    def get_product_listing_response(self) -> str:
        """
        Generate response listing all IOT products
        
        Returns:
            str: Formatted response with all products
        """
        product_list = []
        for product in IOT_PRODUCTS:
            product_list.append(f"• **{product['name']}**: {product['description']}")
        
        response = "Here are all our IOT products:\n\n" + "\n".join(product_list)
        response += "\n\nYou can ask me specific questions about any of these products! For example:\n"
        response += "• 'How do I install the Smart Home Hub?'\n"
        response += "• 'What features does the Security Camera have?'\n"
        response += "• 'How do I troubleshoot my Smart Thermostat?'\n"
        response += "• 'How do I set up the Smart Lighting System?'"
        
        return response
    
    def calculate_similarity(self, query: str, keywords: List[str]) -> float:
        """
        Calculate similarity between query and product keywords
        
        Args:
            query (str): User's query
            keywords (List[str]): Product keywords
            
        Returns:
            float: Similarity score (0-1)
        """
        query_lower = query.lower()
        
        # Check for exact keyword matches
        exact_matches = sum(1 for keyword in keywords if keyword in query_lower)
        
        # Calculate sequence similarity for partial matches
        similarities = []
        for keyword in keywords:
            similarity = SequenceMatcher(None, query_lower, keyword).ratio()
            similarities.append(similarity)
        
        # Combine exact matches and similarity scores
        exact_score = exact_matches / len(keywords) if keywords else 0
        similarity_score = max(similarities) if similarities else 0
        
        # Weighted combination (exact matches are more important)
        final_score = (exact_score * 0.7) + (similarity_score * 0.3)
        
        return final_score
    
    def route_query_to_product(self, query: str) -> Tuple[Optional[str], float]:
        """
        Route user query to the most relevant IOT product
        
        Args:
            query (str): User's query
            
        Returns:
            Tuple[Optional[str], float]: (Product name, confidence score)
        """
        try:
            # First check if this is a product listing request
            if self.is_product_listing_request(query):
                logger.info(f"Product listing request detected: '{query}'")
                return None, 1.0  # Return None to indicate listing request
            
            best_product = None
            best_score = 0.0
            
            # Calculate similarity for each product
            for product_name, keywords in self.product_keywords.items():
                similarity_score = self.calculate_similarity(query, keywords)
                
                if similarity_score > best_score:
                    best_score = similarity_score
                    best_product = product_name
            
            # Set minimum threshold for routing
            if best_score < 0.1:  # Very low confidence
                logger.info(f"Low confidence routing for query: '{query}' (score: {best_score})")
                return None, best_score
            
            logger.info(f"Routed query '{query}' to {best_product} (confidence: {best_score:.2f})")
            return best_product, best_score
            
        except Exception as e:
            logger.error(f"Error routing query '{query}': {e}")
            return None, 0.0
    
    def get_expert_contact(self, product_name: str = None) -> Optional[Dict]:
        """
        Get expert contact information for a specific product or overall expert
        
        Args:
            product_name (str): Name of the IOT product (optional)
            
        Returns:
            Optional[Dict]: Expert contact information or None
        """
        try:
            # If product name is provided, try to find product-specific expert
            if product_name:
                for product in IOT_PRODUCTS:
                    if product["name"] == product_name:
                        return product["expert"]
            
            # If no product-specific expert found or no product specified, return overall expert
            if OVERALL_EXPERTS:
                # Return the first overall expert (Senior Technical Lead)
                overall_expert = OVERALL_EXPERTS[0]
                logger.info(f"Using overall expert: {overall_expert['name']}")
                return overall_expert
            
            logger.warning(f"No expert found for product: {product_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting expert contact for {product_name}: {e}")
            return None
    
    def format_expert_contact(self, expert_info: Dict) -> str:
        """
        Format expert contact information for display
        
        Args:
            expert_info (Dict): Expert contact information
            
        Returns:
            str: Formatted expert contact string
        """
        try:
            # Check if this is an overall expert (has title and specialties)
            if 'title' in expert_info and 'specialties' in expert_info:
                contact_info = f"""
**Overall IOT Expert Contact Information:**

👤 **Name:** {expert_info['name']}
🏷️ **Title:** {expert_info['title']}
📧 **Email:** {expert_info['email']}
📞 **Phone:** {expert_info['phone']}
🎯 **Specialties:** {', '.join(expert_info['specialties'])}

Feel free to contact our expert for comprehensive IOT support!
                """
            else:
                # Product-specific expert
                contact_info = f"""
**Product Expert Contact Information:**

👤 **Name:** {expert_info['name']}
📧 **Email:** {expert_info['email']}
📞 **Phone:** {expert_info['phone']}

Feel free to contact our expert for detailed technical support!
                """
            
            return contact_info.strip()
            
        except Exception as e:
            logger.error(f"Error formatting expert contact: {e}")
            return "Expert contact information not available."
    
    def analyze_query_intent(self, query: str) -> Dict:
        """
        Analyze the intent of the user query
        
        Args:
            query (str): User's query
            
        Returns:
            Dict: Analysis results including intent type and routing information
        """
        try:
            analysis = {
                "is_exit": False,
                "is_language_selection": False,
                "selected_language": None,
                "is_product_listing": False,
                "routed_product": None,
                "confidence_score": 0.0,
                "expert_contact": None
            }
            
            # Check for exit command
            if self.is_exit_command(query):
                analysis["is_exit"] = True
                return analysis
            
            # Check for language selection
            selected_language = self.is_language_selection(query)
            if selected_language:
                analysis["is_language_selection"] = True
                analysis["selected_language"] = selected_language
                return analysis
            
            # Check for product listing request
            if self.is_product_listing_request(query):
                analysis["is_product_listing"] = True
                return analysis
            
            # Route to specific product
            routed_product, confidence = self.route_query_to_product(query)
            analysis["routed_product"] = routed_product
            analysis["confidence_score"] = confidence
            
            # Get expert contact if product is identified
            if routed_product:
                expert_info = self.get_expert_contact(routed_product)
                analysis["expert_contact"] = expert_info
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing query intent: {e}")
            return {
                "is_exit": False,
                "is_language_selection": False,
                "selected_language": None,
                "is_product_listing": False,
                "routed_product": None,
                "confidence_score": 0.0,
                "expert_contact": None
            }
    
    def get_language_selection_prompt(self) -> str:
        """
        Get the language selection prompt
        
        Returns:
            str: Language selection prompt
        """
        return LANGUAGE_SELECTION_PROMPT

# Global product router instance
product_router = ProductRouter() 