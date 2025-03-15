"""
OpenAI SDK Import Module

This module centralizes all imports from the OpenAI API and provides
tools and utilities for working with the Assistants API and Agents SDK.

Usage:
    from src.sdk_imports import (
        OpenAIClient, ThreadManager, AssistantManager,
        function_tool, WebSearchTool, etc.
    )
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, Callable, Awaitable
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import from OpenAI
try:
    import openai
    from openai import OpenAI, AsyncOpenAI
    from openai._streaming import Stream
    from openai.types.beta.threads import ThreadMessage
    from openai.types.beta.threads.runs import Run, RunStatus
    from openai.types.beta.threads.runs.tool_call import ToolCall
    from openai.types.beta.assistants import Assistant

    # Set OPENAI_API_KEY if available
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        logger.info("Setting OpenAI API key from environment")
    else:
        logger.warning("No OpenAI API key found in environment. API calls will fail.")

    OPENAI_AVAILABLE = True
    logger.info("OpenAI SDK imported successfully")

    # If ANTHROPIC_API_KEY is available, import Anthropic as well
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        try:
            import anthropic
            from anthropic import Anthropic, AsyncAnthropic
            logger.info("Anthropic SDK imported successfully")
            ANTHROPIC_AVAILABLE = True
        except ImportError:
            logger.warning("Anthropic SDK not available. Install with 'pip install anthropic'")
            ANTHROPIC_AVAILABLE = False
    else:
        ANTHROPIC_AVAILABLE = False
        logger.info("No Anthropic API key found in environment. Anthropic functionality disabled.")

except ImportError as e:
    logger.warning(f"Could not import OpenAI SDK: {e}. Install with 'pip install openai'")
    OPENAI_AVAILABLE = False
    ANTHROPIC_AVAILABLE = False

    # Create placeholders for imports
    class OpenAI:
        def __init__(self, *args, **kwargs):
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")

    class AsyncOpenAI:
        def __init__(self, *args, **kwargs):
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")

    class Anthropic:
        def __init__(self, *args, **kwargs):
            raise ImportError("Anthropic SDK not available. Install with 'pip install anthropic'")

    class AsyncAnthropic:
        def __init__(self, *args, **kwargs):
            raise ImportError("Anthropic SDK not available. Install with 'pip install anthropic'")


# OpenAI Client wrapper
class OpenAIClient:
    """
    Wrapper class for the OpenAI client that provides convenient access to
    both synchronous and asynchronous clients.
    
    Attributes:
        sync_client (OpenAI): Synchronous OpenAI client
        async_client (AsyncOpenAI): Asynchronous OpenAI client
        api_key (str): OpenAI API key
    """
    
    _instance = None
    
    def __new__(cls, api_key=None):
        """
        Create a new OpenAIClient instance, or return the existing one.
        This implements a singleton pattern.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to None, which will
                use the OPENAI_API_KEY environment variable.
        
        Returns:
            OpenAIClient: An instance of OpenAIClient
        """
        if cls._instance is None:
            cls._instance = super(OpenAIClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, api_key=None):
        """
        Initialize the OpenAIClient.
        
        Args:
            api_key (str, optional): OpenAI API key. Defaults to None, which will
                use the OPENAI_API_KEY environment variable.
        """
        if not hasattr(self, 'initialized'):
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            
            if not OPENAI_AVAILABLE:
                logger.error("OpenAI SDK not available. Install with 'pip install openai'")
                self.sync_client = None
                self.async_client = None
                return
            
            if not self.api_key:
                logger.warning("No OpenAI API key provided. API calls will fail.")
            
            # Create synchronous client
            self.sync_client = OpenAI(api_key=self.api_key)
            
            # Create asynchronous client
            self.async_client = AsyncOpenAI(api_key=self.api_key)
            
            self.initialized = True
            logger.info("OpenAIClient initialized")
    
    def chat_completions(self, *args, **kwargs):
        """
        Create a chat completion using the synchronous client.
        
        Args:
            *args: Positional arguments to pass to the client
            **kwargs: Keyword arguments to pass to the client
        
        Returns:
            The response from the OpenAI API
        """
        if not OPENAI_AVAILABLE or not self.sync_client:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return self.sync_client.chat.completions.create(*args, **kwargs)
    
    async def async_chat_completions(self, *args, **kwargs):
        """
        Create a chat completion using the asynchronous client.
        
        Args:
            *args: Positional arguments to pass to the client
            **kwargs: Keyword arguments to pass to the client
        
        Returns:
            The response from the OpenAI API
        """
        if not OPENAI_AVAILABLE or not self.async_client:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return await self.async_client.chat.completions.create(*args, **kwargs)
    
    def images(self, *args, **kwargs):
        """
        Generate images using the synchronous client.
        
        Args:
            *args: Positional arguments to pass to the client
            **kwargs: Keyword arguments to pass to the client
        
        Returns:
            The response from the OpenAI API
        """
        if not OPENAI_AVAILABLE or not self.sync_client:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return self.sync_client.images.generate(*args, **kwargs)
    
    async def async_images(self, *args, **kwargs):
        """
        Generate images using the asynchronous client.
        
        Args:
            *args: Positional arguments to pass to the client
            **kwargs: Keyword arguments to pass to the client
        
        Returns:
            The response from the OpenAI API
        """
        if not OPENAI_AVAILABLE or not self.async_client:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return await self.async_client.images.generate(*args, **kwargs)


# Thread Manager
class ThreadManager:
    """
    Manager class for OpenAI Assistants API threads.
    
    This class provides methods for creating, retrieving, and managing threads
    in the OpenAI Assistants API.
    
    Attributes:
        client (OpenAIClient): The OpenAI client to use for API calls
    """
    
    def __init__(self, client=None):
        """
        Initialize the ThreadManager.
        
        Args:
            client (OpenAIClient, optional): The OpenAI client to use. Defaults to None,
                which will create a new OpenAIClient instance.
        """
        self.client = client or OpenAIClient()
        logger.info("ThreadManager initialized")
    
    def create_thread(self):
        """
        Create a new thread.
        
        Returns:
            The created thread
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return self.client.sync_client.beta.threads.create()
    
    async def async_create_thread(self):
        """
        Create a new thread asynchronously.
        
        Returns:
            The created thread
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return await self.client.async_client.beta.threads.create()
    
    def get_thread(self, thread_id):
        """
        Retrieve a thread by ID.
        
        Args:
            thread_id (str): The ID of the thread to retrieve
        
        Returns:
            The retrieved thread
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return self.client.sync_client.beta.threads.retrieve(thread_id)
    
    async def async_get_thread(self, thread_id):
        """
        Retrieve a thread by ID asynchronously.
        
        Args:
            thread_id (str): The ID of the thread to retrieve
        
        Returns:
            The retrieved thread
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return await self.client.async_client.beta.threads.retrieve(thread_id)
    
    def add_message(self, thread_id, content, role="user", file_ids=None):
        """
        Add a message to a thread.
        
        Args:
            thread_id (str): The ID of the thread to add the message to
            content (str): The content of the message
            role (str, optional): The role of the message sender. Defaults to "user".
            file_ids (List[str], optional): List of file IDs to attach to the message.
                Defaults to None.
        
        Returns:
            The created message
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        message_params = {
            "role": role,
            "content": content,
        }
        
        if file_ids:
            message_params["file_ids"] = file_ids
        
        return self.client.sync_client.beta.threads.messages.create(
            thread_id=thread_id,
            **message_params
        )
    
    async def async_add_message(self, thread_id, content, role="user", file_ids=None):
        """
        Add a message to a thread asynchronously.
        
        Args:
            thread_id (str): The ID of the thread to add the message to
            content (str): The content of the message
            role (str, optional): The role of the message sender. Defaults to "user".
            file_ids (List[str], optional): List of file IDs to attach to the message.
                Defaults to None.
        
        Returns:
            The created message
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        message_params = {
            "role": role,
            "content": content,
        }
        
        if file_ids:
            message_params["file_ids"] = file_ids
        
        return await self.client.async_client.beta.threads.messages.create(
            thread_id=thread_id,
            **message_params
        )
    
    def list_messages(self, thread_id):
        """
        List all messages in a thread.
        
        Args:
            thread_id (str): The ID of the thread to list messages from
        
        Returns:
            List of messages in the thread
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return self.client.sync_client.beta.threads.messages.list(thread_id=thread_id)
    
    async def async_list_messages(self, thread_id):
        """
        List all messages in a thread asynchronously.
        
        Args:
            thread_id (str): The ID of the thread to list messages from
        
        Returns:
            List of messages in the thread
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        return await self.client.async_client.beta.threads.messages.list(thread_id=thread_id)


# Assistant Manager
class AssistantManager:
    """
    Manager class for OpenAI Assistants API assistants.
    
    This class provides methods for creating, retrieving, and managing assistants
    in the OpenAI Assistants API.
    
    Attributes:
        client (OpenAIClient): The OpenAI client to use for API calls
        thread_manager (ThreadManager): The thread manager to use for thread operations
    """
    
    def __init__(self, client=None, thread_manager=None):
        """
        Initialize the AssistantManager.
        
        Args:
            client (OpenAIClient, optional): The OpenAI client to use. Defaults to None,
                which will create a new OpenAIClient instance.
            thread_manager (ThreadManager, optional): The thread manager to use. Defaults to None,
                which will create a new ThreadManager instance.
        """
        self.client = client or OpenAIClient()
        self.thread_manager = thread_manager or ThreadManager(client=self.client)
        self._assistants_cache = {}  # Cache assistants by ID
        logger.info("AssistantManager initialized")
    
    def create_assistant(self, name, instructions, model="gpt-4o", tools=None, tool_resources=None):
        """
        Create a new assistant.
        
        Args:
            name (str): The name of the assistant
            instructions (str): Instructions for the assistant
            model (str, optional): The model to use. Defaults to "gpt-4o".
            tools (List[Dict], optional): List of tools for the assistant to use.
                Defaults to None.
            tool_resources (Dict, optional): Resources for the tools. Defaults to None.
        
        Returns:
            The created assistant
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        assistant_params = {
            "name": name,
            "instructions": instructions,
            "model": model,
        }
        
        if tools:
            assistant_params["tools"] = tools
        
        if tool_resources:
            assistant_params["tool_resources"] = tool_resources
        
        assistant = self.client.sync_client.beta.assistants.create(**assistant_params)
        self._assistants_cache[assistant.id] = assistant
        return assistant
    
    async def async_create_assistant(self, name, instructions, model="gpt-4o", tools=None, tool_resources=None):
        """
        Create a new assistant asynchronously.
        
        Args:
            name (str): The name of the assistant
            instructions (str): Instructions for the assistant
            model (str, optional): The model to use. Defaults to "gpt-4o".
            tools (List[Dict], optional): List of tools for the assistant to use.
                Defaults to None.
            tool_resources (Dict, optional): Resources for the tools. Defaults to None.
        
        Returns:
            The created assistant
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        assistant_params = {
            "name": name,
            "instructions": instructions,
            "model": model,
        }
        
        if tools:
            assistant_params["tools"] = tools
        
        if tool_resources:
            assistant_params["tool_resources"] = tool_resources
        
        assistant = await self.client.async_client.beta.assistants.create(**assistant_params)
        self._assistants_cache[assistant.id] = assistant
        return assistant
    
    def get_assistant(self, assistant_id):
        """
        Retrieve an assistant by ID. Uses cache if available.
        
        Args:
            assistant_id (str): The ID of the assistant to retrieve
        
        Returns:
            The retrieved assistant
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        # Check cache first
        if assistant_id in self._assistants_cache:
            return self._assistants_cache[assistant_id]
        
        # Retrieve from API and cache
        assistant = self.client.sync_client.beta.assistants.retrieve(assistant_id)
        self._assistants_cache[assistant_id] = assistant
        return assistant
    
    async def async_get_assistant(self, assistant_id):
        """
        Retrieve an assistant by ID asynchronously. Uses cache if available.
        
        Args:
            assistant_id (str): The ID of the assistant to retrieve
        
        Returns:
            The retrieved assistant
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        # Check cache first
        if assistant_id in self._assistants_cache:
            return self._assistants_cache[assistant_id]
        
        # Retrieve from API and cache
        assistant = await self.client.async_client.beta.assistants.retrieve(assistant_id)
        self._assistants_cache[assistant_id] = assistant
        return assistant
    
    def run_assistant(self, assistant_id, thread_id, instructions=None, tools_input=None):
        """
        Run an assistant on a thread.
        
        Args:
            assistant_id (str): The ID of the assistant to run
            thread_id (str): The ID of the thread to run the assistant on
            instructions (str, optional): Additional instructions for the run.
                Defaults to None.
            tools_input (Dict, optional): Input for the tools. Defaults to None.
        
        Returns:
            The created run
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        run_params = {
            "assistant_id": assistant_id,
        }
        
        if instructions:
            run_params["instructions"] = instructions
        
        if tools_input:
            run_params["tools_input"] = tools_input
        
        return self.client.sync_client.beta.threads.runs.create(
            thread_id=thread_id,
            **run_params
        )
    
    async def async_run_assistant(self, assistant_id, thread_id, instructions=None, tools_input=None):
        """
        Run an assistant on a thread asynchronously.
        
        Args:
            assistant_id (str): The ID of the assistant to run
            thread_id (str): The ID of the thread to run the assistant on
            instructions (str, optional): Additional instructions for the run.
                Defaults to None.
            tools_input (Dict, optional): Input for the tools. Defaults to None.
        
        Returns:
            The created run
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        run_params = {
            "assistant_id": assistant_id,
        }
        
        if instructions:
            run_params["instructions"] = instructions
        
        if tools_input:
            run_params["tools_input"] = tools_input
        
        return await self.client.async_client.beta.threads.runs.create(
            thread_id=thread_id,
            **run_params
        )
    
    def _run_until_complete(self, thread_id, run_id, poll_interval=1, timeout=60):
        """
        Wait for a run to complete.
        
        Args:
            thread_id (str): The ID of the thread
            run_id (str): The ID of the run to wait for
            poll_interval (int, optional): How often to poll the API in seconds.
                Defaults to 1.
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 60.
        
        Returns:
            The completed run
        
        Raises:
            TimeoutError: If the run doesn't complete within the timeout
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            run = self.client.sync_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                return run
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")
    
    async def _async_run_until_complete(self, thread_id, run_id, poll_interval=1, timeout=60):
        """
        Wait for a run to complete asynchronously.
        
        Args:
            thread_id (str): The ID of the thread
            run_id (str): The ID of the run to wait for
            poll_interval (int, optional): How often to poll the API in seconds.
                Defaults to 1.
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 60.
        
        Returns:
            The completed run
        
        Raises:
            TimeoutError: If the run doesn't complete within the timeout
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            run = await self.client.async_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                return run
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")
    
    def run_assistant_and_wait(self, assistant_id, thread_id, instructions=None, tools_input=None, timeout=60):
        """
        Run an assistant on a thread and wait for it to complete.
        
        Args:
            assistant_id (str): The ID of the assistant to run
            thread_id (str): The ID of the thread to run the assistant on
            instructions (str, optional): Additional instructions for the run.
                Defaults to None.
            tools_input (Dict, optional): Input for the tools. Defaults to None.
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 60.
        
        Returns:
            The completed run
        """
        run = self.run_assistant(
            assistant_id=assistant_id,
            thread_id=thread_id,
            instructions=instructions,
            tools_input=tools_input
        )
        
        return self._run_until_complete(thread_id, run.id, timeout=timeout)
    
    async def async_run_assistant_and_wait(self, assistant_id, thread_id, instructions=None, tools_input=None, timeout=60):
        """
        Run an assistant on a thread and wait for it to complete asynchronously.
        
        Args:
            assistant_id (str): The ID of the assistant to run
            thread_id (str): The ID of the thread to run the assistant on
            instructions (str, optional): Additional instructions for the run.
                Defaults to None.
            tools_input (Dict, optional): Input for the tools. Defaults to None.
            timeout (int, optional): Maximum time to wait in seconds. Defaults to 60.
        
        Returns:
            The completed run
        """
        run = await self.async_run_assistant(
            assistant_id=assistant_id,
            thread_id=thread_id,
            instructions=instructions,
            tools_input=tools_input
        )
        
        return await self._async_run_until_complete(thread_id, run.id, timeout=timeout)
    
    def get_latest_message(self, thread_id):
        """
        Get the latest assistant message from a thread.
        
        Args:
            thread_id (str): The ID of the thread
        
        Returns:
            The latest assistant message, or None if there are no assistant messages
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        messages = self.client.sync_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=1
        )
        
        for message in messages.data:
            if message.role == "assistant":
                return message
        
        return None
    
    async def async_get_latest_message(self, thread_id):
        """
        Get the latest assistant message from a thread asynchronously.
        
        Args:
            thread_id (str): The ID of the thread
        
        Returns:
            The latest assistant message, or None if there are no assistant messages
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK not available. Install with 'pip install openai'")
        
        messages = await self.client.async_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=1
        )
        
        for message in messages.data:
            if message.role == "assistant":
                return message
        
        return None


# Function tool for the OpenAI Assistants API
def function_tool(name, description, parameters=None):
    """
    Create a function tool for the OpenAI Assistants API.
    
    Args:
        name (str): The name of the function
        description (str): A description of what the function does
        parameters (Dict, optional): The parameters schema for the function.
            Defaults to None.
    
    Returns:
        Dict: A function tool definition
    """
    function = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
        }
    }
    
    if parameters:
        function["function"]["parameters"] = parameters
    else:
        function["function"]["parameters"] = {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    return function


# Web search tool for the OpenAI Assistants API
class WebSearchTool:
    """
    Web search tool for the OpenAI Assistants API.
    
    This class provides a web search tool that can be used with the OpenAI Assistants API.
    The actual search is performed by OpenAI's built-in search capability.
    
    Usage:
        tools = [WebSearchTool().as_tool()]
    """
    
    @staticmethod
    def as_tool():
        """
        Get the web search tool definition.
        
        Returns:
            Dict: A web search tool definition
        """
        return {
            "type": "web_search"
        }


# Backward compatibility with the older Agents SDK
class AgentSDKCompatLayer:
    """
    Compatibility layer for the older Agents SDK.
    
    This class provides compatibility with the older Agents SDK, allowing
    existing code to continue working with the new Assistants API.
    """
    
    @staticmethod
    def create_agent(name, instructions, model=None, tools=None):
        """
        Create an agent compatible with the older Agents SDK.
        
        Args:
            name (str): The name of the agent
            instructions (str): Instructions for the agent
            model (str, optional): The model to use. Defaults to None.
            tools (List, optional): List of tools for the agent to use.
                Defaults to None.
        
        Returns:
            An agent-like object that can be used with the older Agents SDK
        """
        # Import compatibility classes
        from collections import namedtuple
        
        Agent = namedtuple("Agent", ["name", "instructions", "model", "tools", "assistant_id", "as_tool"])
        
        # Create an assistant using the Assistants API
        manager = AssistantManager()
        assistant = manager.create_assistant(
            name=name,
            instructions=instructions,
            model=model or "gpt-4o",
            tools=tools
        )
        
        # Create a function that can be used to create a tool from this agent
        def as_tool(tool_name=None, tool_description=None):
            return function_tool(
                name=tool_name or name,
                description=tool_description or f"Use the {name} agent",
                parameters={
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input for the agent"
                        }
                    },
                    "required": ["input"]
                }
            )
        
        # Create and return an agent-like object
        return Agent(
            name=name,
            instructions=instructions,
            model=model or "gpt-4o",
            tools=tools,
            assistant_id=assistant.id,
            as_tool=as_tool
        )


# Export compatibility classes for backward compatibility
Agent = AgentSDKCompatLayer.create_agent

# Export all the classes and functions
__all__ = [
    "OpenAIClient", "ThreadManager", "AssistantManager",
    "function_tool", "WebSearchTool", "Agent"
]

# Import the Agents SDK for backward compatibility (if available)
try:
    from agents import (
        Agent, Runner, RunConfig, RunResult, RunHooks,
        ModelSettings, AgentsException, MaxTurnsExceeded,
        InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
        set_default_openai_key, Handoff, InputGuardrail, OutputGuardrail, function_tool,
        WebSearchTool, Tracing, Span, get_current_trace, trace,
        ModelProvider, Model, OpenAIChatCompletionsModel, set_default_openai_api
    )
    from agents.guardrail import Guardrail, GuardrailFunctionOutput
    from agents.models.openai_provider import OpenAIProvider
    
    # Set the OpenAI API key for the SDK if available
    if openai_api_key:
        set_default_openai_key(openai_api_key)
    
    SDK_AVAILABLE = True
    logger.info("OpenAI Agents SDK imported successfully")
except ImportError as e:
    logger.warning(f"Could not import OpenAI Agents SDK: {e}. Using mock implementations.")
    SDK_AVAILABLE = False
    
    # Mock implementations will follow...
    # ... 