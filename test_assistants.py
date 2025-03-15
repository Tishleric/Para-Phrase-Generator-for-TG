"""
Test script for the Assistants API integration.

This script tests the AssistantsManager class to ensure it can create and manage assistants.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from src.assistants import AssistantsManager, WebSearchTool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_assistants_api():
    """
    Test the Assistants API integration.
    """
    logger.info("Testing Assistants API integration...")
    
    # Create an assistants manager
    manager = AssistantsManager()
    
    # Create a test assistant
    assistant = manager.create_assistant(
        name="Test Assistant",
        instructions="You are a test assistant. Your task is to respond with a simple greeting.",
        tools=[],
        model="gpt-4o"
    )
    
    logger.info(f"Created test assistant: {assistant.id}")
    
    # Create a thread
    thread = manager.create_thread()
    
    logger.info(f"Created thread: {thread.id}")
    
    # Add a message to the thread
    manager.add_message(
        thread_id=thread.id,
        role="user",
        content="Hello, assistant!"
    )
    
    logger.info("Added message to thread")
    
    # Run the assistant
    run = await manager.create_run(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    
    logger.info(f"Created run: {run.id}")
    
    # Wait for the run to complete
    run = await manager.wait_for_run(thread_id=thread.id, run_id=run.id)
    
    logger.info(f"Run completed with status: {run.status}")
    
    # Get the response
    response = manager.get_run_content(thread_id=thread.id, run_id=run.id)
    
    logger.info(f"Response: {response}")
    
    # Test web search
    logger.info("Testing web search...")
    
    # Create a web search assistant
    web_search_assistant = manager.create_assistant(
        name="Web Search Test Assistant",
        instructions="You are a web search assistant. Your task is to search for information about the query and provide a concise summary.",
        tools=[WebSearchTool().as_tool()],
        model="gpt-4o"
    )
    
    logger.info(f"Created web search assistant: {web_search_assistant.id}")
    
    # Create a thread for web search
    web_search_thread = manager.create_thread()
    
    logger.info(f"Created web search thread: {web_search_thread.id}")
    
    # Add a message to the thread
    manager.add_message(
        thread_id=web_search_thread.id,
        role="user",
        content="What is the current score of the latest Manchester United match?"
    )
    
    logger.info("Added message to web search thread")
    
    # Run the web search assistant
    web_search_run = await manager.create_run(
        thread_id=web_search_thread.id,
        assistant_id=web_search_assistant.id
    )
    
    logger.info(f"Created web search run: {web_search_run.id}")
    
    # Wait for the run to complete
    web_search_run = await manager.wait_for_run(thread_id=web_search_thread.id, run_id=web_search_run.id)
    
    logger.info(f"Web search run completed with status: {web_search_run.status}")
    
    # Get the response
    web_search_response = manager.get_run_content(thread_id=web_search_thread.id, run_id=web_search_run.id)
    
    logger.info(f"Web search response: {web_search_response}")
    
    logger.info("Assistants API test completed")

if __name__ == "__main__":
    asyncio.run(test_assistants_api()) 