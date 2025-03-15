"""
Run script for the Para-Phrase Generator.

This script runs the Telegram bot and handles errors gracefully.
"""

import os
import sys
import time
import logging
import argparse
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Para-Phrase Generator bot')
    parser.add_argument('--env', choices=['staging', 'production'], default='production',
                      help='Specify the environment to run the bot in (default: production)')
    parser.add_argument('--debug', action='store_true', 
                      help='Run in debug mode with more verbose logging')
    args = parser.parse_args()
    
    # Set environment variables based on selected environment
    os.environ['BOT_ENVIRONMENT'] = args.env
    if args.debug:
        os.environ['DEBUG_MODE'] = 'true'
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Load environment variables
    load_dotenv()
    logger.info(f"Starting bot in {args.env} environment")
    
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
        logger.info(f"Environment: {args.env}")
        
        # Add a flag to distinguish between staging and production
        bot.ENVIRONMENT = args.env
        
        # Run the bot with reconnection logic
        while True:
            try:
                logger.info("Bot polling started")
                bot.bot.polling(none_stop=True, timeout=60)
            except Exception as polling_error:
                logger.error(f"Polling error: {polling_error}")
                logger.error(traceback.format_exc())
                logger.info("Reconnecting in a short while...")
                time.sleep(10)  # Wait before attempting to reconnect
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main() 