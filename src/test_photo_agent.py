"""
Tests for the Photo Agent.

This module contains tests for the PhotoAgent class, which is responsible
for analyzing image content from Telegram messages.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from typing import Dict, List, Any, Optional

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.photo_agent import PhotoAgent
from src.sdk_imports import SDK_AVAILABLE

class TestPhotoAgent(unittest.TestCase):
    """Test cases for the PhotoAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = PhotoAgent()
        
        # Sample messages with photos
        self.photo_messages = [
            {
                "message_id": 1,
                "from": {"username": "user1"},
                "photo": [
                    {"file_id": "small_photo", "width": 100, "height": 100},
                    {"file_id": "large_photo", "width": 800, "height": 600}
                ],
                "caption": "Check out this photo!"
            },
            {
                "message_id": 2,
                "from": {"username": "user2"},
                "photo": [
                    {"file_id": "small_photo2", "width": 100, "height": 100},
                    {"file_id": "large_photo2", "width": 800, "height": 600}
                ]
            }
        ]
        
        # Sample messages without photos
        self.text_messages = [
            {
                "message_id": 3,
                "from": {"username": "user3"},
                "text": "This is a text message with no photos."
            }
        ]
        
        # Mixed messages
        self.mixed_messages = self.photo_messages + self.text_messages
    
    def test_analyze_image_tool(self):
        """Test the analyze_image_tool method."""
        result = self.agent.analyze_image_tool("https://example.com/image.jpg")
        
        # Check that the result has the expected structure
        self.assertIn("description", result)
        self.assertIn("confidence", result)
        self.assertIn("contains_text", result)
        self.assertIn("is_meme", result)
    
    def test_process_telegram_photos_tool(self):
        """Test the process_telegram_photos_tool method."""
        results = self.agent.process_telegram_photos_tool(self.photo_messages)
        
        # Check that we got the expected number of results
        self.assertEqual(len(results), 2)
        
        # Check that the results have the expected structure
        for result in results:
            self.assertIn("sender", result)
            self.assertIn("message_id", result)
            self.assertIn("caption", result)
            self.assertIn("description", result)
            self.assertIn("analyzed", result)
        
        # Check that the first result has the caption
        self.assertEqual(results[0]["caption"], "Check out this photo!")
        
        # Check that the second result has no caption
        self.assertEqual(results[1]["caption"], "")
    
    def test_process_images_with_photos(self):
        """Test the process_images method with messages containing photos."""
        # Mock the SDK if it's available
        if SDK_AVAILABLE:
            with patch('src.agents.photo_agent.RunContext') as mock_context:
                with patch.object(self.agent.agent, 'run') as mock_run:
                    # Set up the mock to return a result
                    mock_result = MagicMock()
                    mock_result.output.content = "Image 1: A photo of a cat. Image 2: A landscape photo."
                    mock_run.return_value = mock_result
                    
                    result = self.agent.process_images(self.photo_messages)
                    
                    # Check that the agent was called
                    mock_run.assert_called_once()
                    
                    # Check that the result is as expected
                    self.assertEqual(result, "Image 1: A photo of a cat. Image 2: A landscape photo.")
        else:
            # Test the fallback implementation
            result = self.agent.process_images(self.photo_messages)
            
            # Check that the result contains descriptions for both images
            self.assertIn("Image 1:", result)
            self.assertIn("Image 2:", result)
            self.assertIn("user1", result)
            self.assertIn("user2", result)
            self.assertIn("Check out this photo!", result)
    
    def test_process_images_without_photos(self):
        """Test the process_images method with messages not containing photos."""
        result = self.agent.process_images(self.text_messages)
        
        # Should return None when no photos are found
        self.assertIsNone(result)
    
    def test_process_images_with_empty_messages(self):
        """Test the process_images method with an empty message list."""
        result = self.agent.process_images([])
        
        # Should return None when no messages are provided
        self.assertIsNone(result)
    
    def test_process_images_with_mixed_messages(self):
        """Test the process_images method with a mix of photo and text messages."""
        # Mock the SDK if it's available
        if SDK_AVAILABLE:
            with patch('src.agents.photo_agent.RunContext') as mock_context:
                with patch.object(self.agent.agent, 'run') as mock_run:
                    # Set up the mock to return a result
                    mock_result = MagicMock()
                    mock_result.output.content = "Image 1: A photo of a cat. Image 2: A landscape photo."
                    mock_run.return_value = mock_result
                    
                    result = self.agent.process_images(self.mixed_messages)
                    
                    # Check that the agent was called
                    mock_run.assert_called_once()
                    
                    # Check that the result is as expected
                    self.assertEqual(result, "Image 1: A photo of a cat. Image 2: A landscape photo.")
        else:
            # Test the fallback implementation
            result = self.agent.process_images(self.mixed_messages)
            
            # Check that the result contains descriptions for both images
            self.assertIn("Image 1:", result)
            self.assertIn("Image 2:", result)
            self.assertIn("user1", result)
            self.assertIn("user2", result)
            self.assertIn("Check out this photo!", result)

if __name__ == '__main__':
    unittest.main() 