"""
Configuration package for the IOT Product Support Chatbot

This package contains all configuration settings, database setup,
and environment management for the chatbot application.
"""

from .settings import *
from .database import db_manager

__all__ = ['db_manager'] 