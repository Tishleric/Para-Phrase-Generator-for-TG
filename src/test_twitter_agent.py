# src/test_twitter_agent.py
# Test script for Twitter agent functionality
"""
This script tests the functionality of the Twitter agent.
"""

import logging
import sys
import os
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Twitter agent
from src.agents import get_twitter_agent
from src.agents.interface import AgentInterface
from src.agents.context import RunContextManager

def test_extract_twitter_links():
    """
    Test the Twitter link extraction functionality.
    """
    # Get the Twitter agent
    twitter_agent = get_twitter_agent()
    
    # Test text with Twitter links
    test_text = """
    Check out this tweet: https://twitter.com/OpenAI/status/1234567890
    And this one from X: https://x.com/user/status/9876543210
    And a regular URL: https://example.com
    """
    
    # Extract Twitter links
    links = twitter_agent._extract_twitter_links(test_text)
    
    # Print the results
    print(f"Extracted {len(links)} Twitter links:")
    for link in links:
        print(f"- {link}")
    
    # Verify the results
    assert len(links) == 2, f"Expected 2 links, got {len(links)}"
    
    # Strip whitespace from links for comparison
    cleaned_links = [link.strip() for link in links]
    assert "https://twitter.com/OpenAI/status/1234567890" in cleaned_links, "Missing Twitter link"
    assert "https://x.com/user/status/9876543210" in cleaned_links, "Missing X link"
    
    print("Twitter link extraction test passed!")

def test_analyze_tweet_content():
    """
    Test the tweet content analysis functionality.
    """
    # Get the Twitter agent
    twitter_agent = get_twitter_agent()
    
    # Test URL
    test_url = "https://twitter.com/OpenAI/status/1234567890"
    
    # Analyze tweet content
    analysis = twitter_agent._analyze_tweet_content(test_url)
    
    # Print the results
    print(f"Tweet analysis results:")
    for key, value in analysis.items():
        print(f"- {key}: {value}")
    
    # Verify the results
    assert analysis["url"] == test_url, "URL mismatch"
    assert analysis["username"] == "OpenAI", "Username mismatch"
    assert analysis["tweet_id"] == "1234567890", "Tweet ID mismatch"
    
    print("Tweet content analysis test passed!")

def test_process_twitter_links():
    """
    Test the Twitter link processing functionality.
    """
    # Get the Twitter agent
    twitter_agent = get_twitter_agent()
    
    # Create test messages
    test_messages = [
        {
            "sender": "User1",
            "text": "Check out this tweet: https://twitter.com/OpenAI/status/1234567890"
        },
        {
            "sender": "User2",
            "text": "And this one from X: https://x.com/user/status/9876543210"
        },
        {
            "sender": "User3",
            "text": "Just a regular message with no links."
        }
    ]
    
    # Process Twitter links
    summary = twitter_agent.process_twitter_links(test_messages)
    
    # Print the results
    print(f"Twitter link processing results:")
    print(summary)
    
    # Verify the results
    assert summary is not None, "Summary should not be None"
    assert len(summary) > 0, "Summary should not be empty"
    
    print("Twitter link processing test passed!")

def test_delegation_agent_integration():
    """
    Test the integration with the delegation agent.
    """
    # Import the delegation agent
    from src.agents import get_delegation_agent
    
    # Get the delegation agent
    delegation_agent = get_delegation_agent()
    
    # Create test messages
    test_messages = [
        {
            "sender": "User1",
            "text": "Check out this tweet: https://twitter.com/OpenAI/status/1234567890"
        },
        {
            "sender": "User2",
            "text": "And this one from X: https://x.com/user/status/9876543210"
        },
        {
            "sender": "User3",
            "text": "Just a regular message with no links."
        }
    ]
    
    # Check for Twitter links
    twitter_result = delegation_agent._check_for_twitter_links(test_messages)
    
    # Print the results
    print(f"Delegation agent Twitter link check results:")
    for key, value in twitter_result.items():
        print(f"- {key}: {value}")
    
    # Verify the results
    assert twitter_result["has_links"] == True, "Should have Twitter links"
    assert len(twitter_result["links"]) == 2, f"Expected 2 links, got {len(twitter_result['links'])}"
    assert len(twitter_result["messages"]) == 2, "Should have 2 messages with links"
    
    print("Delegation agent integration test passed!")

def run_all_tests():
    """
    Run all tests.
    """
    print("Running Twitter agent tests...\n")
    
    try:
        test_extract_twitter_links()
        print("\n")
        
        test_analyze_tweet_content()
        print("\n")
        
        test_process_twitter_links()
        print("\n")
        
        test_delegation_agent_integration()
        print("\n")
        
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    run_all_tests() 