# Agent Architecture Documentation

## Overview

This project implements a flexible agent-based architecture using the OpenAI Agents SDK. The architecture follows a delegation pattern, where a main coordinator agent can analyze input and route it to specialized sub-agents based on content type and requirements.

## Core Components

### 1. SDK Imports (`src/sdk_imports.py`)

This module serves as an abstraction layer that imports necessary components from the OpenAI Agents SDK. It provides fallback mock implementations for testing when the actual SDK is unavailable.

Key components imported:
- `Agent`: The main agent class for creating AI assistants
- `Runner`: Executes agent workflows
- `RunConfig`: Configuration for agent execution
- `function_tool`: Decorator for creating function tools
- `WebSearchTool`: Built-in tool for web searches
- `ModelSettings`: Configuration for the agent's model behavior

### 2. Agent Types

The architecture supports several types of agents:

#### Main Delegation Agent
- Serves as the entry point and coordinator
- Analyzes input to determine which specialized agent should handle it
- Can process general inputs itself
- Manages handoffs to specialized agents

#### Specialized Agents
- **Twitter Link Agent**: Processes Twitter/X links and extracts key information
- **Photo Analysis Agent**: Analyzes images and describes content
- **Football Score Agent**: Provides context for football-related conversations

### 3. Tools

Agents can use various tools to enhance their capabilities:

#### Built-in SDK Tools
- `WebSearchTool`: Searches the web for information

#### Custom Function Tools
- `get_current_time()`: Returns the current time
- `analyze_message()`: Performs basic analysis on message text

## Flow of Execution

1. User input is received and formatted
2. The delegation agent analyzes the input
3. If specialized handling is needed, the delegation agent hands off to the appropriate specialized agent
4. The specialized agent processes the input and returns a result
5. The final output is returned to the user

## Code Structure

```
├── src/
│   ├── sdk_imports.py         # SDK abstraction layer
│   └── ...
├── agent_example.py           # Example implementation
├── agent_architecture.md      # This documentation
└── test_agents_sdk.py         # Test script
```

## Example Usage

The `agent_example.py` script demonstrates the architecture with three example use cases:

1. Regular conversation summarization
2. Football-related conversation analysis
3. Twitter link processing

Each example shows how the delegation agent analyzes the content and routes it appropriately, applying different tones to the final output.

## Implementation Details

### Agent Creation

Agents are created with specific instructions that define their purpose and behavior. For example:

```python
agent = Agent(
    name="Delegation Agent",
    instructions="""You are the main coordinator for a message summarization system.
    Analyze the messages and determine if they contain:
    - Twitter/X links (hand off to Twitter Link Agent)
    - Photos/images (hand off to Photo Analysis Agent)
    - Football references (hand off to Football Score Agent)
    
    If none of these special cases apply, process the message yourself...
    """,
    model="gpt-3.5-turbo",
    tools=[analyze_message, get_current_time],
    handoffs=[twitter_agent, photo_agent, football_agent],
    model_settings=ModelSettings(temperature=0.7)
)
```

### Message Processing

Messages are processed asynchronously:

```python
async def process_messages(messages, tone="stoic"):
    # Format messages for the agent
    formatted_messages = f"""
    The following is a conversation between several users:
    
    {messages}
    
    Summarize this conversation in a {tone} tone.
    """
    
    # Create and run the delegation agent
    delegation_agent = create_delegation_agent()
    
    result = await Runner.run(
        delegation_agent,
        input=formatted_messages,
        run_config=RunConfig(workflow_name=f"Message Summary - {tone} tone")
    )
    
    return result.final_output
```

## Extending the Architecture

To add a new specialized agent:

1. Create a new agent creation function similar to `create_twitter_agent()`
2. Configure it with appropriate instructions, model, and tools
3. Add it to the handoffs list in the delegation agent
4. Update the delegation agent's instructions to include the new specialization

## Best Practices

- Each agent should have clear, specific instructions
- Keep the delegation logic simple and explicit
- Use appropriate models for each agent (e.g., vision models for image processing)
- Set appropriate temperature values based on the required creativity/precision balance
- Implement proper error handling for when handoffs fail 