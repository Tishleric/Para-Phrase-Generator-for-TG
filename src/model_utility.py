# src/model_utility.py
# Utility for managing model selection and fallbacks
"""
This module provides utility functions for model selection,
fallback mechanisms, and model availability checks for the
OpenAI Agents SDK.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union, Tuple

# Import from centralized SDK imports
from .sdk_imports import SDK_AVAILABLE, OpenAIProvider
from .config import DEBUG_MODE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define model tiers
MODEL_TIERS = {
    "high": ["gpt-4o", "claude-3-7-sonnet-20240620", "gpt-4-turbo", "gpt-4-0125-preview", "o3"],
    "medium": ["gpt-3.5-turbo", "o2", "o1"],
    "low": ["o1-mini", "o3-mini"]
}

# Default models to use for each purpose
DEFAULT_MODELS = {
    "delegation": "gpt-4o",  # Use GPT-4o for routing
    "summarization": "claude-3-7-sonnet-20240620",  # Use Claude for summarization
    "content_analysis": "gpt-4o",
    "twitter": "gpt-4o",  # Twitter link processing
    "tone_summary": "claude-3-7-sonnet-20240620",  # Use Claude for tone-specific summaries
    "photo": "gpt-4o",     # Use GPT-4o for photo analysis as it has strong vision capabilities
    "football": "gpt-4o",  # Use GPT-4o for football score analysis
    "fallback": "gpt-4o"   # Use GPT-4o as fallback
}

class ModelUtility:
    """
    Utility class for model selection and management.
    
    This class provides functions for selecting appropriate models,
    handling fallbacks when preferred models are unavailable, and
    checking model availability.
    
    Attributes:
        available_models (List[str]): List of available models
    """
    
    def __init__(self):
        """
        Initialize the ModelUtility instance.
        """
        self.available_models = self._get_available_models()
        logger.info(f"Available models: {self.available_models}")
    
    def _get_available_models(self) -> List[str]:
        """
        Get a list of available models.
        
        Returns:
            List[str]: List of available model IDs
        """
        if not SDK_AVAILABLE:
            # When SDK isn't available, return a default set of models
            return [
                "claude-3-7-sonnet-20240620", "o3", "o3-mini", "o2", "o1", "o1-mini",
                "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
            ]
        
        try:
            # Here we would ideally query the API for available models
            # For now, we'll return a default set
            return [
                "claude-3-7-sonnet-20240620", "o3", "o3-mini", "o2", "o1", "o1-mini",
                "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"
            ]
        except Exception as e:
            logger.warning(f"Failed to get available models: {e}")
            # Return a conservative list of likely available models
            return ["claude-3-7-sonnet-20240620", "gpt-4o", "o3-mini", "o1-mini", "gpt-3.5-turbo"]
    
    def get_model_for_purpose(self, purpose: str, tier: str = "medium") -> str:
        """
        Get the best available model for a specific purpose.
        
        Args:
            purpose (str): The purpose of the model (e.g., 'delegation', 'summarization')
            tier (str): The tier of model to use ('high', 'medium', 'low')
            
        Returns:
            str: The ID of the selected model
        """
        # Try to use the default model for the purpose
        default_model = DEFAULT_MODELS.get(purpose, DEFAULT_MODELS["fallback"])
        
        if default_model in self.available_models:
            return default_model
        
        # If the default model isn't available, try to find another in the same tier
        tier_models = MODEL_TIERS.get(tier, MODEL_TIERS["low"])
        
        for model in tier_models:
            if model in self.available_models:
                logger.info(f"Using {model} as fallback for {purpose} (default: {default_model})")
                return model
        
        # If no models in the tier are available, use the fallback model
        fallback = DEFAULT_MODELS["fallback"]
        logger.warning(f"No suitable models available for {purpose}. Using fallback: {fallback}")
        return fallback
    
    def is_model_available(self, model_id: str) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_id (str): The ID of the model to check
            
        Returns:
            bool: True if the model is available, False otherwise
        """
        return model_id in self.available_models
    
    def get_model_tier(self, model_id: str) -> str:
        """
        Get the tier of a specific model.
        
        Args:
            model_id (str): The ID of the model to check
            
        Returns:
            str: The tier of the model ('high', 'medium', 'low')
        """
        for tier, models in MODEL_TIERS.items():
            if model_id in models:
                return tier
        
        # Default to low tier if not found
        return "low" 