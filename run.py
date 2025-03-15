"""
Run script for the Para-Phrase Generator.

This script runs the Telegram bot and handles errors gracefully.
"""

import os
import sys
import logging
import traceback
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to run the bot.
    """
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file or environment.")
        return
    
    try:
        # Import the bot module
        import bot
        
        # Log startup
        logger.info("Starting Para-Phrase Generator...")
        
        # Run the bot
        bot.bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 