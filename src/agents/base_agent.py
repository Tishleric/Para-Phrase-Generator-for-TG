# src/agents/base_agent.py
# Base agent class for all agent implementations
"""
This module defines the BaseAgent class, which serves as the foundation
for all agent implementations in the Para-Phrase Generator.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Callable

# Import from centralized SDK imports
from ..sdk_imports import (
    function_tool, SDK_AVAILABLE, OpenAIClient, 
    AgentSDKCompatLayer as Agent
)
from openai import OpenAI
from ..config import DEBUG_MODE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define placeholder types for handoffs and guardrails
class Handoff:
    """Placeholder for Handoff type when SDK is not available."""
    def __init__(self, target, condition):
        self.target = target
        self.condition = condition

class Guardrail:
    """Placeholder for Guardrail type when SDK is not available."""
    def __init__(self, name, condition):
        self.name = name
        self.condition = condition

# No need for placeholder types since they're now in sdk_imports.py

class BaseAgent:
    """
    Base class for all agent implementations.
    
    This class provides common functionality and structure for all agents
    in the Para-Phrase Generator, serving as a wrapper around the OpenAI
    Agents SDK.
    
    Attributes:
        name (str): The name of the agent
        agent (Agent): The OpenAI Agent instance
        client (OpenAI): The OpenAI client
    """
    
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: Optional[List[Callable]] = None,
        handoffs: Optional[List[Handoff]] = None,
        guardrails: Optional[List[Guardrail]] = None
    ):
        """
        Initialize a BaseAgent instance.
        
        Args:
            name (str): The name of the agent
            instructions (str): The instructions for the agent
            model (str): The model to use for the agent
            tools (Optional[List[Callable]]): List of function tools to register
            handoffs (Optional[List[Handoff]]): List of handoffs to other agents
            guardrails (Optional[List[Guardrail]]): List of guardrails for validation
        """
        self.name = name
        self.client = OpenAI()
        
        # Create the agent
        self.agent = Agent(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools or [],
            handoffs=handoffs or [],
            guardrails=guardrails or []
        )
        
        logger.debug(f"Initialized {name} agent using model {model}")
    
    def process(self, input_text: str, **kwargs) -> str:
        """
        Process input with the agent.
        
        Args:
            input_text (str): The input text to process
            **kwargs: Additional arguments to pass to the agent
            
        Returns:
            str: The agent's response
        """
        try:
            logger.debug(f"Processing input with {self.name} agent: {input_text[:50]}...")
            response = self.agent.run(input_text, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error processing input with {self.name} agent: {str(e)}")
            return f"Error processing with {self.name}: {str(e)}"
            
    def add_tool(self, tool: Callable) -> None:
        """
        Add a tool to the agent.
        
        Args:
            tool (Callable): The function tool to add
        """
        self.agent.tools.append(tool)
        logger.debug(f"Added tool {tool.__name__} to {self.name} agent")
        
    def add_handoff(self, handoff: Handoff) -> None:
        """
        Add a handoff to the agent.
        
        Args:
            handoff (Handoff): The handoff to add
        """
        self.agent.handoffs.append(handoff)
        logger.debug(f"Added handoff to {handoff.target.name} for {self.name} agent")
        
    def add_guardrail(self, guardrail: Guardrail) -> None:
        """
        Add a guardrail to the agent.
        
        Args:
            guardrail (Guardrail): The guardrail to add
        """
        self.agent.guardrails.append(guardrail)
        logger.debug(f"Added guardrail to {self.name} agent") 