"""
Test script for the profile assistant.

This script tests the ProfileAssistant class to ensure it can extract information from messages
and update user profiles.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from src.assistants import ProfileAssistant
from src.vector_store import UserProfileStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_profile_assistant():
    """
    Test the profile assistant.
    """
    logger.info("Testing profile assistant...")
    
    # Create a test directory for the vector store
    test_dir = "test_profile_assistant"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a vector store
    store = UserProfileStore(db_directory=test_dir)
    
    # Create a profile assistant
    assistant = ProfileAssistant(profile_store=store)
    
    # Create test messages
    messages = [
        {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User"
            },
            "text": "I'm a big fan of Manchester United!"
        },
        {
            "message_id": 2,
            "from": {
                "id": 123456789,
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User"
            },
            "text": "I think climate change is a serious issue that needs to be addressed."
        },
        {
            "message_id": 3,
            "from": {
                "id": 123456789,
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User"
            },
            "text": "I'm always late to meetings, it's a bad habit of mine."
        }
    ]
    
    # Process the messages
    await assistant.process_messages(messages)
    
    # Get the user profile
    profile = assistant.get_user_profile("123456789")
    
    if profile:
        logger.info("User profile retrieved successfully:")
        logger.info(f"User ID: {profile['user_id']}")
        logger.info(f"Profile text: {profile['profile_text']}")
        logger.info(f"Metadata: {profile['metadata']}")
    else:
        logger.error("Failed to retrieve user profile")
    
    # Get the user interests
    interests = assistant.get_user_interests("123456789")
    
    if interests:
        logger.info("User interests retrieved successfully:")
        for category, items in interests.items():
            logger.info(f"{category}: {items}")
    else:
        logger.error("Failed to retrieve user interests")
    
    logger.info("Profile assistant test completed")

if __name__ == "__main__":
    asyncio.run(test_profile_assistant()) 