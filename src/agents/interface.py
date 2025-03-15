# src/agents/interface.py
# Interface for interacting with the OpenAI Agents SDK
"""
This module provides a standardized interface for working with the OpenAI Agents SDK.
It handles error handling, retry logic, and tracing for agent operations.
"""

import os
import time
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic, Callable

# Use the centralized SDK imports
from ..sdk_imports import (
    Agent, Runner, RunConfig, RunResult, RunHooks, Tracing,
    ModelSettings, AgentsException, MaxTurnsExceeded,
    InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
    Span, get_current_trace, OpenAIProvider, SDK_AVAILABLE
)

# Local imports
from ..config import DEBUG_MODE, get_model_provider
from ..utils import format_error_message

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define a type variable for context
T = TypeVar('T')

class AgentInterface(Generic[T]):
    """
    A standardized interface for working with the OpenAI Agents SDK.
    
    This class provides a unified way to interact with agents, handling
    error conditions, retries, and tracing.
    
    Attributes:
        max_retries (int): Maximum number of retries for failed API calls
        retry_delay (float): Delay between retries in seconds
        tracing_enabled (bool): Whether tracing is enabled
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        tracing_enabled: bool = True
    ):
        """
        Initialize an AgentInterface instance.
        
        Args:
            max_retries (int): Maximum number of retries for failed API calls
            retry_delay (float): Delay between retries in seconds
            tracing_enabled (bool): Whether tracing is enabled
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.tracing_enabled = tracing_enabled
        
        # Initialize tracing if enabled
        if self.tracing_enabled:
            Tracing.enable()
            logger.debug("Agent tracing enabled")
    
    async def run_agent(self, agent: Agent[T], input_text: str, context: Optional[T] = None) -> RunResult:
        """
        Run an agent with input text.
        
        Args:
            agent (Agent): The agent to run
            input_text (str): The input text to process
            context (Optional[T]): The context to pass to the agent
            
        Returns:
            RunResult: The result of running the agent
        """
        # Get agent type from the agent name
        agent_type = agent.name.lower().replace(" ", "_")
        if "_agent" in agent_type:
            agent_type = agent_type.split("_agent")[0]
            
        logger.debug(f"Running agent: {agent.name} ({agent_type})")
        
        # Get the model provider for this agent type
        model_provider = get_model_provider(agent_type)
            
        for attempt in range(self.max_retries):
            try:
                # Create run config with model provider
                run_config = RunConfig(
                    workflow_name=f"{agent.name}_workflow",
                    model_provider=model_provider
                )
                
                logger.debug(f"Starting agent run with config: {run_config}")
                result = await Runner.run(
                    agent,
                    input_text,
                    context=context,
                    run_config=run_config
                )
                return result
            except AgentsException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed for {agent.name}: {str(e)}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {agent.name}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error running {agent.name}: {str(e)}")
                raise
    
    def run_agent_sync(
        self,
        agent: Agent[T],
        input_text: str,
        context: Optional[T] = None,
        max_turns: int = 10,
        hooks: Optional[RunHooks[T]] = None,
        run_config: Optional[RunConfig] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        Run an agent synchronously with retry logic and error handling.
        
        Args:
            agent (Agent[T]): The agent to run
            input_text (str): The input text to process
            context (Optional[T]): The context object
            max_turns (int): Maximum number of agent turns
            hooks (Optional[RunHooks[T]]): Hooks for agent lifecycle events
            run_config (Optional[RunConfig]): Configuration for the run
            
        Returns:
            Union[str, Dict[str, Any]]: The agent's response
        
        Raises:
            AgentsException: If the agent run fails after all retries
        """
        retries = 0
        current_delay = self.retry_delay
        
        while retries <= self.max_retries:
            try:
                logger.debug(f"Running agent {agent.name} synchronously (attempt {retries + 1}/{self.max_retries + 1})")
                
                # Create a span for this agent run if tracing is enabled
                span_name = f"{agent.name} run (sync)"
                with Span(name=span_name) as span:
                    span.add_attribute("input_length", len(input_text))
                    span.add_attribute("max_turns", max_turns)
                    
                    # Use the Runner to execute the agent synchronously
                    result = Runner.run_sync(
                        starting_agent=agent,
                        input=input_text,
                        context=context,
                        max_turns=max_turns,
                        hooks=hooks,
                        run_config=run_config
                    )
                    
                    # Log the successful response
                    span.add_attribute("status", "success")
                    span.add_attribute("turns_used", len(result.history))
                    
                    # Extract the final output
                    return result.final_output
                    
            except InputGuardrailTripwireTriggered as e:
                # Handle guardrail tripwires
                logger.warning(f"Input guardrail tripwire triggered: {str(e)}")
                return f"Input validation error: {str(e)}"
                
            except OutputGuardrailTripwireTriggered as e:
                # Handle guardrail tripwires
                logger.warning(f"Output guardrail tripwire triggered: {str(e)}")
                return f"Output validation error: {str(e)}"
                
            except MaxTurnsExceeded as e:
                # Handle max turns exceeded
                logger.warning(f"Max turns exceeded: {str(e)}")
                return "The agent took too many turns to complete the task."
                
            except AgentsException as e:
                # Handle agent exceptions
                logger.error(f"Agent error: {str(e)}")
                
                if retries < self.max_retries:
                    # Increment retry counter and delay
                    retries += 1
                    logger.info(f"Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                    
                    # Increase delay for next retry (exponential backoff)
                    current_delay *= 2
                else:
                    logger.error(f"Failed after {self.max_retries} retries")
                    return format_error_message(e, "Agent processing failed")
            
            except Exception as e:
                # Handle unexpected exceptions
                logger.exception(f"Unexpected error: {str(e)}")
                return format_error_message(e, "Unexpected error during agent execution")
    
    def create_run_config(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        workflow_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        **kwargs
    ) -> RunConfig:
        """
        Create a RunConfig object with the specified settings.
        
        Args:
            model (Optional[str]): Model override for all agents
            temperature (Optional[float]): Temperature setting
            max_tokens (Optional[int]): Maximum tokens for responses
            workflow_name (Optional[str]): Name for the workflow trace
            trace_id (Optional[str]): Custom trace ID
            **kwargs: Additional parameters for RunConfig
            
        Returns:
            RunConfig: Configured RunConfig object
        """
        # Create model settings if temperature or max_tokens are provided
        model_settings = None
        if temperature is not None or max_tokens is not None:
            model_settings = ModelSettings(
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        # Create the run config
        return RunConfig(
            model=model,
            model_provider=OpenAIProvider(),
            model_settings=model_settings,
            workflow_name=workflow_name or "Para-Phrase Generator workflow",
            trace_id=trace_id,
            tracing_disabled=not self.tracing_enabled,
            **kwargs
        ) 