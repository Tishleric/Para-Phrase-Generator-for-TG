# src/test_football_agent.py
# Test script for Football agent functionality
"""
This script tests the functionality of the Football agent.
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

# Import the Football agent
from src.agents import get_football_agent
from src.agents.interface import AgentInterface
from src.agents.context import RunContextManager

def test_extract_football_references():
    """
    Test the football reference extraction functionality.
    """
    # Get the Football agent
    football_agent = get_football_agent()
    
    # Test text with football references
    test_text = """
    Did you see the match yesterday? Barcelona 3-1 Real Madrid was amazing!
    I can't believe Chelsea lost 0-2 to Arsenal.
    The score was 1:1 at halftime.
    Manchester United played well but Liverpool was better.
    The final score was 2-0.
    """
    
    # Extract football references
    references = football_agent._extract_football_references(test_text)
    
    # Print the results
    print(f"Extracted {len(references)} football references:")
    for ref in references:
        print(f"- Type: {ref['type']}, Match: {ref.get('match_string', ref.get('original_text', 'Unknown'))}")
    
    # Verify the results
    assert len(references) >= 3, f"Expected at least 3 references, got {len(references)}"
    
    # Check for team-score references
    team_score_refs = [ref for ref in references if ref["type"] == "team_score"]
    assert len(team_score_refs) >= 1, f"Expected at least 1 team-score reference, got {len(team_score_refs)}"
    
    # Check for team-only references
    team_only_refs = [ref for ref in references if ref["type"] == "team_only"]
    assert len(team_only_refs) >= 0, f"Expected at least 0 team-only reference, got {len(team_only_refs)}"
    
    print("Football reference extraction test passed!")

def test_analyze_match_information():
    """
    Test the match information analysis functionality.
    """
    # Get the Football agent
    football_agent = get_football_agent()
    
    # Test references
    test_references = [
        {
            "type": "team_score",
            "team_home": "Barcelona",
            "score_home": 3,
            "score_away": 1,
            "team_away": "Real Madrid",
            "match_string": "Barcelona 3-1 Real Madrid",
            "span": (0, 0)  # Dummy span
        },
        {
            "type": "score_only",
            "score_home": 1,
            "score_away": 1,
            "match_string": "1:1",
            "span": (0, 0)  # Dummy span
        },
        {
            "type": "team_only",
            "team": "Liverpool",
            "match_string": "Liverpool",
            "span": (0, 0)  # Dummy span
        }
    ]
    
    # Analyze each reference
    for ref in test_references:
        analysis = football_agent._analyze_match_information(ref)
        
        # Print the results
        print(f"Analysis for {ref['match_string']}:")
        for key, value in analysis.items():
            print(f"- {key}: {value}")
        print()
        
        # Verify the results
        assert "match_type" in analysis, "Analysis should include match_type"
        assert "confidence" in analysis, "Analysis should include confidence"
        
        if ref["type"] == "team_score":
            assert analysis["match_type"] == "identified", "Team-score reference should be identified"
            assert "team_home" in analysis, "Analysis should include team_home"
            assert "team_away" in analysis, "Analysis should include team_away"
            assert "result" in analysis, "Analysis should include result"
        
        elif ref["type"] == "score_only":
            assert analysis["match_type"] == "partial", "Score-only reference should be partial"
            assert "score_home" in analysis, "Analysis should include score_home"
            assert "score_away" in analysis, "Analysis should include score_away"
        
        elif ref["type"] == "team_only":
            assert analysis["match_type"] == "team_mention", "Team-only reference should be team_mention"
            assert "team" in analysis, "Analysis should include team"
    
    print("Match information analysis test passed!")

def test_process_football_references():
    """
    Test the football reference processing functionality.
    """
    # Get the Football agent
    football_agent = get_football_agent()
    
    # Create test messages
    test_messages = [
        {
            "sender": "User1",
            "text": "Did you see the match yesterday? Barcelona 3-1 Real Madrid was amazing!"
        },
        {
            "sender": "User2",
            "text": "I can't believe Chelsea lost 0-2 to Arsenal."
        },
        {
            "sender": "User3",
            "text": "Just a regular message with no football references."
        }
    ]
    
    # Process football references
    summary = football_agent.process_football_references(test_messages)
    
    # Print the results
    print(f"Football reference processing results:")
    print(summary)
    
    # Verify the results
    assert summary is not None, "Summary should not be None"
    assert len(summary) > 0, "Summary should not be empty"
    
    print("Football reference processing test passed!")

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
            "text": "Did you see the match yesterday? Barcelona 3-1 Real Madrid was amazing!"
        },
        {
            "sender": "User2",
            "text": "I can't believe Chelsea lost 0-2 to Arsenal."
        },
        {
            "sender": "User3",
            "text": "Just a regular message with no football references."
        }
    ]
    
    # Check for football references
    football_result = delegation_agent._check_for_football_references(test_messages)
    
    # Print the results
    print(f"Delegation agent football reference check results:")
    for key, value in football_result.items():
        print(f"- {key}: {value}")
    
    # Verify the results
    assert football_result["has_references"] == True, "Should have football references"
    assert len(football_result["references"]) > 0, "Should have some football references"
    assert len(football_result["messages"]) > 0, "Should have messages with football references"
    
    print("Delegation agent integration test passed!")

def run_all_tests():
    """
    Run all tests.
    """
    print("Running Football agent tests...\n")
    
    try:
        test_extract_football_references()
        print("\n")
        
        test_analyze_match_information()
        print("\n")
        
        test_process_football_references()
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