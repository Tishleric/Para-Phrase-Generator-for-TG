"""
OpenAI Agents SDK Import Module

This module centralizes all imports from the OpenAI Agents SDK and provides
fallbacks for testing when the SDK is not available.

Usage:
    from src.sdk_imports import Agent, Runner, RunConfig, etc.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flag for SDK availability
SDK_AVAILABLE = True

# Try to import from installed package
try:
    # Import directly from the installed package
    from agents import (
        Agent, Runner, RunConfig, RunResult, RunHooks,
        ModelSettings, AgentsException, MaxTurnsExceeded,
        InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
        set_default_openai_key, Handoff, InputGuardrail, OutputGuardrail, function_tool,
        WebSearchTool, Tracing, Span, get_current_trace, trace
    )
    from agents.guardrail import Guardrail, GuardrailFunctionOutput
    from agents.models.openai_provider import OpenAIProvider
    
    # Set the OpenAI API key for the SDK
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        set_default_openai_key(openai_api_key)
        
    logger.info("OpenAI Agents SDK imported successfully from installed package")
except ImportError as e:
    # SDK is not available, provide mock implementations for testing
    logger.warning(f"OpenAI Agents SDK not available. Using mock implementations for testing. Error: {str(e)}")
    SDK_AVAILABLE = False
    
    # Define type variable for generic classes
    T = TypeVar('T')
    TSpanData = TypeVar('TSpanData')
    TContext = TypeVar('TContext')
    
    # Mock implementations for testing
    class Agent(Generic[T]):
        """Mock Agent class"""
        def __init__(self, name: str = "", instructions: str = "", model: str = "", model_settings: Any = None, tools: List = None, handoffs: List = None, guardrails: List = None):
            self.name = name
            self.instructions = instructions
            self.model = model
            self.model_settings = model_settings
            self.tools = tools or []
            self.handoffs = handoffs or []
            self.guardrails = guardrails or []
            
        def run(self, input_text: str, **kwargs):
            """Mock run method"""
            return f"Mock response from {self.name}"
    
    class ModelSettings:
        """Mock ModelSettings class"""
        def __init__(self, temperature: float = 0.7, max_tokens: int = 100):
            self.temperature = temperature
            self.max_tokens = max_tokens
    
    class RunConfig:
        """Mock RunConfig class"""
        def __init__(self, workflow_name: str = "", temperature: float = 0.7, max_tokens: int = 100, **kwargs):
            self.workflow_name = workflow_name
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.kwargs = kwargs
    
    class RunResult:
        """Mock RunResult class"""
        def __init__(self, output: str = "", response: Dict[str, Any] = None):
            self.output = output
            self.response = response or {}
            self.history = []
            self.final_output = output
    
    class Runner:
        """Mock Runner class"""
        @staticmethod
        async def run(starting_agent: Agent, input: str, context: Any = None, max_turns: int = 10, hooks: Any = None, run_config: RunConfig = None):
            """Mock async run method"""
            result = RunResult(output=f"Mock response from {starting_agent.name}")
            result.history = [{"role": "assistant", "content": result.output}]
            result.final_output = result.output
            return result
            
        @staticmethod
        def run_sync(starting_agent: Agent, input: str, context: Any = None, max_turns: int = 10, hooks: Any = None, run_config: RunConfig = None):
            """Mock sync run method"""
            result = RunResult(output=f"Mock response from {starting_agent.name}")
            result.history = [{"role": "assistant", "content": result.output}]
            result.final_output = result.output
            return result
    
    class RunHooks(Generic[T]):
        """Mock RunHooks class"""
        def __init__(self):
            pass
            
        def on_agent_start(self, agent: Agent[T], context: Optional[T] = None):
            """Mock on_agent_start method"""
            pass
            
        def on_agent_end(self, agent: Agent[T], context: Optional[T] = None):
            """Mock on_agent_end method"""
            pass
    
    class AgentsException(Exception):
        """Mock AgentsException class"""
        pass
    
    class MaxTurnsExceeded(AgentsException):
        """Mock MaxTurnsExceeded class"""
        pass
    
    class InputGuardrailTripwireTriggered(AgentsException):
        """Mock InputGuardrailTripwireTriggered class"""
        pass
    
    class OutputGuardrailTripwireTriggered(AgentsException):
        """Mock OutputGuardrailTripwireTriggered class"""
        pass
    
    class Handoff:
        """Mock Handoff class"""
        def __init__(self, target: Agent = None, filter: Callable = None):
            self.target = target
            self.filter = filter
    
    class GuardrailFunctionOutput:
        """Mock GuardrailFunctionOutput class"""
        def __init__(self, output_info: Any = None, tripwire_triggered: bool = False):
            self.output_info = output_info
            self.tripwire_triggered = tripwire_triggered
    
    class Guardrail(Generic[TContext]):
        """Mock Guardrail base class"""
        def __init__(self, guardrail_function: Callable = None, name: str = None):
            self.guardrail_function = guardrail_function
            self.name = name
            
        def get_name(self) -> str:
            if self.name:
                return self.name
            return self.guardrail_function.__name__ if self.guardrail_function else "unnamed_guardrail"
            
    class InputGuardrail(Guardrail[TContext]):
        """Mock InputGuardrail class"""
        def __init__(self, guardrail_function: Callable = None, name: str = None):
            super().__init__(guardrail_function, name)
            
        async def run(self, agent: Agent, input: str, context: Any = None):
            if not self.guardrail_function:
                return {"tripwire_triggered": False}
            return await self.guardrail_function(context, agent, input)
            
    class OutputGuardrail(Guardrail[TContext]):
        """Mock OutputGuardrail class"""
        def __init__(self, guardrail_function: Callable = None, name: str = None):
            super().__init__(guardrail_function, name)
            
        async def run(self, agent: Agent, output: Any, context: Any = None):
            if not self.guardrail_function:
                return {"tripwire_triggered": False}
            return await self.guardrail_function(context, agent, output)
    
    def function_tool(func: Callable = None, **kwargs):
        """Mock function_tool decorator"""
        if func is None:
            return lambda f: f
        return func
    
    class WebSearchTool:
        """Mock WebSearchTool class"""
        def __init__(self):
            self.name = "web_search"
            self.description = "Search the web for information"
        
        def run(self, query: str):
            """Mock run method for web search"""
            return {
                "results": [
                    {
                        "title": f"Mock search result for: {query}",
                        "link": "https://example.com/mock-result",
                        "snippet": f"This is a mock search result for the query: {query}. " 
                                 f"It contains synthetic information for testing purposes."
                    }
                ]
            }
    
    class OpenAIProvider:
        """Mock OpenAIProvider class"""
        def __init__(self, api_key: str = ""):
            self.api_key = api_key
    
    def set_default_openai_key(key: str):
        """Mock set_default_openai_key function"""
        pass

    class RunContextWrapper:
        """Mock RunContextWrapper class"""
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            
        def to_dict(self):
            """Convert context to dictionary"""
            return self.kwargs
    
    # Mock Tracing classes
    class Span(Generic[TSpanData]):
        """Mock Span class"""
        def __init__(self, trace_id: str = "mock_trace_id", span_id: str = "mock_span_id", parent_id: Optional[str] = None, span_data: Any = None):
            self.trace_id = trace_id
            self.span_id = span_id
            self.parent_id = parent_id
            self.span_data = span_data
            self.started_at = None
            self.ended_at = None
            
        def __enter__(self):
            self.start()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.finish()
            
        def start(self):
            """Mock start method"""
            import time
            self.started_at = time.time()
            return self
            
        def finish(self):
            """Mock finish method"""
            import time
            self.ended_at = time.time()
            return self
    
    class Trace:
        """Mock Trace class"""
        def __init__(self, name: str = "mock_trace", trace_id: str = "mock_trace_id", group_id: Optional[str] = None, metadata: Dict[str, Any] = None):
            self.name = name
            self.trace_id = trace_id
            self.group_id = group_id
            self.metadata = metadata or {}
            self.started_at = None
            self.ended_at = None
            self.spans = []
            
        def __enter__(self):
            self.start()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.finish()
            
        def start(self):
            """Mock start method"""
            import time
            self.started_at = time.time()
            return self
            
        def finish(self):
            """Mock finish method"""
            import time
            self.ended_at = time.time()
            return self
            
        def add_span(self, span: Span):
            """Add span to trace"""
            self.spans.append(span)
    
    class Tracing:
        """Mock Tracing class"""
        @staticmethod
        def create_trace(name: str = "mock_trace", trace_id: Optional[str] = None, group_id: Optional[str] = None, metadata: Dict[str, Any] = None):
            """Create a trace"""
            return Trace(name=name, trace_id=trace_id or "mock_trace_id", group_id=group_id, metadata=metadata)
            
        @staticmethod
        def create_span(trace_id: str, span_id: Optional[str] = None, parent_id: Optional[str] = None, span_data: Any = None):
            """Create a span"""
            return Span(trace_id=trace_id, span_id=span_id or "mock_span_id", parent_id=parent_id, span_data=span_data)
            
        @staticmethod
        def enable():
            """Mock enable method"""
            logger.info("Mock tracing enabled")
            return True
            
        @staticmethod
        def disable():
            """Mock disable method"""
            logger.info("Mock tracing disabled")
            return True
    
    def get_current_trace() -> Optional[Trace]:
        """Mock get_current_trace function"""
        return None
        
    def trace(name: str = "mock_trace", trace_id: Optional[str] = None, group_id: Optional[str] = None, metadata: Dict[str, Any] = None):
        """Mock trace context manager"""
        return Trace(name=name, trace_id=trace_id, group_id=group_id, metadata=metadata)

# Export all the classes and functions
__all__ = [
    "Agent", "Runner", "RunConfig", "RunResult", "RunHooks",
    "ModelSettings", "AgentsException", "MaxTurnsExceeded",
    "InputGuardrailTripwireTriggered", "OutputGuardrailTripwireTriggered",
    "OpenAIProvider", "set_default_openai_key",
    "Handoff", "InputGuardrail", "OutputGuardrail", "function_tool", 
    "SDK_AVAILABLE", "WebSearchTool", "RunContextWrapper", "Guardrail",
    "GuardrailFunctionOutput", "Tracing", "Span", "get_current_trace", "trace"
] 