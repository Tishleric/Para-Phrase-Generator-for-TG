# Telegram Message Summarization Bot (Para-Phrase Generator)

A Telegram bot that summarizes messages using a multi-agent architecture with OpenAI Agents.

## Features

- Summarize recent messages with the `/last N` command
- Customize summary tone with `/tone TYPE` (stoic, chaotic, pubbie, deaf)
- Multi-agent architecture for specialized content processing:
  - Twitter link detection and summarization
  - Image content analysis
  - Football score context
  - User profile-aware personalization

## Architecture

The bot uses a multi-agent architecture based on the OpenAI Agents SDK:

- **Delegation Agent**: Routes requests to specialized agents based on content
- **Tone-Specific Agents**: Generate summaries in different tones (stoic, chaotic, pubbie, deaf)
- **Specialized Content Agents**: Process specific content types (Twitter links, images, etc.)
- **Context Management**: Maintains state across agent handoffs

## Setup

### Prerequisites

- Python 3.8+
- A Telegram Bot token (from [BotFather](https://t.me/botfather))
- Anthropic API key (for legacy summarization)
- OpenAI API key (for agent-based summarization)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/para-phrase-generator.git
cd para-phrase-generator
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create your environment file:
```bash
cp .env.example .env
# Edit .env with your API keys and tokens
```

### Configuration

Edit the `.env` file with your API keys and configuration options:

```
# API Keys
ANTHROPIC_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_token_here

# Feature Flags
DEBUG_MODE=false
USE_AGENT_SYSTEM=true
```

- `USE_AGENT_SYSTEM`: Set to `true` to use the new agent-based architecture, or `false` to use the legacy system
- `DEBUG_MODE`: Set to `true` to enable debug logging

### Running the Bot

```bash
python bot.py
```

## Testing the Agent Framework

To test the new agent framework:

```bash
python -m src.test_agents
```

## Project Structure

```
├── bot.py                  # Main Telegram bot implementation
├── summarizer.py           # Legacy summarization engine
├── requirements.txt        # Project dependencies
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── Procfile                # Heroku deployment configuration
└── src/                    # New agent-based architecture
    ├── __init__.py
    ├── config.py           # Configuration and settings
    ├── utils.py            # Utility functions
    ├── test_agents.py      # Test script for agents
    └── agents/             # Agent implementations
        ├── __init__.py
        ├── base_agent.py   # Base agent class
        ├── delegation_agent.py  # Main orchestration agent
        └── tone_agent.py   # Tone-specific summary agent
```

## Usage

1. Add the bot to a Telegram group
2. The bot will listen to all messages and store them
3. Use `/last N` to get a summary of the last N messages (e.g., `/last 10`)
4. Use `/tone TYPE` to set the summary tone (stoic, chaotic, pubbie, deaf)

## Development

The project is currently transitioning from a monolithic architecture to a multi-agent system based on the OpenAI Agents framework. The implementation is being done in phases, with each phase building on the previous one.

## License

[MIT License](LICENSE) 