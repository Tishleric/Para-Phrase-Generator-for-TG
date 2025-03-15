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
    AVAILABLE_TONES, DEFAULT_TONE, ADD_MESSAGE_LINKS
)
from .assistants import DelegationAssistant, ProfileAssistant
from .assistants.linking import create_message_mapping, find_reference_candidates, add_links_to_summary
from .vector_store import UserProfileStore

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
        profile_assistant (ProfileAssistant): The profile assistant instance
        profile_store (UserProfileStore): The user profile store
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
        self.profile_assistant = None
        self.profile_store = UserProfileStore()
        
        # Only initialize the assistants if USE_AGENT_SYSTEM is True
        if USE_AGENT_SYSTEM:
            try:
                self.delegation_assistant = DelegationAssistant()
                self.profile_assistant = ProfileAssistant(profile_store=self.profile_store)
                logger.info("TelegramBridge initialized with delegation and profile assistants")
            except Exception as e:
                logger.error(f"Failed to initialize assistants: {e}")
                logger.error(traceback.format_exc())
                logger.warning("TelegramBridge initialized without assistants")
        else:
            logger.info("TelegramBridge initialized without assistants (agent system disabled)")
    
    def get_chat_tone(self, chat_id: Union[str, int]) -> str:
        """
        Get the tone for a specific chat.
        
        Args:
            chat_id (Union[str, int]): Chat ID
            
        Returns:
            str: The chat tone
        """
        # Convert chat_id to string if it's an integer
        chat_id = str(chat_id)
        
        # Return the tone for this chat, or the default tone if not set
        return self.chat_tones.get(chat_id, DEFAULT_TONE)
    
    def set_chat_tone(self, chat_id: Union[str, int], tone: str) -> bool:
        """
        Set the tone for a specific chat.
        
        Args:
            chat_id (Union[str, int]): Chat ID
            tone (str): The tone to set
            
        Returns:
            bool: True if the tone was set successfully, False otherwise
        """
        # Convert chat_id to string if it's an integer
        chat_id = str(chat_id)
        
        # Check if the tone is valid
        if tone not in AVAILABLE_TONES:
            return False
        
        # Set the tone
        self.chat_tones[chat_id] = tone
        return True
    
    def store_message(self, message: Dict[str, Any]) -> None:
        """
        Store a message in the chat history.
        
        Args:
            message (Dict[str, Any]): The message to store
        """
        # Extract the chat ID
        chat_id = str(message.get("chat", {}).get("id", "unknown"))
        
        # Initialize the chat history for this chat if it doesn't exist
        if chat_id not in self.chat_history:
            self.chat_history[chat_id] = []
        
        # Add the message to the chat history
        self.chat_history[chat_id].append(message)
        
        # Limit the number of messages stored
        if len(self.chat_history[chat_id]) > MAX_MESSAGES_PER_CHAT:
            self.chat_history[chat_id] = self.chat_history[chat_id][-MAX_MESSAGES_PER_CHAT:]
        
        # Process the message for user profile updates
        if self.profile_assistant:
            # Initialize the user profile if it doesn't exist
            if "from" in message and message["from"]:
                self.profile_assistant.initialize_user_from_telegram(message["from"])
            
            # Process the message asynchronously
            asyncio.create_task(self._process_message_for_profile(message))
    
    async def _process_message_for_profile(self, message: Dict[str, Any]) -> None:
        """
        Process a message for user profile updates.
        
        Args:
            message (Dict[str, Any]): The message to process
        """
        if not self.profile_assistant:
            return
        
        try:
            # Process the message
            await self.profile_assistant.process_messages([message])
        except Exception as e:
            logger.error(f"Error processing message for profile: {e}")
            logger.error(traceback.format_exc())
    
    async def handle_command(
        self,
        message: Dict[str, Any],
        command: str,
        args: List[str]
    ) -> Optional[str]:
        """
        Handle a command from the user.
        
        Args:
            message (Dict[str, Any]): The message containing the command
            command (str): The command name
            args (List[str]): The command arguments
            
        Returns:
            Optional[str]: The response to the command, or None if the command
                was not handled
        """
        # Check if the agent system is enabled
        if not USE_AGENT_SYSTEM or not self.delegation_assistant:
            return None
        
        # Handle the command
        if command == "tone":
            return await self._handle_tone_command(message, args)
        elif command == "last":
            return await self._handle_last_command(message, args)
        elif command == "profile":
            return await self._handle_profile_command(message, args)
        
        return None
    
    async def _handle_tone_command(
        self,
        message: Dict[str, Any],
        args: List[str]
    ) -> Optional[str]:
        """
        Handle the /tone command.
        
        Args:
            message (Dict[str, Any]): The message containing the command
            args (List[str]): The command arguments
            
        Returns:
            Optional[str]: The response to the command, or None if the command
                was not handled
        """
        if not args:
            return f"Please specify a tone. Available tones: {', '.join(AVAILABLE_TONES)}"
        
        tone = args[0].lower()
        
        if tone not in AVAILABLE_TONES:
            return f"Invalid tone. Available tones: {', '.join(AVAILABLE_TONES)}"
        
        chat_id = str(message.get("chat", {}).get("id", "unknown"))
        self.chat_tones[chat_id] = tone
        
        return f"Tone set to {tone}!"
    
    async def _handle_last_command(
        self,
        message: Dict[str, Any],
        args: List[str]
    ) -> Optional[str]:
        """
        Handle the /last command.
        
        Args:
            message (Dict[str, Any]): The message dictionary
            args (List[str]): Command arguments (number of messages to summarize)
        
        Returns:
            Optional[str]: Summary of the last N messages, or None if error
        """
        try:
            # Parse the message count
            if not args:
                return "Please specify the number of messages to summarize."
            
            try:
                count = int(args[0])
            except ValueError:
                return "Please specify a valid number of messages to summarize."
            
            if count <= 0:
                return "Please specify a positive number of messages to summarize."
            
            # Get the chat ID
            chat_id = str(message.get("chat", {}).get("id", ""))
            
            # Get the messages to summarize
            if chat_id not in self.chat_history or not self.chat_history[chat_id]:
                return "No messages to summarize."
            
            # Get the most recent N messages
            messages_to_summarize = self.chat_history[chat_id][-count:]
            
            # Get the chat tone
            tone = self.get_chat_tone(chat_id)
            
            # Always create a mapping of message IDs to messages for linking
            message_mapping = create_message_mapping(messages_to_summarize)
            
            # Get the delegation assistant
            delegation_assistant = DelegationAssistant()
            
            # Process the summary request
            summary = await delegation_assistant.process_summary_request(
                messages_to_summarize,
                tone,
                message_mapping
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error handling /last command: {e}")
            logger.error(traceback.format_exc())
            return format_error_message(e)
    
    async def _handle_profile_command(
        self,
        message: Dict[str, Any],
        args: List[str]
    ) -> Optional[str]:
        """
        Handle the /profile command.
        
        Args:
            message (Dict[str, Any]): The message containing the command
            args (List[str]): The command arguments
            
        Returns:
            Optional[str]: The response to the command, or None if the command
                was not handled
        """
        if not self.profile_assistant:
            return "Profile assistant is not available."
        
        # Get the user ID
        user_id = None
        
        if args:
            # Try to parse the user ID from the arguments
            try:
                user_id = int(args[0])
            except ValueError:
                # Check if it's a username
                username = args[0].lstrip('@')
                
                # Look for the user in the chat history
                chat_id = str(message.get("chat", {}).get("id", "unknown"))
                if chat_id in self.chat_history:
                    for msg in self.chat_history[chat_id]:
                        if msg.get("from", {}).get("username") == username:
                            user_id = msg.get("from", {}).get("id")
                            break
        else:
            # Use the sender's user ID
            user_id = message.get("from", {}).get("id")
        
        if not user_id:
            return "Could not determine the user ID. Please specify a valid user ID or username."
        
        # Get the user profile
        profile = self.profile_assistant.get_user_profile(user_id)
        
        if not profile:
            return f"No profile found for user ID {user_id}."
        
        # Get the user interests
        interests = self.profile_assistant.get_user_interests(user_id)
        
        # Format the profile information
        profile_text = f"Profile for user ID {user_id}:\n\n"
        
        # Add basic information
        metadata = profile.get("metadata", {})
        if metadata.get("first_name"):
            profile_text += f"First Name: {metadata['first_name']}\n"
        
        if metadata.get("last_name"):
            profile_text += f"Last Name: {metadata['last_name']}\n"
        
        if metadata.get("username"):
            profile_text += f"Username: @{metadata['username']}\n"
        
        profile_text += "\n"
        
        # Add interests
        if interests:
            profile_text += "Interests:\n"
            
            for category, items in interests.items():
                profile_text += f"\n{category.capitalize()}:\n"
                for item in items:
                    profile_text += f"- {item}\n"
        else:
            profile_text += "No interests found."
        
        return profile_text 