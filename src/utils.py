# src/utils.py
# Utility functions for Para-Phrase Generator
"""
This module provides utility functions used throughout the Para-Phrase Generator.
"""

import re
import traceback
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from .config import DEBUG_MODE, DEFAULT_TONE, MAX_MESSAGES_PER_CHAT, USE_AGENT_SYSTEM, AVAILABLE_TONES

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_all_caps(text: str) -> bool:
    """
    Check if a text string is in all capital letters.
    
    Args:
        text (str): Text string to check
        
    Returns:
        bool: True if the text is all caps, False otherwise
    """
    if not text:  # Handle empty or None text
        return False
    has_upper = any(c.isupper() for c in text)
    has_lower = any(c.islower() for c in text)
    return has_upper and not has_lower

def extract_all_caps_sequences(text: str) -> List[str]:
    """
    Extract sequences of all-caps words from text.
    
    Args:
        text (str): Text to process
        
    Returns:
        List[str]: List of all-caps sequences
    """
    if not text:
        return []
    words = text.split()
    sequences = []
    current_sequence = []
    for word in words:
        if word.isupper() and any(c.isalpha() for c in word):  # Must be all caps and have at least one letter
            current_sequence.append(word)
        else:
            if current_sequence:  # End of a sequence
                sequences.append(" ".join(current_sequence))
                current_sequence = []
    if current_sequence:  # Add the last sequence if exists
        sequences.append(" ".join(current_sequence))
    return sequences

def extract_twitter_urls(text: str) -> List[str]:
    """
    Extract Twitter URLs from text.
    
    Args:
        text (str): Text to process
        
    Returns:
        List[str]: List of Twitter URLs
    """
    if not text:
        return []
    # Pattern for Twitter URLs
    pattern = r'https?://(?:www\.)?twitter\.com/[^\s]+'
    return re.findall(pattern, text)

def format_messages_for_summary(messages: List[Dict[str, Any]], tone: str) -> List[str]:
    """
    Format messages for summarization.
    
    Args:
        messages (List[Dict[str, Any]]): List of message dictionaries
        tone (str): The tone for summarization
        
    Returns:
        List[str]: List of formatted message strings
    """
    formatted_messages = []
    
    if tone == "deaf":
        for msg in messages:
            if msg.get("text"):  # Only process messages with text
                sequences = extract_all_caps_sequences(msg["text"])
                for seq in sequences:
                    formatted_messages.append(f"{msg['sender']}: {seq}")
        if not formatted_messages:
            # Return a placeholder if no all caps found
            return ["No all-caps messages found."]
    else:
        for msg in messages:
            if msg.get("is_image"):
                formatted_messages.append(f"{msg['sender']} sent an image.")
            elif msg.get("reply_to"):
                original = msg['reply_to']
                formatted_messages.append(f"{msg['sender']} replied to {original['sender']}'s message '{original['text']}': {msg['text']}")
            else:
                formatted_messages.append(f"{msg['sender']}: {msg['text']}")
    
    return formatted_messages

