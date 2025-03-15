"""
Message Linking Utilities

This module provides utilities for generating Telegram message links and tracking
message references in summaries.
"""

import re
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_telegram_link(chat_id: str, message_id: int, text: str) -> str:
    """
    Generate a Telegram message link.
    
    Args:
        chat_id (str): The ID of the chat (can be username for public chats)
        message_id (int): The ID of the message
        text (str): The text to display for the link
    
    Returns:
        str: An HTML link to the Telegram message
    """
    # For private chats, chat_id is numeric and requires the c/ prefix
    if chat_id.startswith('-') or chat_id.isdigit():
        link_chat_id = f"c/{chat_id.lstrip('-')}"
    else:
        # For public chats, chat_id can be a username
        link_chat_id = chat_id
    
    # Generate the link
    link = f"https://t.me/{link_chat_id}/{message_id}"
    
    # Create an HTML link
    html_link = f'<a href="{link}">{text}</a>'
    
    return html_link


def create_message_mapping(messages: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Create a mapping of message IDs to message objects.
    
    Args:
        messages (List[Dict[str, Any]]): List of message dictionaries
    
    Returns:
        Dict[int, Dict[str, Any]]: A mapping of message IDs to message objects
    """
    mapping = {}
    
    for message in messages:
        message_id = message.get("message_id")
        if message_id:
            mapping[message_id] = message
    
    return mapping


def find_reference_candidates(
    messages: List[Dict[str, Any]],
    summary: str,
    min_phrase_length: int = 5
) -> List[Dict[str, Any]]:
    """
    Find candidate phrases in the summary that could reference original messages.
    
    Args:
        messages (List[Dict[str, Any]]): List of message dictionaries
        summary (str): The summary text
        min_phrase_length (int, optional): Minimum length of phrase to consider.
            Defaults to 5.
    
    Returns:
        List[Dict[str, Any]]: List of candidate references
    """
    candidates = []
    
    # Extract the text from each message
    for message in messages:
        message_id = message.get("message_id")
        text = message.get("text", "")
        
        if not text or len(text) < min_phrase_length:
            continue
        
        # Look for phrases that are at least min_phrase_length characters
        for i in range(len(text) - min_phrase_length + 1):
            phrase = text[i:i + min_phrase_length]
            
            # Check if the phrase is in the summary
            if phrase in summary:
                candidates.append({
                    "message_id": message_id,
                    "phrase": phrase,
                    "full_text": text,
                    "index_in_summary": summary.find(phrase)
                })
    
    # Sort candidates by their position in the summary
    candidates.sort(key=lambda x: x["index_in_summary"])
    
    return candidates


def add_links_to_summary(
    summary: str,
    candidates: List[Dict[str, Any]],
    chat_id: str,
    max_links: int = 5
) -> str:
    """
    Add links to the summary for key phrases.
    
    Args:
        summary (str): The summary text
        candidates (List[Dict[str, Any]]): List of candidate references
        chat_id (str): The ID of the chat
        max_links (int, optional): Maximum number of links to add. Defaults to 5.
    
    Returns:
        str: The summary with links added
    """
    if not candidates:
        return summary
    
    # Limit the number of links
    if len(candidates) > max_links:
        # Use a simple algorithm to distribute links throughout the summary
        step = len(candidates) // max_links
        selected_candidates = candidates[::step][:max_links]
    else:
        selected_candidates = candidates
    
    # Add links to the summary, starting from the end to avoid shifting indices
    linked_summary = summary
    for candidate in reversed(selected_candidates):
        message_id = candidate["message_id"]
        phrase = candidate["phrase"]
        index = candidate["index_in_summary"]
        
        # Generate the link
        link = generate_telegram_link(chat_id, message_id, phrase)
        
        # Replace the phrase with the link
        linked_summary = linked_summary[:index] + link + linked_summary[index + len(phrase):]
    
    return linked_summary 