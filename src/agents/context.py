# src/agents/context.py
# Run context management for agents
"""
This module provides classes for managing context between agents in the
OpenAI Agents SDK framework. It handles state persistence, serialization,
and context sharing between different agents.
"""

import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Set, TypeVar, Generic
from dataclasses import dataclass, field, asdict

from ..config import DEBUG_MODE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define a type variable for context
T = TypeVar('T')

@dataclass
class BotContext:
    """
    Base context object for the Telegram bot.
    
    This class contains shared state that can be passed between agents
    during a conversation.
    
    Attributes:
        chat_id (Optional[int]): The ID of the current chat
        user_id (Optional[int]): The ID of the current user
        message_history (List[Dict[str, Any]]): List of recent messages
        tone (str): The current tone setting
        command (Optional[str]): The current command being processed
        command_args (Dict[str, Any]): Arguments for the current command
        session_id (str): Unique identifier for this context session
        created_at (datetime.datetime): When this context was created
        last_updated (datetime.datetime): When this context was last updated
        metadata (Dict[str, Any]): Additional metadata for the context
    """
    
    chat_id: Optional[int] = None
    user_id: Optional[int] = None
    message_history: List[Dict[str, Any]] = field(default_factory=list)
    tone: str = "stoic"
    command: Optional[str] = None
    command_args: Dict[str, Any] = field(default_factory=dict)
    session_id: str = field(default_factory=lambda: f"session_{datetime.datetime.now().timestamp()}")
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_updated: datetime.datetime = field(default_factory=datetime.datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.datetime.now()
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the history.
        
        Args:
            message (Dict[str, Any]): The message to add
        """
        self.message_history.append(message)
        self.update_timestamp()
    
    def set_command(self, command: str, args: Dict[str, Any] = None) -> None:
        """
        Set the current command and arguments.
        
        Args:
            command (str): The command being processed
            args (Dict[str, Any], optional): Command arguments
        """
        self.command = command
        self.command_args = args or {}
        self.update_timestamp()
    
    def set_tone(self, tone: str) -> None:
        """
        Set the tone for summarization.
        
        Args:
            tone (str): The tone to use
        """
        self.tone = tone
        self.update_timestamp()
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key (str): The metadata key
            value (Any): The metadata value
        """
        self.metadata[key] = value
        self.update_timestamp()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the context
        """
        # Convert to dictionary, handling datetime objects
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['last_updated'] = self.last_updated.isoformat()
        return result
    
    def to_json(self) -> str:
        """
        Convert the context to a JSON string.
        
        Returns:
            str: JSON representation of the context
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BotContext':
        """
        Create a context object from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of the context
            
        Returns:
            BotContext: The context object
        """
        # Handle datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.datetime.fromisoformat(data['created_at'])
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.datetime.fromisoformat(data['last_updated'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BotContext':
        """
        Create a context object from a JSON string.
        
        Args:
            json_str (str): JSON representation of the context
            
        Returns:
            BotContext: The context object
        """
        return cls.from_dict(json.loads(json_str))


class RunContextManager(Generic[T]):
    """
    Manager for agent run contexts.
    
    This class provides utilities for creating, tracking, and updating
    context objects that are shared between agents during execution.
    
    Attributes:
        contexts (Dict[str, T]): Dictionary of active contexts by ID
        default_context_class: The class to use for creating new contexts
    """
    
    def __init__(self, default_context_class: Any = BotContext):
        """
        Initialize a RunContextManager instance.
        
        Args:
            default_context_class (Any): The class to use for creating new contexts
        """
        self.contexts: Dict[str, T] = {}
        self.default_context_class = default_context_class
        logger.debug(f"Initialized RunContextManager with {default_context_class.__name__}")
    
    def get_context(self, context_id: str) -> Optional[T]:
        """
        Get a context by ID.
        
        Args:
            context_id (str): The context ID
            
        Returns:
            Optional[T]: The context object, or None if not found
        """
        return self.contexts.get(context_id)
    
    def create_context(self, context_id: str, **kwargs) -> T:
        """
        Create a new context.
        
        Args:
            context_id (str): The context ID
            **kwargs: Additional arguments for the context constructor
            
        Returns:
            T: The new context object
        """
        # Create a new context object
        context = self.default_context_class(**kwargs)
        
        # Store it in the contexts dictionary
        self.contexts[context_id] = context
        logger.debug(f"Created new context with ID {context_id}")
        
        return context
    
    def get_or_create_context(self, context_id: str, **kwargs) -> T:
        """
        Get a context by ID, or create a new one if it doesn't exist.
        
        Args:
            context_id (str): The context ID
            **kwargs: Additional arguments for the context constructor
            
        Returns:
            T: The context object
        """
        existing = self.get_context(context_id)
        if existing is not None:
            return existing
        
        return self.create_context(context_id, **kwargs)
    
    def update_context(self, context_id: str, **kwargs) -> Optional[T]:
        """
        Update a context with new values.
        
        Args:
            context_id (str): The context ID
            **kwargs: New values to set on the context
            
        Returns:
            Optional[T]: The updated context, or None if not found
        """
        context = self.get_context(context_id)
        if context is None:
            logger.warning(f"Attempted to update non-existent context {context_id}")
            return None
        
        # Update the context with new values
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        # Update the timestamp
        if hasattr(context, 'update_timestamp'):
            context.update_timestamp()
        
        logger.debug(f"Updated context {context_id}")
        return context
    
    def delete_context(self, context_id: str) -> bool:
        """
        Delete a context.
        
        Args:
            context_id (str): The context ID
            
        Returns:
            bool: True if the context was deleted, False if not found
        """
        if context_id in self.contexts:
            del self.contexts[context_id]
            logger.debug(f"Deleted context {context_id}")
            return True
        
        logger.warning(f"Attempted to delete non-existent context {context_id}")
        return False
    
    def get_all_context_ids(self) -> Set[str]:
        """
        Get all context IDs.
        
        Returns:
            Set[str]: Set of all context IDs
        """
        return set(self.contexts.keys())
    
    def cleanup_old_contexts(self, max_age_seconds: int = 3600) -> int:
        """
        Remove contexts that haven't been updated for a certain time.
        
        Args:
            max_age_seconds (int): Maximum age in seconds
            
        Returns:
            int: Number of contexts removed
        """
        now = datetime.datetime.now()
        to_remove = []
        
        # Find contexts to remove
        for context_id, context in self.contexts.items():
            if hasattr(context, 'last_updated'):
                age = now - context.last_updated
                if age.total_seconds() > max_age_seconds:
                    to_remove.append(context_id)
        
        # Remove the contexts
        for context_id in to_remove:
            self.delete_context(context_id)
        
        logger.info(f"Cleaned up {len(to_remove)} old contexts")
        return len(to_remove) 