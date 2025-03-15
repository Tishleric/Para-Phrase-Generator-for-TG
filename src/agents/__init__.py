# src/agents/__init__.py
# Package initialization file for agents
"""
This module contains agent implementations for the Para-Phrase Generator.
Agents are specialized components that handle specific aspects of message processing
and summarization using the OpenAI Agents framework.
"""

import logging
from typing import Dict, Type, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Singleton instances for agents
_delegation_agent = None
_tone_agents = {}
_twitter_agent = None
_football_agent = None
_photo_agent = None

def get_agent_classes():
    """
    Get the agent classes without causing circular imports.
    
    Returns:
        dict: Dictionary of agent classes
    """
    from .base_agent import BaseAgent
    from .delegation_agent import DelegationAgent
    from .tone_agent import ToneAgent
    from .twitter_agent import TwitterAgent
    from .football_agent import FootballAgent
    from .photo_agent import PhotoAgent
    from .interface import AgentInterface
    from .context import BotContext, RunContextManager
    
    return {
        'BaseAgent': BaseAgent,
        'DelegationAgent': DelegationAgent,
        'ToneAgent': ToneAgent,
        'TwitterAgent': TwitterAgent,
        'FootballAgent': FootballAgent,
        'PhotoAgent': PhotoAgent,
        'AgentInterface': AgentInterface,
        'BotContext': BotContext,
        'RunContextManager': RunContextManager,
    }

def get_delegation_agent():
    """
    Get the delegation agent singleton instance.
    
    Returns:
        DelegationAgent: The delegation agent instance
    """
    global _delegation_agent
    
    if _delegation_agent is None:
        from .delegation_agent import DelegationAgent
        _delegation_agent = DelegationAgent()
        logger.info("Delegation agent created")
    
    return _delegation_agent

def get_tone_agent(tone):
    """
    Get a tone agent singleton instance for a specific tone.
    
    Args:
        tone (str): The tone to get an agent for
    
    Returns:
        ToneAgent: The tone agent instance
    """
    global _tone_agents
    
    if tone not in _tone_agents:
        from .tone_agent import ToneAgent
        _tone_agents[tone] = ToneAgent(tone)
        logger.info(f"Tone agent created for tone: {tone}")
    
    return _tone_agents[tone]

def get_twitter_agent():
    """
    Get the twitter agent singleton instance.
    
    Returns:
        TwitterAgent: The twitter agent instance
    """
    global _twitter_agent
    
    if _twitter_agent is None:
        from .twitter_agent import TwitterAgent
        _twitter_agent = TwitterAgent()
        logger.info("Twitter agent created")
    
    return _twitter_agent

def get_football_agent():
    """
    Get the football agent singleton instance.
    
    Returns:
        FootballAgent: The football agent instance
    """
    global _football_agent
    
    if _football_agent is None:
        from .football_agent import FootballAgent
        _football_agent = FootballAgent()
        logger.info("Football agent created")
    
    return _football_agent

def get_photo_agent():
    """
    Get the photo agent singleton instance.
    
    Returns:
        PhotoAgent: The photo agent instance
    """
    global _photo_agent
    
    if _photo_agent is None:
        from .photo_agent import PhotoAgent
        _photo_agent = PhotoAgent()
        logger.info("Photo agent created")
    
    return _photo_agent

def reset_agents():
    """
    Reset all agent singleton instances.
    Useful for testing and when configuration changes.
    """
    global _delegation_agent, _tone_agents, _twitter_agent, _football_agent, _photo_agent
    
    _delegation_agent = None
    _tone_agents = {}
    _twitter_agent = None
    _football_agent = None
    _photo_agent = None
    
    logger.info("All agent instances reset") 