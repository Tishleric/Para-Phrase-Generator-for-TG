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
    
    logger.debug(f"Generated link: {html_link} for message_id {message_id}")
    
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
    min_phrase_length: int = 4,
    max_phrase_length: int = 30
) -> List[Dict[str, Any]]:
    """
    Find candidate phrases in the summary that could reference original messages.
    
    Args:
        messages (List[Dict[str, Any]]): List of message dictionaries
        summary (str): The summary text
        min_phrase_length (int, optional): Minimum length of phrase to consider.
            Defaults to 4.
        max_phrase_length (int, optional): Maximum length of phrase to consider.
            Defaults to 30.
    
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
        
        # For longer messages, find the most significant phrases
        if len(text) > max_phrase_length:
            # Split into sentences if possible
            sentences = re.split(r'[.!?]', text)
            phrases = [s.strip() for s in sentences if len(s.strip()) >= min_phrase_length]
            
            # If no good sentences, take the first part of the message
            if not phrases:
                phrases = [text[:max_phrase_length]]
        else:
            phrases = [text]
        
        for phrase in phrases:
            # Skip phrases that are too short
            if len(phrase) < min_phrase_length:
                continue
                
            # Check if the phrase is in the summary (case insensitive)
            summary_lower = summary.lower()
            phrase_lower = phrase.lower()
            if phrase_lower in summary_lower:
                # Find the actual case-preserved version in the summary
                index = summary_lower.find(phrase_lower)
                actual_phrase = summary[index:index + len(phrase)]
                
                candidates.append({
                    "message_id": message_id,
                    "phrase": actual_phrase,
                    "full_text": text,
                    "index_in_summary": index
                })
    
    # Sort candidates by their position in the summary
    candidates.sort(key=lambda x: x["index_in_summary"])
    
    # Remove overlapping candidates (prefer longer phrases)
    filtered_candidates = []
    used_ranges = []
    
    for candidate in sorted(candidates, key=lambda x: len(x["phrase"]), reverse=True):
        index = candidate["index_in_summary"]
        end_index = index + len(candidate["phrase"])
        
        # Check if this candidate overlaps with an already used range
        overlap = False
        for start, end in used_ranges:
            if (index <= end and end_index >= start):
                overlap = True
                break
        
        if not overlap:
            filtered_candidates.append(candidate)
            used_ranges.append((index, end_index))
    
    # Sort back by position in summary
    filtered_candidates.sort(key=lambda x: x["index_in_summary"])
    
    return filtered_candidates


def add_links_to_summary(
    summary: str,
    candidates: List[Dict[str, Any]],
    chat_id: str,
    max_links: int = 8
) -> str:
    """
    Add links to the summary for key phrases.
    
    Args:
        summary (str): The summary text
        candidates (List[Dict[str, Any]]): List of candidate references
        chat_id (str): The ID of the chat
        max_links (int, optional): Maximum number of links to add. Defaults to 8.
    
    Returns:
        str: The summary with links added
    """
    if not candidates:
        return summary
    
    # Limit the number of links
    if len(candidates) > max_links:
        # Use an algorithm to distribute links throughout the summary
        summary_length = len(summary)
        segment_size = summary_length // max_links
        
        selected_candidates = []
        for i in range(max_links):
            segment_start = i * segment_size
            segment_end = (i + 1) * segment_size if i < max_links - 1 else summary_length
            
            # Find candidates in this segment
            segment_candidates = [c for c in candidates if segment_start <= c["index_in_summary"] < segment_end]
            
            if segment_candidates:
                # Choose the candidate with the most significant phrase (length is a simple heuristic)
                selected = max(segment_candidates, key=lambda x: len(x["phrase"]))
                selected_candidates.append(selected)
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