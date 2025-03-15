"""
Telegram Bridge for the Para-Phrase Generator

This module provides a bridge between the Telegram bot and the Assistants API implementation.
It handles message storage, command routing, and summary generation.
"""

import re
import os
import logging
import traceback
import asyncio
from typing import Dict, List, Optional, Any, Union
import json

from .config import (
    DEBUG_MODE, USE_AGENT_SYSTEM, MAX_MESSAGES_PER_CHAT,
    AVAILABLE_TONES, DEFAULT_TONE
)
from .assistants import DelegationAssistant
from .assistants.linking import create_message_mapping, find_reference_candidates, add_links_to_summary

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_error_message(error: Exception) -> str:
    """
    Format an error message for the user.
    
    Args:
        error (Exception): The error to format
    
    Returns:
        str: Formatted error message
    """
    if DEBUG_MODE:
        return f"Error: {str(error)}\n\n{traceback.format_exc()}"
    else:
        return f"An error occurred: {str(error)}"


class TelegramBridge:
    """
    Bridge class to handle communication between the Telegram bot and the Assistants API.
    
    This class provides methods for storing messages, handling commands, and generating
    summaries using the Assistants API implementation.
    
    Attributes:
        chat_history (Dict[str, List[Dict[str, Any]]]): Dictionary of chat histories
        chat_tones (Dict[str, str]): Dictionary of chat tones
        delegation_assistant (DelegationAssistant): The delegation assistant instance
    """
    
    def __init__(
        self, 
        chat_history: Optional[Dict[str, List[Dict[str, Any]]]] = None, 
        chat_tones: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the TelegramBridge.
        
        Args:
            chat_history (Optional[Dict[str, List[Dict[str, Any]]]], optional): Dictionary of
                chat histories. Defaults to None, which creates a new empty dictionary.
            chat_tones (Optional[Dict[str, str]], optional): Dictionary of chat tones.
                Defaults to None, which creates a new empty dictionary.
        """
        self.chat_history = chat_history or {}
        self.chat_tones = chat_tones or {}
        self.delegation_assistant = None
        
        # Only initialize the delegation assistant if USE_AGENT_SYSTEM is True
        if USE_AGENT_SYSTEM:
            try:
                self.delegation_assistant = DelegationAssistant()
                logger.info("TelegramBridge initialized with delegation assistant")
            except Exception as e:
                logger.error(f"Failed to initialize delegation assistant: {e}")
                logger.error(traceback.format_exc())
                logger.warning("TelegramBridge initialized without delegation assistant")
        else:
            logger.info("TelegramBridge initialized without delegation assistant (agent system disabled)")
    
    def get_chat_tone(self, chat_id: Union[str, int]) -> str:
        """
        Get the tone for a specific chat.
        
        Args:
            chat_id (Union[str, int]): Chat ID
            
        Returns:
            str: The chat tone
        """
        # Convert chat_id to string if it's an integer
        chat_id_str = str(chat_id)
        
        # Return the tone for the chat, or the default tone if not set
        return self.chat_tones.get(chat_id_str, DEFAULT_TONE)
    
    def set_chat_tone(self, chat_id: Union[str, int], tone: str) -> None:
        """
        Set the tone for a specific chat.
        
        Args:
            chat_id (Union[str, int]): Chat ID
            tone (str): Tone to set
        """
        # Convert chat_id to string if it's an integer
        chat_id_str = str(chat_id)
        
        # Set the tone for the chat
        self.chat_tones[chat_id_str] = tone
        logger.info(f"Set tone for chat {chat_id_str} to {tone}")
    
    def get_message_history(
        self, 
        chat_id: Union[str, int], 
        count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get the message history for a specific chat.
        
        Args:
            chat_id (Union[str, int]): Chat ID
            count (Optional[int]): Number of messages to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of message dictionaries
        """
        # Convert chat_id to string if it's an integer
        chat_id_str = str(chat_id)
        
        # Get the message history for the chat
        messages = self.chat_history.get(chat_id_str, [])
        
        # Return the requested number of messages, or all messages if count is None
        if count is not None and count > 0:
            return messages[-count:]
        return messages
    
    def store_message(self, message: Dict[str, Any]) -> None:
        """
        Store a message in the chat history.
        
        Args:
            message (Dict[str, Any]): Message dictionary
        """
        try:
            # Check if this is a proper dictionary or a message object
            if isinstance(message, dict):
                # It's already a dictionary
                chat = message.get('chat', {})
                if isinstance(chat, dict):
                    chat_id = str(chat.get('id', ''))
                else:
                    # The chat might be an object
                    chat_id = str(getattr(chat, 'id', ''))
            else:
                # It's likely a message object that was converted to dict incorrectly
                # Try to get the chat_id directly from the object
                chat = getattr(message, 'chat', None)
                if chat:
                    chat_id = str(getattr(chat, 'id', ''))
                else:
                    logger.warning("Message has no chat attribute, skipping")
                    return
            
            if not chat_id:
                logger.warning("Message has no chat ID, skipping")
                return
            
            # Convert to dictionary if it's not already
            if not isinstance(message, dict):
                # Extract key attributes manually
                message_dict = {
                    'message_id': getattr(message, 'message_id', None),
                    'from_user': {
                        'id': getattr(getattr(message, 'from_user', None), 'id', None),
                        'username': getattr(getattr(message, 'from_user', None), 'username', None),
                    },
                    'chat': {
                        'id': chat_id,
                        'type': getattr(chat, 'type', None),
                        'title': getattr(chat, 'title', None),
                    },
                    'date': getattr(message, 'date', None),
                    'text': getattr(message, 'text', None),
                }
                
                # Check for photo
                if hasattr(message, 'photo') and message.photo:
                    message_dict['photo'] = [
                        {
                            'file_id': photo.file_id,
                            'file_unique_id': photo.file_unique_id,
                            'width': photo.width,
                            'height': photo.height,
                            'file_size': getattr(photo, 'file_size', None)
                        }
                        for photo in message.photo
                    ]
                
                # Use message_dict instead of message
                message = message_dict
        
            # Initialize chat history for this chat if it doesn't exist
            if chat_id not in self.chat_history:
                self.chat_history[chat_id] = []
            
            # Add the message to the chat history
            self.chat_history[chat_id].append(message)
            
            # Trim the chat history if it's too long
            if len(self.chat_history[chat_id]) > MAX_MESSAGES_PER_CHAT:
                self.chat_history[chat_id] = self.chat_history[chat_id][-MAX_MESSAGES_PER_CHAT:]
                
        except Exception as e:
            logger.error(f"Error in store_message: {e}")
            logger.error(traceback.format_exc())
    
    async def handle_command_async(
        self, 
        message: Dict[str, Any], 
        command: str, 
        args: List[str]
    ) -> Optional[str]:
        """
        Handle a command from a Telegram message asynchronously.
        
        Args:
            message (Dict[str, Any]): Message dictionary
            command (str): Command to handle
            args (List[str]): Command arguments
            
        Returns:
            Optional[str]: Response to send, or None if no response
        """
        # Get the chat ID from the message
        chat_id = str(message.get('chat', {}).get('id', ''))
        
        if not chat_id:
            logger.warning("Message has no chat ID, skipping")
            return None
        
        # Skip agent processing if disabled
        if not USE_AGENT_SYSTEM or not self.delegation_assistant:
            logger.info("Agent system is disabled or delegation assistant is not initialized, skipping")
            return None
        
        try:
            # Handle tone command
            if command == "/tone" and args:
                tone = args[0].lower()
                
                # Validate the tone
                if tone not in AVAILABLE_TONES:
                    return f"Invalid tone. Available tones: {', '.join(AVAILABLE_TONES)}"
                
                # Set the tone for the chat
                self.set_chat_tone(chat_id, tone)
                return f"Tone set to {tone}!"
            
            # Handle last command
            elif command == "/last" and args:
                try:
                    # Parse the count argument
                    count = int(args[0])
                    
                    # Validate the count
                    if count <= 0:
                        return "Please specify a positive number of messages to summarize."
                    
                    # Get the message history
                    messages = self.get_message_history(chat_id, count)
                    
                    if not messages:
                        return "No messages to summarize."
                    
                    # Get the tone for the chat
                    tone = self.get_chat_tone(chat_id)
                    
                    # Create a message mapping for linking
                    message_mapping = create_message_mapping(messages)
                    
                    # Process the request using the delegation assistant
                    summary = await self.delegation_assistant.process_summary_request(
                        messages=messages,
                        tone=tone,
                        message_mapping=message_mapping
                    )
                    
                    # Add links to the summary
                    candidates = find_reference_candidates(messages, summary)
                    linked_summary = add_links_to_summary(summary, candidates, chat_id)
                    
                    return linked_summary
                    
                except ValueError:
                    return "Please specify a valid number of messages to summarize."
            
            # Unknown command or missing arguments
            return None
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            logger.error(traceback.format_exc())
            return format_error_message(e)
    
    def handle_command(
        self, 
        message: Dict[str, Any], 
        command: str, 
        args: List[str]
    ) -> Optional[str]:
        """
        Handle a command from a Telegram message.
        
        Args:
            message (Dict[str, Any]): Message dictionary
            command (str): Command to handle
            args (List[str]): Command arguments
            
        Returns:
            Optional[str]: Response to send, or None if no response
        """
        # Run the async handler in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.handle_command_async(message, command, args))
        finally:
            loop.close() 