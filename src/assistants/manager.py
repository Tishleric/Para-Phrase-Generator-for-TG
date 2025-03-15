"""
Assistants and Thread Managers

This module provides manager classes for working with the OpenAI Assistants API,
including creating and managing assistants, threads, and runs.
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import json

# Use our compatibility layer instead of direct imports
from ..sdk_imports import (
    OpenAI, AsyncOpenAI, 
    ThreadMessage, Run, RunStatus, Assistant
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        return await self.async_client.images.generate(*args, **kwargs)


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
        return self.client.sync_client.beta.threads.create()
    
    async def async_create_thread(self):
        """
        Create a new thread asynchronously.
        
        Returns:
            The created thread
        """
        return await self.client.async_client.beta.threads.create()
    
    def get_thread(self, thread_id):
        """
        Retrieve a thread by ID.
        
        Args:
            thread_id (str): The ID of the thread to retrieve
        
        Returns:
            The retrieved thread
        """
        return self.client.sync_client.beta.threads.retrieve(thread_id)
    
    async def async_get_thread(self, thread_id):
        """
        Retrieve a thread by ID asynchronously.
        
        Args:
            thread_id (str): The ID of the thread to retrieve
        
        Returns:
            The retrieved thread
        """
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
        return self.client.sync_client.beta.threads.messages.list(thread_id=thread_id)
    
    async def async_list_messages(self, thread_id):
        """
        List all messages in a thread asynchronously.
        
        Args:
            thread_id (str): The ID of the thread to list messages from
        
        Returns:
            List of messages in the thread
        """
        return await self.client.async_client.beta.threads.messages.list(thread_id=thread_id)


class AssistantsManager:
    """
    Manager class for OpenAI Assistants API assistants.
    
    This class provides methods for creating, retrieving, and managing assistants
    in the OpenAI Assistants API.
    
    Attributes:
        client (OpenAIClient): The OpenAI client to use for API calls
        thread_manager (ThreadManager): The thread manager to use for thread operations
        _assistants_cache (Dict[str, Assistant]): Cache of assistants by ID
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
        logger.info("AssistantsManager initialized")
    
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
    
    def get_run(self, thread_id, run_id):
        """
        Retrieve a run by ID.
        
        Args:
            thread_id (str): The ID of the thread
            run_id (str): The ID of the run to retrieve
        
        Returns:
            The retrieved run
        """
        return self.client.sync_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
    
    async def async_get_run(self, thread_id, run_id):
        """
        Retrieve a run by ID asynchronously.
        
        Args:
            thread_id (str): The ID of the thread
            run_id (str): The ID of the run to retrieve
        
        Returns:
            The retrieved run
        """
        return await self.client.async_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
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
        start_time = time.time()
        while time.time() - start_time < timeout:
            run = self.get_run(thread_id, run_id)
            
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
        start_time = time.time()
        while time.time() - start_time < timeout:
            run = await self.async_get_run(thread_id, run_id)
            
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
    
    def submit_tool_outputs(self, thread_id, run_id, tool_outputs):
        """
        Submit tool outputs for a run.
        
        Args:
            thread_id (str): The ID of the thread
            run_id (str): The ID of the run
            tool_outputs (List[Dict]): List of tool outputs
        
        Returns:
            The updated run
        """
        return self.client.sync_client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
    
    async def async_submit_tool_outputs(self, thread_id, run_id, tool_outputs):
        """
        Submit tool outputs for a run asynchronously.
        
        Args:
            thread_id (str): The ID of the thread
            run_id (str): The ID of the run
            tool_outputs (List[Dict]): List of tool outputs
        
        Returns:
            The updated run
        """
        return await self.client.async_client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
    
    def get_latest_message(self, thread_id):
        """
        Get the latest assistant message from a thread.
        
        Args:
            thread_id (str): The ID of the thread
        
        Returns:
            The latest assistant message, or None if there are no assistant messages
        """
        messages = self.client.sync_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=10
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
        messages = await self.client.async_client.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=10
        )
        
        for message in messages.data:
            if message.role == "assistant":
                return message
        
        return None
    
    def get_message_content(self, message):
        """
        Extract the text content from a message.
        
        Args:
            message (ThreadMessage): The message to extract content from
        
        Returns:
            str: The text content of the message
        """
        if not message or not message.content:
            return ""
        
        content_parts = []
        for content_item in message.content:
            if content_item.type == "text":
                content_parts.append(content_item.text.value)
        
        return "\n".join(content_parts)
    
    def upload_file(self, file_path, purpose="assistants"):
        """
        Upload a file to OpenAI.
        
        Args:
            file_path (str): Path to the file to upload
            purpose (str, optional): Purpose of the file. Defaults to "assistants".
        
        Returns:
            The uploaded file
        """
        with open(file_path, "rb") as file:
            return self.client.sync_client.files.create(
                file=file,
                purpose=purpose
            )
    
    async def async_upload_file(self, file_path, purpose="assistants"):
        """
        Upload a file to OpenAI asynchronously.
        
        Args:
            file_path (str): Path to the file to upload
            purpose (str, optional): Purpose of the file. Defaults to "assistants".
        
        Returns:
            The uploaded file
        """
        with open(file_path, "rb") as file:
            return await self.client.async_client.files.create(
                file=file,
                purpose=purpose
            )
    
    def upload_file_content(self, file_content, file_name, purpose="assistants"):
        """
        Upload file content to OpenAI.
        
        Args:
            file_content (bytes): Content of the file to upload
            file_name (str): Name of the file
            purpose (str, optional): Purpose of the file. Defaults to "assistants".
        
        Returns:
            The uploaded file
        """
        from tempfile import NamedTemporaryFile
        
        with NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            result = self.upload_file(temp_file_path, purpose=purpose)
        finally:
            os.unlink(temp_file_path)
        
        return result
    
    async def async_upload_file_content(self, file_content, file_name, purpose="assistants"):
        """
        Upload file content to OpenAI asynchronously.
        
        Args:
            file_content (bytes): Content of the file to upload
            file_name (str): Name of the file
            purpose (str, optional): Purpose of the file. Defaults to "assistants".
        
        Returns:
            The uploaded file
        """
        from tempfile import NamedTemporaryFile
        
        with NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            result = await self.async_upload_file(temp_file_path, purpose=purpose)
        finally:
            os.unlink(temp_file_path)
        
        return result 