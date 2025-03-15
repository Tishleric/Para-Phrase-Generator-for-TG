"""
User Profile Assistant

This module provides an assistant for managing user profiles in the vector store.
It extracts information from messages and updates user profiles accordingly.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Union
import json

from .manager import AssistantsManager
from .tools import function_tool, WebSearchTool, CodeInterpreterTool

from ..vector_store import UserProfileStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProfileAssistant:
    """
    Assistant for managing user profiles.
    
    This class provides methods for extracting information from messages and
    updating user profiles in the vector store.
    
    Attributes:
        assistants_manager (AssistantsManager): The assistants manager
        profile_store (UserProfileStore): The user profile store
        assistant_id (str): The ID of the profile assistant
    """
    
    def __init__(
        self,
        assistants_manager: Optional[AssistantsManager] = None,
        profile_store: Optional[UserProfileStore] = None
    ):
        """
        Initialize the ProfileAssistant.
        
        Args:
            assistants_manager (AssistantsManager, optional): The assistants manager.
                Defaults to None, which creates a new AssistantsManager instance.
            profile_store (UserProfileStore, optional): The user profile store.
                Defaults to None, which creates a new UserProfileStore instance.
        """
        self.assistants_manager = assistants_manager or AssistantsManager()
        self.profile_store = profile_store or UserProfileStore()
        self.assistant_id = None
        
        # Initialize the assistant
        self._initialize_assistant()
    
    def _initialize_assistant(self):
        """
        Initialize the profile assistant.
        """
        logger.info("Initializing profile assistant...")
        
        # Define the tools for the profile assistant
        tools = [
            WebSearchTool().as_tool(),
            function_tool(
                name="update_user_profile",
                description="Update a user's profile with new information",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the user"
                        },
                        "information": {
                            "type": "string",
                            "description": "The information to add to the profile"
                        },
                        "category": {
                            "type": "string",
                            "description": "The category of the information (e.g., 'sports_team', 'opinion', 'personality')"
                        }
                    },
                    "required": ["user_id", "information", "category"]
                }
            ),
            function_tool(
                name="get_user_profile",
                description="Get information about a user from their profile",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "The ID of the user"
                        }
                    },
                    "required": ["user_id"]
                }
            )
        ]
        
        # Define the instructions for the profile assistant
        instructions = """
        You are a profile assistant that extracts information about users from messages and updates their profiles.
        
        Your tasks:
        1. Analyze messages to identify information about users, such as:
           - Sports team allegiances (e.g., "I'm a Manchester United fan")
           - Opinions on topics (e.g., "I think climate change is a serious issue")
           - Personality traits (e.g., "I'm always late to meetings")
           - Preferences (e.g., "I love pizza")
           - Biographical information (e.g., "I grew up in London")
        
        2. Update user profiles with this information, categorizing it appropriately.
        
        3. When asked about a user, retrieve their profile and provide a summary of what you know about them.
        
        Be attentive to context and nuance. Don't make assumptions about users based on limited information.
        Only extract information that is clearly stated or strongly implied.
        """
        
        # Check if the assistant already exists
        existing_assistants = self.assistants_manager.list_assistants(name="Profile Assistant")
        
        if existing_assistants:
            # Use the existing assistant
            self.assistant_id = existing_assistants[0].id
            logger.info(f"Using existing profile assistant: {self.assistant_id}")
        else:
            # Create a new assistant
            assistant = self.assistants_manager.create_assistant(
                name="Profile Assistant",
                instructions=instructions,
                tools=tools,
                model="gpt-4o"
            )
            self.assistant_id = assistant.id
            logger.info(f"Created new profile assistant: {self.assistant_id}")
    
    async def process_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Process messages to extract user information and update profiles.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries
        """
        logger.info(f"Processing {len(messages)} messages for user profiles...")
        
        # Create a thread for the profile assistant
        thread = self.assistants_manager.create_thread()
        
        # Format the messages for the profile assistant
        formatted_messages = self._format_messages_for_processing(messages)
        
        # Add the formatted messages to the thread
        self.assistants_manager.add_message(
            thread_id=thread.id,
            role="user",
            content=formatted_messages
        )
        
        # Run the profile assistant
        run = await self.assistants_manager.create_run(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )
        
        # Wait for the run to complete
        run = await self.assistants_manager.wait_for_run(thread_id=thread.id, run_id=run.id)
        
        # Process the results
        self._process_profile_results(thread.id, messages)
    
    def _format_messages_for_processing(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format messages for processing by the profile assistant.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries
            
        Returns:
            str: Formatted messages
        """
        formatted_messages = []
        
        for message in messages:
            user_id = message.get("from", {}).get("id")
            username = message.get("from", {}).get("username")
            first_name = message.get("from", {}).get("first_name")
            last_name = message.get("from", {}).get("last_name")
            text = message.get("text", "")
            
            if not user_id or not text:
                continue
            
            # Format the message
            formatted_message = f"User ID: {user_id}"
            
            if username:
                formatted_message += f", Username: {username}"
            
            if first_name:
                formatted_message += f", First Name: {first_name}"
            
            if last_name:
                formatted_message += f", Last Name: {last_name}"
            
            formatted_message += f"\nMessage: {text}\n"
            
            formatted_messages.append(formatted_message)
        
        # Join the formatted messages
        return "\n".join(formatted_messages)
    
    def _process_profile_results(self, thread_id: str, original_messages: List[Dict[str, Any]]) -> None:
        """
        Process the results of the profile assistant run.
        
        Args:
            thread_id (str): The ID of the thread
            original_messages (List[Dict[str, Any]]): The original messages
        """
        # Get the messages from the thread
        messages = self.assistants_manager.list_messages(thread_id=thread_id)
        
        # Look for tool calls in the assistant's messages
        for message in messages:
            if message.role != "assistant":
                continue
            
            # Process tool calls
            for content in message.content:
                if content.type != "tool_calls":
                    continue
                
                for tool_call in content.tool_calls:
                    if tool_call.type != "function":
                        continue
                    
                    function = tool_call.function
                    
                    if function.name == "update_user_profile":
                        # Parse the arguments
                        try:
                            args = json.loads(function.arguments)
                            user_id = args.get("user_id")
                            information = args.get("information")
                            category = args.get("category")
                            
                            if user_id and information and category:
                                # Update the user profile
                                self.profile_store.add_user_information(
                                    user_id=user_id,
                                    information=information,
                                    category=category
                                )
                                logger.info(f"Updated profile for user {user_id} with {category}: {information}")
                        except Exception as e:
                            logger.error(f"Error updating user profile: {e}")
    
    def get_user_profile(self, user_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get a user's profile.
        
        Args:
            user_id (Union[str, int]): The user ID
            
        Returns:
            Optional[Dict[str, Any]]: The user profile, or None if not found
        """
        return self.profile_store.get_user_profile(user_id)
    
    def get_user_interests(self, user_id: Union[str, int]) -> Dict[str, List[str]]:
        """
        Get a user's interests.
        
        Args:
            user_id (Union[str, int]): The user ID
            
        Returns:
            Dict[str, List[str]]: Dictionary of interests by category
        """
        return self.profile_store.extract_user_interests(user_id)
    
    def initialize_user_from_telegram(self, user_data: Dict[str, Any]) -> None:
        """
        Initialize a user profile from Telegram user data.
        
        Args:
            user_data (Dict[str, Any]): Telegram user data
        """
        user_id = user_data.get("id")
        username = user_data.get("username")
        first_name = user_data.get("first_name")
        last_name = user_data.get("last_name")
        
        if not user_id:
            return
        
        # Add or update the user
        self.profile_store.add_or_update_user(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        
        logger.info(f"Initialized profile for user {user_id}") 