#!/usr/bin/env python
"""
Test script to verify that the OpenAI Agents SDK is properly installed and working.
"""

import os
import asyncio
import logging
import pytest
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_direct_import():
    """Test direct import of OpenAI Agents SDK."""
    logger.info("Testing direct import of OpenAI Agents SDK...")
    try:
        from agents import Agent, Runner, set_default_openai_key
        logger.info("SUCCESS: Basic OpenAI Agents SDK components imported directly.")
        
        # Test API key setting
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            set_default_openai_key(api_key)
            logger.info(f"SUCCESS: API key set (prefix: {api_key[:5]}...)")
        else:
            logger.warning("WARNING: No API key found in environment variables.")
            
        return True
    except ImportError as e:
        logger.error(f"ERROR: Failed to import OpenAI Agents SDK directly: {str(e)}")
        return False

def test_project_import():
    """Test import of OpenAI Agents SDK through project's sdk_imports module."""
    logger.info("Testing import of OpenAI Agents SDK through project's sdk_imports module...")
    try:
        from src.sdk_imports import Agent, Runner, SDK_AVAILABLE
        if SDK_AVAILABLE:
            logger.info("SUCCESS: OpenAI Agents SDK imported through project's sdk_imports module.")
        else:
            logger.warning("WARNING: OpenAI Agents SDK not available through project's sdk_imports module. Using mock implementations.")
        return SDK_AVAILABLE
    except ImportError as e:
        logger.error(f"ERROR: Failed to import OpenAI Agents SDK through project's sdk_imports module: {str(e)}")
        return False

@pytest.mark.asyncio
async def test_agent_creation():
    """Test creation and running of a simple agent."""
    logger.info("Testing creation and running of a simple agent...")
    try:
        from agents import Agent, Runner
        
        # Create a simple agent
        agent = Agent(
            name="Test Agent",
            instructions="You are a test agent that responds with 'Hello, world!'.",
            model="gpt-3.5-turbo"
        )
        
        # Run the agent
        logger.info("Running the agent...")
        result = await Runner.run(agent, "Say hello")
        
        # Check the result
        logger.info(f"Agent response: {result.final_output}")
        return True
    except Exception as e:
        logger.error(f"ERROR: Failed to create and run agent: {str(e)}")
        return False

def test_inspect_api():
    """Test inspection of the OpenAI Agents SDK API."""
    logger.info("Inspecting OpenAI Agents SDK API...")
    try:
        import agents
        
        # Print available modules and classes
        dir_results = dir(agents)
        logger.info(f"Available in agents module: {', '.join(name for name in dir_results if not name.startswith('_'))}")
        
        # Try to import specific components to see what's actually available
        try:
            from agents import Tracing
            logger.info("Tracing is available")
        except ImportError:
            logger.info("Tracing is NOT available")
            
        try:
            from agents.run_context import RunContext
            logger.info("RunContext is available")
        except ImportError:
            logger.info("RunContext is NOT available")
            
        return True
    except Exception as e:
        logger.error(f"ERROR: Failed to inspect API: {str(e)}")
        return False

async def main():
    """Run all tests."""
    logger.info("Starting OpenAI Agents SDK tests...")
    
    # Test API inspection
    test_inspect_api()
    
    # Test direct import
    direct_import_success = test_direct_import()
    
    # Test project import
    project_import_success = test_project_import()
    
    # Test agent creation
    agent_creation_success = False
    if direct_import_success:
        agent_creation_success = await test_agent_creation()
    
    # Print summary
    logger.info("-" * 80)
    logger.info("Test Summary:")
    logger.info(f"Direct Import: {'SUCCESS' if direct_import_success else 'FAILURE'}")
    logger.info(f"Project Import: {'SUCCESS' if project_import_success else 'FAILURE'}")
    logger.info(f"Agent Creation and Running: {'SUCCESS' if agent_creation_success else 'FAILURE'}")
    logger.info("-" * 80)
    
    if direct_import_success and project_import_success and agent_creation_success:
        logger.info("All tests passed successfully!")
    else:
        logger.warning("Some tests failed. Please check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main()) 