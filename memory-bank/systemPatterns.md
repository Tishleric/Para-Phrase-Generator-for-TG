# System Patterns - Para-Phrase Generator

## System Architecture

The system is structured as a multi-agent architecture built on top of the OpenAI Agents SDK. This architecture replaces the previous monolithic design with a modular approach where specialized agents handle different aspects of message processing and summarization.

### High-Level Architecture

```
┌──────────────────┐     ┌─────────────────────┐     ┌────────────────────┐
│                  │     │                     │     │                    │
│  Telegram Bot    │────►│  Delegation Agent   │────►│  Specialized       │
│  (Main Entry)    │     │  (Task Router)      │     │  Agents            │
│                  │     │                     │     │                    │
└──────────────────┘     └─────────────────────┘     └────────────────────┘
                                   │                            │
                                   │                            │
                                   ▼                            ▼
                         ┌─────────────────────┐     ┌────────────────────┐
                         │                     │     │                    │
                         │  Message Store      │     │  External APIs     │
                         │  (Context)          │     │  (Web Search, etc) │
                         │                     │     │                    │
                         └─────────────────────┘     └────────────────────┘
```

### Agent Structure

The multi-agent system follows a delegation pattern:

1. **Entry Point:** The Telegram bot receives commands and messages.
2. **Delegation:** The delegation agent determines what type of content needs processing.
3. **Specialized Processing:** Task-specific agents handle different content types.
4. **Result Integration:** Results are compiled into a coherent summary.

## Key Design Patterns

### Delegation Pattern
The system uses a delegation pattern where a central agent analyzes content and delegates to specialized agents. This pattern:
- Keeps each agent focused on a specific task
- Allows for independent development of agents
- Simplifies testing by isolating functionality

### Agent Base Class and Inheritance
All agents inherit from a base agent class that:
- Standardizes construction and API calls
- Provides common utility methods
- Enforces consistent behavior

### Centralized SDK Import Strategy
A central `sdk_imports.py` file manages all interactions with the OpenAI Agents SDK:
- Provides fallback mock implementations for testing
- Isolates the rest of the codebase from SDK changes
- Simplifies development when the SDK is not available

### Composition Over Inheritance
For specialized functionality, we favor composition over deep inheritance hierarchies:
- Agents use tool functions for specialized capabilities
- Functionality is encapsulated in utility classes
- This approach is more flexible for future enhancements

### Context Sharing
Context is shared between agents through:
- Handoff mechanisms provided by the SDK
- Common context objects passed during delegation
- A central message store for access to chat history

## Agent Implementations

### Delegation Agent
- **Purpose:** Central router that inspects content and delegates tasks
- **Responsibilities:**
  - Analyze message content for special patterns (Twitter links, football references, images)
  - Delegate to appropriate specialized agents based on content analysis
  - Compile results into coherent summaries

### Twitter Link Agent
- **Purpose:** Process Twitter links found in messages
- **Responsibilities:**
  - Identify Twitter links using pattern matching
  - Extract key information from the links
  - Summarize tweet content for inclusion in the overall summary

### Football Agent
- **Purpose:** Detect and provide context for football-related content
- **Responsibilities:**
  - Identify football references (teams, players, scores, etc.)
  - Use web search to find relevant information about mentioned matches
  - Return contextualized information for inclusion in summaries
- **Enhancement:** Will eventually use vector store for user team preferences

### Tone-Specific Summary Agent
- **Purpose:** Generate summaries in specified tones
- **Responsibilities:**
  - Create summaries following tone-specific guidelines
  - Incorporate results from specialized agents
  - Format output for Telegram display

### Photo Content Analysis Agent (In Progress)
- **Purpose:** Analyze images shared in the chat
- **Responsibilities:**
  - Process image data from Telegram
  - Use OCR or image recognition as appropriate
  - Generate textual descriptions of image content

## SDK Integration Patterns

### Agent Creation and Configuration
Agents are created with:
- Descriptive names for tracing
- Clear instructions for the model
- Relevant tools registered with the agent
- Appropriate handoffs to other agents

