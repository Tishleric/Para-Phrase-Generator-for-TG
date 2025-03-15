# Para-Phrase Generator

A Telegram bot that leverages OpenAI's APIs to provide intelligent conversation, information retrieval, and user profile management.

## Features

- **Message Summarization**: Summarizes conversations and provides concise responses.
- **Image Analysis**: Processes and analyzes images shared in the chat.
- **Link Processing**: Extracts and processes information from shared links.
- **Real-time Information**: Retrieves up-to-date information using web search capabilities.
- **Sports Information**: Provides real-time sports updates and information.
- **User Profile Management**: Maintains user profiles with preferences and interests.

## Architecture

The bot is built with a modular architecture:

- **Core Components**:
  - `TelegramBridge`: Handles Telegram API interactions
  - `AssistantsManager`: Manages OpenAI Assistants API integration
  - `UserProfileStore`: Vector database for user profile storage
  - `DelegationAssistant`: Routes messages to appropriate specialized assistants

- **Specialized Assistants**:
  - `ProfileAssistant`: Extracts and manages user profile information
  - `WebSearchAssistant`: Performs web searches for real-time information
  - `SportsAssistant`: Retrieves sports-related information
  - `PhotoAssistant`: Processes and analyzes images

## Setup

### Prerequisites

- Python 3.9+
- OpenAI API key
- Telegram Bot Token

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd Para-Phrase-Generator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```

### Running the Bot

Run the bot using:
```
python run.py
```

## Testing

The project includes several test scripts to verify functionality:

- `test_vector_store.py`: Tests the user profile vector store
- `test_assistants.py`: Tests the OpenAI Assistants API integration
- `test_profile_assistant.py`: Tests the profile assistant functionality

Run tests using:
```
python test_vector_store.py
python test_assistants.py
python test_profile_assistant.py
```

## Commands

The bot supports the following commands:

- `/start`: Initiates conversation with the bot
- `/help`: Displays help information
- `/profile`: Shows the user's profile information
- `/reset`: Resets the conversation thread

## Development

### Project Structure

```
├── agents/
│   ├── assistants_manager.py
│   ├── delegation_assistant.py
│   ├── profile_assistant.py
│   ├── sports_assistant.py
│   └── web_search_assistant.py
├── utils/
│   ├── telegram_bridge.py
│   └── user_profile_store.py
├── bot.py
├── run.py
├── requirements.txt
└── tests/
    ├── test_assistants.py
    ├── test_profile_assistant.py
    └── test_vector_store.py
```

## License

[MIT License](LICENSE) 