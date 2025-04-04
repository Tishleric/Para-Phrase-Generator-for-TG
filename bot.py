# bot.py
# Main file to run the Telegram bot for message summarization
import telebot
import os
import logging
import traceback
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Union
import sys

# Import utility functions and classes
from src.telegram_bridge import TelegramBridge, format_error_message
from src.utils import extract_command_args

# Import configuration
from src.config import (
    DEBUG_MODE, USE_AGENT_SYSTEM, MAX_MESSAGES_PER_CHAT,
    AVAILABLE_TONES, DEFAULT_TONE, ADD_MESSAGE_LINKS, ENABLE_IMAGE_ANALYSIS
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Set default environment
ENVIRONMENT = os.environ.get('BOT_ENVIRONMENT', 'production')
logger.info(f"Bot running in {ENVIRONMENT} environment")

# Print startup information
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if token:
    # Mask the token for security, only show first 10 chars
    masked_token = token[:10] + "..." + token[-5:]
    print(f"Starting bot with token: {masked_token}")
    print(f"Environment: {ENVIRONMENT}")
    print("Bot is initializing...")
else:
    print("ERROR: No Telegram token found in environment variables!")

bot = telebot.TeleBot(os.environ.get("TELEGRAM_BOT_TOKEN"))
chat_history = {}  # {chat_id: [list of messages]}
chat_tones = {}  # {chat_id: tone}

# Initialize the TelegramBridge for agent integration
telegram_bridge = TelegramBridge(chat_history, chat_tones)

@bot.message_handler(commands=['tone'])
def set_tone(message):
    try:
        # Extract the tone from the message
        command, args = extract_command_args(message.text)
        
        if not args:
            bot.reply_to(message, f"Please specify a tone. Available tones: {', '.join(AVAILABLE_TONES)}")
            return
        
        tone = args[0].lower()
        
        if USE_AGENT_SYSTEM:
            # Use the TelegramBridge to handle the command
            response = telegram_bridge.handle_command(message.__dict__, command, args)
            
            if response:
                bot.reply_to(message, response)
                return
        
        # Legacy system (or agent system not enabled)
        if tone not in AVAILABLE_TONES:
            bot.reply_to(message, f"Invalid tone. Available tones: {', '.join(AVAILABLE_TONES)}")
            return
        
        chat_id = str(message.chat.id)
        chat_tones[chat_id] = tone
        
        bot.reply_to(message, f"Tone set to {tone}!")
        
    except Exception as e:
        logger.error(f"Error in set_tone: {e}")
        logger.error(traceback.format_exc())
        bot.reply_to(message, format_error_message(e))

@bot.message_handler(commands=['last'])
def last_messages(message):
    try:
        # Extract the count from the message
        command, args = extract_command_args(message.text)
        
        if not args:
            bot.reply_to(message, "Please specify the number of messages to summarize.")
            return
        
        try:
            count = int(args[0])
        except ValueError:
            bot.reply_to(message, "Please specify a valid number of messages to summarize.")
            return
        
        if count <= 0:
            bot.reply_to(message, "Please specify a positive number of messages to summarize.")
            return
        
        chat_id = str(message.chat.id)
        
        if chat_id not in chat_history or not chat_history[chat_id]:
            bot.reply_to(message, "No messages to summarize.")
            return
        
        # Send a "processing" message to indicate the bot is working
        processing_message = bot.reply_to(message, "Processing your request... This may take a moment.")
        
        if USE_AGENT_SYSTEM:
            # Use the TelegramBridge to handle the command
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(telegram_bridge.handle_command(message.__dict__, command, args))
            finally:
                loop.close()
            
            if response:
                # Delete the processing message
                bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
                
                # Handle potential parsing of HTML in Telegram
                try:
                    bot.reply_to(message, response, parse_mode="HTML")
                except Exception as html_error:
                    logger.error(f"Error sending HTML message: {html_error}")
                    # Fall back to plain text if HTML parsing fails
                    bot.reply_to(message, response)
                return
        
        # Legacy system (or agent system not enabled)
        # Get the tone for this chat
        tone = chat_tones.get(chat_id, DEFAULT_TONE)
        
        # Call the legacy summarization method
        from summarizer import summarize_messages
        
        # Get the most recent 'count' messages
        messages = chat_history[chat_id][-count:] if count <= len(chat_history[chat_id]) else chat_history[chat_id]
        
        summary = summarize_messages(messages, tone)
        
        # Delete the processing message
        bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        
        bot.reply_to(message, summary)
        
    except Exception as e:
        logger.error(f"Error in last_messages: {e}")
        logger.error(traceback.format_exc())
        bot.reply_to(message, format_error_message(e))

@bot.message_handler(commands=['profile'])
def profile_command(message):
    try:
        # Extract the arguments from the message
        command, args = extract_command_args(message.text)
        
        if USE_AGENT_SYSTEM:
            # Use the TelegramBridge to handle the command
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(telegram_bridge.handle_command(message.__dict__, command, args))
            finally:
                loop.close()
            
            if response:
                bot.reply_to(message, response)
                return
        
        # If we get here, either agent system is disabled or the command wasn't handled
        bot.reply_to(message, "Profile command is only available with the agent system enabled.")
        
    except Exception as e:
        logger.error(f"Error in profile_command: {e}")
        logger.error(traceback.format_exc())
        bot.reply_to(message, format_error_message(e))

@bot.message_handler(func=lambda message: True)
def store_message(message):
    try:
        chat_id = str(message.chat.id)
        
        # Store the message using the TelegramBridge
        telegram_bridge.store_message(message.__dict__)
        
    except Exception as e:
        logger.error(f"Error in store_message: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    print("Bot is starting...")
    
    # Log startup information
    logger.info("Para-Phrase Generator is starting")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Debug mode: {DEBUG_MODE}")
    logger.info(f"Agent system: {'Enabled' if USE_AGENT_SYSTEM else 'Disabled'}")
    logger.info(f"Message linking: {'Enabled' if ADD_MESSAGE_LINKS else 'Disabled'}")
    logger.info(f"Image analysis: {'Enabled' if ENABLE_IMAGE_ANALYSIS else 'Disabled'}")
    
    # Check for API keys
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("No OpenAI API key found. Agent system will fail.")
    
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        logger.error("No Telegram bot token found. Bot will fail to initialize.")
        sys.exit(1)
    
    # Check for Twitter API token
    if os.environ.get("TWITTER_BEARER_TOKEN"):
        logger.info("Twitter API token found. Twitter link parsing will be fully functional.")
    else:
        logger.warning("No Twitter API token found. Twitter link processing will be limited.")
    
    # Start the bot
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Critical error in bot polling: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 