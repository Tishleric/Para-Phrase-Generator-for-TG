"""
Test script for the vector store implementation.

This script tests the UserProfileStore class to ensure it can store and retrieve user profiles.
"""

import os
import logging
from dotenv import load_dotenv
from src.vector_store import UserProfileStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vector_store():
    """
    Test the vector store implementation.
    """
    logger.info("Testing vector store...")
    
    # Create a test directory
    test_dir = "test_vector_store"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a vector store
    store = UserProfileStore(db_directory=test_dir)
    
    # Add a test user
    store.add_or_update_user(
        user_id="123456789",
        username="testuser",
        first_name="Test",
        last_name="User",
        profile_text="This is a test user profile."
    )
    
    # Add some information to the user profile
    store.add_user_information(
        user_id="123456789",
        information="Manchester United",
        category="sports_team"
    )
    
    store.add_user_information(
        user_id="123456789",
        information="I think climate change is a serious issue",
        category="opinion"
    )
    
    store.add_user_information(
        user_id="123456789",
        information="I'm always late to meetings",
        category="personality"
    )
    
    # Get the user profile
    profile = store.get_user_profile("123456789")
    
    if profile:
        logger.info("User profile retrieved successfully:")
        logger.info(f"User ID: {profile['user_id']}")
        logger.info(f"Profile text: {profile['profile_text']}")
        logger.info(f"Metadata: {profile['metadata']}")
    else:
        logger.error("Failed to retrieve user profile")
    
    # Get the user interests
    interests = store.extract_user_interests("123456789")
    
    if interests:
        logger.info("User interests retrieved successfully:")
        for category, items in interests.items():
            logger.info(f"{category}: {items}")
    else:
        logger.error("Failed to retrieve user interests")
    
    logger.info("Vector store test completed")

if __name__ == "__main__":
    test_vector_store() 