```python
agent = Agent(
    name="DelegationAgent",
    instructions="You are responsible for analyzing message content and delegating to specialized agents.",
    tools=[analyze_messages_tool],
    handoffs=[
        Handoff(twitter_agent, lambda message: "twitter.com" in message),
        Handoff(football_agent, lambda message: contains_football_reference(message))
    ]
)
```

### Tool Function Pattern
Tool functions follow a consistent pattern:
- Clear type hints for parameters and return values
- Comprehensive docstrings for the model
- Proper error handling
- Return structured data when possible

```python
@function_tool
def analyze_messages_tool(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze messages to identify content types and patterns.
    
    Args:
        messages: List of message dictionaries with sender, text, and metadata
        
    Returns:
        Dictionary containing identified content types and relevant metadata
    """
    # Implementation
```

### Error Handling Pattern
Error handling follows a defensive approach:
- Validate inputs before processing
- Use try/except blocks for external API calls
- Provide useful fallbacks when primary methods fail
- Return structured error information when needed

## Testing Patterns

### Mock SDK for Testing
The testing approach uses mock implementations of the SDK:
- Allows tests to run without the actual SDK installed
- Simulates SDK behaviors for predictable testing
- Provides detailed diagnostics for test failures

### Component Testing
Each component is tested in isolation:
- Agent-specific test suites
- Tool function unit tests
- Pattern matching function tests

### Integration Testing
Integration tests verify agent interactions:
- Delegation flows between agents
- Context passing between components
- End-to-end processing of sample messages

## Agent Architecture

We're using a multi-agent architecture with the following components:

1. **Delegation Agent**
   - Central coordinator that routes messages to specialized agents
   - Maintains a registry of available agents
   - Decides which agent(s) should handle each message

2. **Specialized Agents**
   - **Twitter Link Detection Agent**
     - Detects Twitter links in messages
     - Extracts and summarizes tweet content
     - Provides context about the tweet

   - **Football Score Agent**
     - Detects football match references
     - Uses web search for live game information
     - Processes various types of football content:
       - Match scores and team mentions
       - Live commentary and excited player references
       - Provides rich context about matches and players

## Web Search Integration Pattern

The Football Score Agent demonstrates our pattern for integrating web search:

1. **Detection First**: Always analyze the message content first before searching
2. **Targeted Queries**: Generate specific search queries based on detected content
3. **Prioritized Results**: Focus on recent events (last 24 hours) for real-time context
4. **Fallback Mechanism**: Provide value even when web search fails

This pattern can be reused for other agents that need web search capabilities.

## Agent Interface Pattern

All specialized agents follow a consistent interface pattern:

1. **BaseAgent Class Inheritance**
   - Common initialization with name, instructions, model, tools
   - Consistent calling mechanism

2. **Agent-Specific Tool Functions**
   - Each agent defines specialized tool functions for its domain
   - Tools are decorated with @function_tool

3. **Main Processing Method**
   - Each agent has a main processing method (e.g., process_twitter_links, process_football_references)
   - Returns a string summary or None if nothing relevant found

4. **Testing Pattern**
   - Each agent has comprehensive unit tests
   - Mock Agent/tools to avoid API calls during testing

## Dictionary-Based Entity Recognition

For entity recognition (teams, players, etc.), we use dictionary-based matching:

1. **Comprehensive Dictionaries**: Maintain dictionaries of common entities
2. **Alias Handling**: Support multiple aliases for the same entity
3. **Standardization**: Map variations to standard entity names
4. **Confidence Levels**: Assign confidence levels based on match quality

This pattern can be reused for any domain that requires entity recognition.

## User Preference Integration (Planned)

We plan to implement a vector store integration pattern:

1. **User Preferences Storage**: Store user-specific preferences in vector store
2. **Context Enhancement**: Use preferences to enhance agent responses
3. **Personalization Layer**: Apply as a final layer on top of agent processing 