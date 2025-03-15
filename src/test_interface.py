# src/test_interface.py
# Test script for the agent interface and context management components
"""
This script tests the functionality of the AgentInterface and RunContextManager
classes to ensure they work as expected with the OpenAI Agents SDK.
"""

import os
import sys
import json
import asyncio
import logging
import pytest
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SDK imports using the centralized sdk_imports module
from src.sdk_imports import Agent, ModelSettings, set_default_openai_key, SDK_AVAILABLE

# Local imports
from src.agents import get_agent_classes

# Get agent classes
agent_classes = get_agent_classes()
AgentInterface = agent_classes['AgentInterface']
BotContext = agent_classes['BotContext']
RunContextManager = agent_classes['RunContextManager']

from src.config import DEBUG_MODE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set OpenAI API key from environment
set_default_openai_key(os.environ.get("OPENAI_API_KEY"))

def create_test_agent() -> Agent:
    """
    Create a simple test agent for validation.
    
    Returns:
        Agent: A basic test agent
    """
    return Agent(
        name="Test Agent",
        instructions="You are a test agent for validating the interface.",
        model="gpt-3.5-turbo",
        model_settings=ModelSettings(
            temperature=0.7,
            max_tokens=256,
        )
    )

@pytest.mark.asyncio
async def test_agent_interface():
    """Test the AgentInterface class with a simple agent."""
    logger.info("Testing AgentInterface...")
    
    # Create an agent interface
    interface = AgentInterface(
        max_retries=2,
        retry_delay=1.0,
        tracing_enabled=True
    )
    
    # Create a test agent
    agent = create_test_agent()
    
    # Create a run configuration
    run_config = interface.create_run_config(
        workflow_name="Test Workflow",
        temperature=0.5,
        max_tokens=150
    )
    
    # Test the agent with a simple query
    try:
        logger.info("Running agent with a simple query...")
        response = await interface.run_agent(
            agent=agent,
            input_text="Summarize the key features of the Python programming language in 2-3 sentences.",
            run_config=run_config
        )
        
        logger.info(f"Agent response: {response}")
        
        # Test with an intentional error (e.g., too many turns)
        logger.info("Testing error handling with a very small max_turns...")
        response = await interface.run_agent(
            agent=agent,
            input_text="What is the meaning of life?",
            max_turns=1,  # Intentionally small to test error handling
            run_config=run_config
        )
        
        logger.info(f"Error handling response: {response}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing agent interface: {str(e)}")
        return False

def test_context_manager():
    """Test the RunContextManager class."""
    logger.info("Testing RunContextManager...")
    
    # Create a context manager
    context_manager = RunContextManager()
    
    # Create a test context
    context_id = "test_chat_123"
    context = context_manager.create_context(
        context_id=context_id,
        chat_id=123,
        user_id=456,
        tone="chaotic"
    )
    
    # Test context retrieval
    retrieved_context = context_manager.get_context(context_id)
    if retrieved_context is None:
        logger.error("Failed to retrieve context")
        return False
    
    # Test context update
    updated_context = context_manager.update_context(
        context_id=context_id,
        tone="pubbie"
    )
    if updated_context is None or updated_context.tone != "pubbie":
        logger.error("Failed to update context")
        return False
    
    # Test JSON serialization
    json_str = context.to_json()
    logger.info(f"Serialized context: {json_str}")
    
    # Test JSON deserialization
    deserialized = BotContext.from_json(json_str)
    if deserialized.chat_id != context.chat_id or deserialized.tone != context.tone:
        logger.error("Failed to deserialize context")
        return False
    
    # Test message addition
    context.add_message({
        "sender": "Alice",
        "text": "Hello, everyone!"
    })
    if len(context.message_history) != 1:
        logger.error("Failed to add message to context")
        return False
    
    # Test context deletion
    if not context_manager.delete_context(context_id):
        logger.error("Failed to delete context")
        return False
    
    # Verify context was deleted
    if context_manager.get_context(context_id) is not None:
        logger.error("Context was not properly deleted")
        return False
    
    logger.info("RunContextManager tests passed!")
    return True

async def run_tests():
    """Run all tests."""
    logger.info("Starting tests...")
    
    # Test the agent interface
    interface_result = await test_agent_interface()
    
    # Test the context manager
    context_result = test_context_manager()
    
    # Report results
    if interface_result and context_result:
        logger.info("All tests passed!")
    else:
        logger.error("Some tests failed!")

if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # Run the tests
    asyncio.run(run_tests()) 