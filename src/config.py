# src/config.py
# Configuration module for Para-Phrase Generator
"""
This module manages configuration settings for the Para-Phrase Generator,
including agent settings, API keys, and other configurable parameters.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Environment settings
BOT_ENVIRONMENT = os.environ.get("BOT_ENVIRONMENT", "production")
DEBUG_MODE = os.environ.get("DEBUG_MODE", "False").lower() == "true"

# Environment-specific configurations
ENV_CONFIG = {
    "production": {
        "USE_AGENT_SYSTEM": True,
        "MAX_MESSAGES_PER_CHAT": 100,
        "DEFAULT_TONE": "stoic",
        "MAX_BASE_TOKENS": 250,
        "MAX_TOTAL_TOKENS": 500,
        "ADD_MESSAGE_LINKS": True,
        "ENABLE_IMAGE_ANALYSIS": True,
        "MAX_LINKS_PER_SUMMARY": 8,
    },
    "staging": {
        "USE_AGENT_SYSTEM": True,
        "MAX_MESSAGES_PER_CHAT": 100,
        "DEFAULT_TONE": "stoic",
        "MAX_BASE_TOKENS": 250,
        "MAX_TOTAL_TOKENS": 500,
        "ADD_MESSAGE_LINKS": True,
        "ENABLE_IMAGE_ANALYSIS": True,
        "MAX_LINKS_PER_SUMMARY": 8,
    }
}

# Override configuration based on environment
current_env_config = ENV_CONFIG.get(BOT_ENVIRONMENT, ENV_CONFIG["production"])

# Update configuration with environment-specific settings
USE_AGENT_SYSTEM = os.environ.get("USE_AGENT_SYSTEM", str(current_env_config["USE_AGENT_SYSTEM"])).lower() == "true"
MAX_MESSAGES_PER_CHAT = int(os.environ.get("MAX_MESSAGES_PER_CHAT", str(current_env_config["MAX_MESSAGES_PER_CHAT"])))
DEFAULT_TONE = os.environ.get("DEFAULT_TONE", current_env_config["DEFAULT_TONE"])
MAX_BASE_TOKENS = int(os.environ.get("MAX_BASE_TOKENS", str(current_env_config["MAX_BASE_TOKENS"])))
MAX_TOTAL_TOKENS = int(os.environ.get("MAX_TOTAL_TOKENS", str(current_env_config["MAX_TOTAL_TOKENS"])))
ADD_MESSAGE_LINKS = os.environ.get("ADD_MESSAGE_LINKS", str(current_env_config["ADD_MESSAGE_LINKS"])).lower() == "true"
ENABLE_IMAGE_ANALYSIS = os.environ.get("ENABLE_IMAGE_ANALYSIS", str(current_env_config["ENABLE_IMAGE_ANALYSIS"])).lower() == "true"
MAX_LINKS_PER_SUMMARY = int(os.environ.get("MAX_LINKS_PER_SUMMARY", str(current_env_config["MAX_LINKS_PER_SUMMARY"])))

# Feature flags
# USE_AGENT_SYSTEM is already set above

# Message history configuration
MAX_MESSAGES_PER_CHAT = 100  # Maximum number of messages to store per chat

# Default tone configuration
AVAILABLE_TONES = ["stoic", "chaotic", "pubbie", "deaf"]

# Summarization configuration
TOKENS_PER_MESSAGE = 10  # Additional tokens per message

# Agent configuration
AGENT_TIER_MAPPING = {
    "delegation": "low",     # Use lower-tier models for routing
    "tone_summary": "high",  # Use higher-tier models for quality summaries
    "twitter": "medium",     # Medium tier for Twitter link processing
    "photo": "high",         # High tier for image analysis (requires vision)
    "football": "medium",    # Medium tier for football score lookups
}

# Special configuration for the deaf tone
# The "deaf" tone doesn't need to process images or football content
DEAF_TONE_SKIP_FEATURES = ["photo", "football"]

# Model provider mapping
MODEL_PROVIDER_MAPPING = {
    "tone_summary": "claude",    # Use Claude for tone summaries
    "summarization": "claude",   # Use Claude for general summarization
    "default": "openai"          # Use OpenAI (GPT-4o) as default
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# Initialize model utility instance
_model_utility = None

def get_model_utility():
    """
    Get the ModelUtility instance.
    
    Returns:
        ModelUtility: The ModelUtility instance
    """
    global _model_utility
    if _model_utility is None:
        from .model_utility import ModelUtility
        _model_utility = ModelUtility()
    return _model_utility

def get_model_provider(agent_type):
    """
    Get the appropriate model provider for an agent type.
    
    Args:
        agent_type (str): The type of agent (e.g., "delegation", "tone_summary")
        
    Returns:
        ModelProvider: The model provider to use
    """
    from .sdk_imports import CLAUDE_MODEL_PROVIDER, OpenAIProvider
    
    provider_type = MODEL_PROVIDER_MAPPING.get(agent_type, MODEL_PROVIDER_MAPPING["default"])
    
    # Return the appropriate provider
    if provider_type == "claude":
        return CLAUDE_MODEL_PROVIDER
    else:
        return OpenAIProvider()

def get_agent_model(agent_type, tier=None):
    """
    Get the model to use for a specific agent type.
    
    Args:
        agent_type (str): The type of agent (e.g., "delegation", "tone_summary")
        tier (str, optional): Override the default tier for this agent type
        
    Returns:
        str: The model name to use for the agent
    """
    # Get the model utility instance
    model_utility = get_model_utility()
    
    # Determine the tier to use
    if tier is None:
        tier = AGENT_TIER_MAPPING.get(agent_type, "medium")
    
    # Get the model for the purpose and tier
    return model_utility.get_model_for_purpose(agent_type, tier) 