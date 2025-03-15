# Technical Context - Para-Phrase Generator

## Technologies Used

### Core Technologies
1. **Python 3.x**: Main programming language
2. **Telegram Bot API**: For interacting with Telegram's messaging platform
3. **Anthropic Claude 3.7 Sonnet**: LLM used for generating message summaries
4. **OpenAI Agents SDK**: Framework for building multi-agent workflows

### Libraries and Frameworks
1. **pyTelegramBotAPI (v4.14.0)**: Python wrapper for the Telegram Bot API
2. **anthropic (v0.49.0)**: Python client for the Anthropic API
3. **python-dotenv (v1.0.0)**: For loading environment variables from .env files
4. **openai-agents**: OpenAI's SDK for building agentic systems with LLMs

### Infrastructure
- **Deployment**: The bot can be run locally or deployed to a cloud platform (setup for Heroku with Procfile)
- **Persistence**: Currently in-memory with no database (messages are lost on restart)
- **State Management**: Dictionary-based storage for message history and tone preferences

## Development Setup

### Prerequisites
- Python 3.x installed
- Telegram Bot token (obtained from BotFather)
- Anthropic API key
- OpenAI API key (for Agents SDK)

### Local Development
1. **Environment Setup**:
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd para-phrase-generator
   
   # Create a virtual environment (optional but recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configuration**:
   ```bash
   # Copy the example .env file
   cp .env.example .env
   
   # Edit .env with your API keys
   TELEGRAM_API_TOKEN=your_telegram_bot_token
   ANTHROPIC_API_KEY=your_anthropic_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Running the Bot**:
   ```bash
   # Run the bot locally
   python bot.py
   ```

## Technical Constraints

### Telegram Bot API Limitations
- Messages over 4096 characters are split into multiple messages
- Rate limiting for bot interactions (up to 30 messages per second)
- Limited formatting options for messages (Markdown and HTML)

### LLM Integration Considerations
- API rate limits and token quotas
- Potential for content moderation filters
- Maximum token context windows (varies by model)

### Multi-Agent Architecture Considerations
- Handoff mechanisms between agents must be reliable
- Tool function interfaces need to be consistent
- Context must be properly passed between agents

## SDK Versioning and Compatibility

### OpenAI Agents SDK
- Using the latest version of the SDK (subject to updates)
- Core functionality relies on:
  - Agent class for agent creation
  - Runner for agent execution
  - Handoff for agent delegation
  - function_tool for tool registration
  - WebSearchTool for web search capabilities

### SDK Import Strategy
- Centralized imports through `src/sdk_imports.py`
- Mock implementations for testing when SDK is not available
- Fallback mechanisms for development without SDK access

## Project Structure

### Key Files and Directories
- **bot.py**: Main entry point for the Telegram bot
- **summarizer.py**: Legacy summarization logic (being refactored)
- **src/**: Directory containing all modular components
  - **agents/**: Directory for all agent implementations
    - **base_agent.py**: Base class for all agents
    - **delegation_agent.py**: Agent responsible for task routing
    - **twitter_agent.py**: Agent for Twitter link processing
    - **football_agent.py**: Agent for football reference processing
    - **tone_agent.py**: Agent for tone-specific summarization
  - **sdk_imports.py**: Centralized SDK import handling
  - **utils.py**: Utility functions for the application
  - **config.py**: Configuration constants and settings
  - **model_utility.py**: Utilities for working with LLMs

### Testing Structure
- **tests/**: Directory containing all test files
- **src/test_*.py**: Unit tests for specific components

## API Usage and Integration

### Anthropic Claude API
- Used for generating summarizations with specific tones
- Structured prompt templates for consistent outputs
- Error handling for API failures

### Telegram Bot API
- Webhook vs. Polling considerations
- Message handling and command parsing
- User and group management

### OpenAI API
- Used via Agents SDK for agent orchestration
- Tool registration for custom functionality
- Context management between agent handoffs

## Future Technical Considerations

### Scalability
- Potential migration to a database for message persistence
- Caching mechanisms for frequently requested summaries
- Horizontal scaling for handling multiple chat groups

### Security
- API key management and rotation
- Input validation and sanitization
- Rate limiting for bot commands

### Monitoring
- Logging for debugging and analytics
- Performance metrics collection
- Error tracking and alerting 