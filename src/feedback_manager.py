"""
Feedback management module for the IOT Product Support Chatbot

This module handles:
- User feedback collection and storage
- Expert contact information management
- Feedback analysis and reporting
- Integration with session management
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Local imports
from config.settings import IOT_PRODUCTS, OVERALL_EXPERTS
from config.database import db_manager
from src.session_manager import session_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackManager:
    """
    Manages user feedback and expert contact information
    
    This class handles:
    - Feedback collection and validation
    - Expert contact information retrieval
    - Feedback storage and analysis
    - Integration with session management
    """
    
    def __init__(self):
        """Initialize the feedback manager"""
        self.feedback_templates = {
            "satisfied": {
                "title": "Thank you for your feedback!",
                "message": "We're glad we could help you with your IOT product questions. If you need further assistance, feel free to contact our product expert.",
                "icon": "✅",
                "title_malay": "Terima kasih atas maklum balas anda!",
                "message_malay": "Kami gembira dapat membantu anda dengan soalan produk IOT anda. Jika anda memerlukan bantuan lanjut, sila hubungi pakar produk kami."
            },
            "unsatisfied": {
                "title": "We're sorry to hear that",
                "message": "Let us connect you with our product expert for better assistance.",
                "icon": "❌",
                "title_malay": "Kami sedih mendengarnya",
                "message_malay": "Mari kami hubungkan anda dengan pakar produk kami untuk bantuan yang lebih baik."
            },
            "skipped": {
                "title": "Session completed",
                "message": "Thank you for using our IOT Product Support Chatbot. We hope we were able to help you!",
                "icon": "⏭️",
                "title_malay": "Sesi selesai",
                "message_malay": "Terima kasih kerana menggunakan Chatbot Sokongan Produk IOT kami. Kami berharap kami dapat membantu anda!"
            }
        }
    
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
                        expert_info = product["expert"]
                        logger.info(f"Found product-specific expert for {product_name}: {expert_info['name']}")
                        return expert_info
            
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
    
    def save_feedback(self, session_id: str, satisfaction_rating: str) -> bool:
        """
        Save user feedback to the database
        
        Args:
            session_id (str): Session identifier
            satisfaction_rating (str): 'satisfied' or 'unsatisfied'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Handle "skipped" feedback as "unsatisfied"
            if satisfaction_rating == "skipped":
                satisfaction_rating = "unsatisfied"
                logger.info(f"Converting 'skipped' feedback to 'unsatisfied' for session {session_id}")
            
            # Validate satisfaction rating
            if satisfaction_rating not in ["satisfied", "unsatisfied"]:
                logger.error(f"Invalid satisfaction rating: {satisfaction_rating}")
                return False
            
            # Save feedback to database (without expert details)
            success = db_manager.save_feedback(session_id, satisfaction_rating)
            
            if success:
                logger.info(f"Saved feedback for session {session_id}: {satisfaction_rating}")
                
                # Mark expert as contacted if feedback is unsatisfied
                if satisfaction_rating == "unsatisfied":
                    session_manager.mark_expert_contacted(session_id)
                
                return True
            else:
                logger.error(f"Failed to save feedback for session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return False
    
    def get_feedback_template(self, satisfaction_rating: str, language: str = "English") -> Dict[str, str]:
        """
        Get feedback template for a satisfaction rating
        
        Args:
            satisfaction_rating (str): 'satisfied' or 'unsatisfied'
            language (str): Language for template ("English" or "Malay")
            
        Returns:
            Dict[str, str]: Feedback template
        """
        try:
            if satisfaction_rating in self.feedback_templates:
                template = self.feedback_templates[satisfaction_rating]
                
                # Return language-specific template
                if language == "Malay":
                    return {
                        "title": template.get("title_malay", template["title"]),
                        "message": template.get("message_malay", template["message"]),
                        "icon": template["icon"]
                    }
                else:
                    return {
                        "title": template["title"],
                        "message": template["message"],
                        "icon": template["icon"]
                    }
            else:
                logger.warning(f"No template found for rating: {satisfaction_rating}")
                if language == "Malay":
                    return {
                        "title": "Terima kasih atas maklum balas anda!",
                        "message": "Kami menghargai input anda.",
                        "icon": "📝"
                    }
                else:
                    return {
                        "title": "Thank you for your feedback!",
                        "message": "We appreciate your input.",
                        "icon": "📝"
                    }
                
        except Exception as e:
            logger.error(f"Error getting feedback template: {e}")
            if language == "Malay":
                return {
                    "title": "Maklum Balas",
                    "message": "Terima kasih atas maklum balas anda.",
                    "icon": "📝"
                }
            else:
                return {
                    "title": "Feedback",
                    "message": "Thank you for your feedback.",
                    "icon": "📝"
                }
    
    def should_show_feedback_modal(self, session_id: str) -> bool:
        """
        Check if feedback modal should be shown for this session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            bool: True if feedback modal should be shown
        """
        try:
            return session_manager.should_show_feedback(session_id)
            
        except Exception as e:
            logger.error(f"Error checking feedback modal condition: {e}")
            return False
    
    def get_session_product(self, session_id: str) -> Optional[str]:
        """
        Get the product involved in the session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Optional[str]: Product name or None
        """
        try:
            session_info = session_manager.get_session_info(session_id)
            if session_info:
                return session_info.get("product_involved")
            return None
            
        except Exception as e:
            logger.error(f"Error getting session product: {e}")
            return None
    
    def create_feedback_modal_data(self, session_id: str) -> Dict[str, Any]:
        """
        Create data for feedback modal
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Dict[str, Any]: Feedback modal data
        """
        try:
            # Get session product
            product_name = self.get_session_product(session_id)
            
            # Get expert contact if product is identified
            expert_info = None
            if product_name:
                expert_info = self.get_expert_contact(product_name)
            
            modal_data = {
                "session_id": session_id,
                "product_name": product_name,
                "expert_info": expert_info,
                "show_expert_contact": expert_info is not None,
                "feedback_options": [
                    {"value": "satisfied", "label": "✅ Satisfied", "color": "green"},
                    {"value": "unsatisfied", "label": "❌ Not Satisfied", "color": "red"}
                ]
            }
            
            return modal_data
            
        except Exception as e:
            logger.error(f"Error creating feedback modal data: {e}")
            return {
                "session_id": session_id,
                "product_name": None,
                "expert_info": None,
                "show_expert_contact": False,
                "feedback_options": [
                    {"value": "satisfied", "label": "✅ Satisfied", "color": "green"},
                    {"value": "unsatisfied", "label": "❌ Not Satisfied", "color": "red"}
                ]
            }
    
    def process_feedback_response(self, session_id: str, satisfaction_rating: str) -> Dict[str, Any]:
        """
        Process user feedback response
        
        Args:
            session_id (str): Session identifier
            satisfaction_rating (str): User's satisfaction rating
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            # Get session product and expert info
            product_name = self.get_session_product(session_id)
            expert_info = None
            
            # Get expert contact - will use product-specific expert if available, otherwise overall expert
            expert_info = self.get_expert_contact(product_name)
            if product_name:
                logger.info(f"Found product for session {session_id}: {product_name}")
            else:
                logger.info(f"No specific product found for session {session_id}, using overall expert")
            
            # Handle "skipped" feedback as "unsatisfied" for processing
            original_rating = satisfaction_rating
            if satisfaction_rating == "skipped":
                satisfaction_rating = "unsatisfied"
                logger.info(f"Processing 'skipped' feedback as 'unsatisfied' for session {session_id}")
            
            # Save feedback to database (without expert details)
            feedback_saved = self.save_feedback(session_id, satisfaction_rating)
            
            # Get session language for appropriate template
            session_info = session_manager.get_session_info(session_id)
            session_language = session_info.get('language', 'English') if session_info else 'English'
            
            # Get feedback template (use original rating for display)
            template = self.get_feedback_template(original_rating, session_language)
            
            # Prepare response
            response = {
                "success": feedback_saved,
                "template": template,
                "expert_contact": None,
                "show_expert_contact": False,
                "product_name": product_name
            }
            
            # Add expert contact for both satisfied and unsatisfied cases
            if expert_info:
                response["expert_contact"] = self.format_expert_contact(expert_info)
                response["show_expert_contact"] = True
                logger.info(f"Added expert contact for {original_rating} feedback: {expert_info['name']}")
            
            logger.info(f"Processed feedback for session {session_id}: {original_rating}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing feedback response: {e}")
            return {
                "success": False,
                "template": self.get_feedback_template("satisfied"),
                "expert_contact": None,
                "show_expert_contact": False,
                "error": str(e)
            }
    
    def get_all_experts(self) -> List[Dict]:
        """
        Get all available experts (product-specific and overall)
        
        Returns:
            List[Dict]: List of all expert information
        """
        try:
            all_experts = []
            
            # Add product-specific experts
            for product in IOT_PRODUCTS:
                expert = product["expert"].copy()
                expert["product"] = product["name"]
                expert["type"] = "product_specific"
                all_experts.append(expert)
            
            # Add overall experts
            for expert in OVERALL_EXPERTS:
                expert_copy = expert.copy()
                expert_copy["type"] = "overall"
                all_experts.append(expert_copy)
            
            logger.info(f"Retrieved {len(all_experts)} total experts")
            return all_experts
            
        except Exception as e:
            logger.error(f"Error getting all experts: {e}")
            return []
    
    def get_expert_by_specialty(self, specialty: str) -> Optional[Dict]:
        """
        Get expert by specialty
        
        Args:
            specialty (str): Specialty to search for
            
        Returns:
            Optional[Dict]: Expert information or None
        """
        try:
            # Check overall experts first
            for expert in OVERALL_EXPERTS:
                if specialty.lower() in [s.lower() for s in expert.get("specialties", [])]:
                    logger.info(f"Found overall expert for specialty '{specialty}': {expert['name']}")
                    return expert
            
            # Check product-specific experts
            for product in IOT_PRODUCTS:
                if specialty.lower() in product["name"].lower():
                    expert = product["expert"]
                    logger.info(f"Found product expert for specialty '{specialty}': {expert['name']}")
                    return expert
            
            # Return first overall expert as fallback
            if OVERALL_EXPERTS:
                logger.info(f"No specific expert found for '{specialty}', using overall expert")
                return OVERALL_EXPERTS[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting expert by specialty: {e}")
            return None
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Get feedback statistics from database
        
        Returns:
            Dict[str, Any]: Feedback statistics
        """
        try:
            # This would require adding a method to get feedback statistics from database
            # For now, return basic structure
            return {
                "total_feedback": 0,
                "satisfied_count": 0,
                "unsatisfied_count": 0,
                "satisfaction_rate": 0.0,
                "expert_contacted_count": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback statistics: {e}")
            return {}
    
    def validate_feedback_rating(self, rating: str) -> bool:
        """
        Validate feedback rating
        
        Args:
            rating (str): Feedback rating to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        valid_ratings = ["satisfied", "unsatisfied"]
        return rating.lower() in valid_ratings
    
    def get_feedback_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feedback analytics for the specified period
        
        Args:
            days (int): Number of days to analyze
            
        Returns:
            Dict[str, Any]: Feedback analytics
        """
        try:
            # This would require database queries to get analytics
            # For now, return basic structure
            return {
                "period_days": days,
                "total_sessions": 0,
                "total_feedback": 0,
                "satisfaction_rate": 0.0,
                "top_products": [],
                "common_issues": []
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {}

# Global feedback manager instance
feedback_manager = FeedbackManager() 