def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format an error message for user-friendly display.
    
    Args:
        error (Exception): The exception that occurred
        context (str, optional): Additional context about where the error occurred
        
    Returns:
        str: A user-friendly error message
    """
    # Extract the error message
    error_message = str(error)
    
    # Create a user-friendly message
    if context:
        friendly_message = f"Error: {context}. {error_message}"
    else:
        friendly_message = f"Error: {error_message}"
    
    # Log the error
    logger.error(friendly_message)
    
    return friendly_message

def format_messages(messages: List[Dict[str, Any]]) -> str:
    """
    Format a list of messages for summarization.
    
    Args:
        messages (List[Dict[str, Any]]): List of message dictionaries
        
    Returns:
        str: Formatted message string
    """
    formatted = []
    
    for i, msg in enumerate(messages):
        # Extract message components
        username = msg.get('from', {}).get('username', 'Unknown')
        text = msg.get('text', '')
        reply_to = msg.get('reply_to_message')
        has_photo = 'photo' in msg
        
        # Format username
        username_str = f"@{username}"
        
        # Format message based on type
        if has_photo:
            if text:
                formatted.append(f"{username_str}: [SHARED PHOTO] {text}")
            else:
                formatted.append(f"{username_str}: [SHARED PHOTO]")
        elif reply_to:
            reply_username = reply_to.get('from', {}).get('username', 'Unknown')
            reply_text = reply_to.get('text', '')
            # Truncate reply text if it's too long
            if len(reply_text) > 50:
                reply_text = reply_text[:47] + "..."
            formatted.append(f"{username_str} replying to @{reply_username} '{reply_text}': {text}")
        else:
            formatted.append(f"{username_str}: {text}")
    
    return "\n".join(formatted)

def extract_command_args(text: str) -> Tuple[str, List[str]]:
    """
    Extract command and arguments from a message text.
    
    Args:
        text (str): Message text
        
    Returns:
        Tuple[str, List[str]]: Command and list of arguments
    """
    parts = text.strip().split()
    command = parts[0] if parts else ""
    args = parts[1:] if len(parts) > 1 else []
    
    return command, args

class TelegramBridge:
    """
    Bridge class to handle communication between the Telegram bot and the agent system.
    
    This class provides methods for converting between Telegram message formats and
    formats expected by the agent system, as well as handling command routing and
    response formatting.
    
    Attributes:
        chat_history (Dict[str, List[Dict[str, Any]]]): Dictionary of chat histories
        chat_tones (Dict[str, str]): Dictionary of chat tones
    """
    
    def __init__(
        self, 
        chat_history: Dict[str, List[Dict[str, Any]]], 
        chat_tones: Dict[str, str]
    ):
        """
        Initialize the TelegramBridge.
        
        Args:
            chat_history (Dict[str, List[Dict[str, Any]]]): Dictionary of chat histories
            chat_tones (Dict[str, str]): Dictionary of chat tones
        """
        self.chat_history = chat_history
        self.chat_tones = chat_tones
        logger.info("TelegramBridge initialized")
    
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
        # Get the chat ID from the message
        chat_id = str(message.get('chat', {}).get('id', ''))
        
        if not chat_id:
            logger.warning("Message has no chat ID, skipping")
            return
        
        # Initialize chat history for this chat if it doesn't exist
        if chat_id not in self.chat_history:
            self.chat_history[chat_id] = []
        
        # Add the message to the chat history
        self.chat_history[chat_id].append(message)
        
        # Trim the chat history if it's too long
        if len(self.chat_history[chat_id]) > MAX_MESSAGES_PER_CHAT:
            self.chat_history[chat_id] = self.chat_history[chat_id][-MAX_MESSAGES_PER_CHAT:]
    
    def handle_command(
        self, 
        message: Dict[str, Any], 
        command: str, 
        args: List[str]
    ) -> Optional[str]:
        """
        Handle a command from a Telegram message using the agent system.
        
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
        if not USE_AGENT_SYSTEM:
            logger.info("Agent system is disabled, skipping")
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
                    
                    # Process the request using the agent system
                    return self._process_summary_request(chat_id, messages, tone)
                    
                except ValueError:
                    return "Please specify a valid number of messages to summarize."
            
            # Unknown command or missing arguments
            return None
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            logger.error(traceback.format_exc())
            return format_error_message(e)
    
    def _process_summary_request(
        self, 
        chat_id: str, 
        messages: List[Dict[str, Any]], 
        tone: str
    ) -> str:
        """
        Process a summary request using the agent system.
        
        Args:
            chat_id (str): Chat ID
            messages (List[Dict[str, Any]]): List of message dictionaries
            tone (str): Tone to use for the summary
            
        Returns:
            str: Summary text
        """
        try:
            # Import here to avoid circular imports
            from .agents import get_delegation_agent
            from .agents.interface import AgentInterface
            from .agents.context import RunContextManager
            
            # Create the agent interface
            interface = AgentInterface()
            
            # Create a run context
            context = RunContextManager.create_context()
            context.set("chat_id", chat_id)
            context.set("messages", messages)
            context.set("tone", tone)
            
            # Get the delegation agent
            delegation_agent = get_delegation_agent()
            
            # Format the input for the delegation agent
            formatted_messages = format_messages(messages)
            input_text = f"Summarize the following messages in {tone} tone:\n\n{formatted_messages}"
            
            # Run the delegation agent
            result = interface.run_agent_sync(
                agent=delegation_agent.agent,
                input_text=input_text,
                context=context,
                max_turns=3
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing summary request: {e}")
            logger.error(traceback.format_exc())
            return format_error_message(e)

def fetch_telegram_file(file_id: str) -> Optional[bytes]:
    """
    Fetch a file from Telegram servers using the file ID.
    
    This function uses the Telegram Bot API to retrieve a file using its file_id.
    It requires a TELEGRAM_BOT_TOKEN environment variable to be set.
    
    Args:
        file_id (str): The Telegram file ID to retrieve
        
    Returns:
        Optional[bytes]: The file content as bytes, or None if retrieval failed
    
    Note:
        This function handles all error cases and returns None on failure,
        logging appropriate error messages for debugging.
    """
    import os
    import logging
    import requests
    
    logger = logging.getLogger(__name__)
    
    # Get the bot token from environment
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("No Telegram bot token found in environment variables")
        return None
    
    try:
        # Step 1: Get the file path from Telegram
        file_info_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        file_info_response = requests.get(file_info_url, timeout=10)
        file_info = file_info_response.json()
        
        if not file_info.get("ok"):
            logger.error(f"Failed to get file info from Telegram: {file_info.get('description', 'Unknown error')}")
            return None
        
        # Step 2: Get the file path
        file_path = file_info["result"]["file_path"]
        
        # Step 3: Construct the download URL
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        
        # Step 4: Download the file
        file_response = requests.get(download_url, timeout=20)
        if file_response.status_code != 200:
            logger.error(f"Failed to download file from Telegram: HTTP status code {file_response.status_code}")
            return None
        
        # Return the file content
        return file_response.content
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching Telegram file: {file_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException fetching Telegram file: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching Telegram file: {e}")
        return None 