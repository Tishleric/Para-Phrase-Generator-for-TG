# bot.py
# Main file to run the Telegram bot for message summarization
import telebot
import os
from summarizer import summarize_messages
from dotenv import load_dotenv

def is_all_caps(text):
    if not text:  # Handle empty or None text
        return False
    has_upper = any(c.isupper() for c in text)
    has_lower = any(c.islower() for c in text)
    return has_upper and not has_lower

def extract_all_caps_sequences(text):
    if not text:
        return []
    words = text.split()
    sequences = []
    current_sequence = []
    for word in words:
        if word.isupper() and any(c.isalpha() for c in word):  # Must be all caps and have at least one letter
            current_sequence.append(word)
        else:
            if current_sequence:  # End of a sequence
                sequences.append(" ".join(current_sequence))
                current_sequence = []
    if current_sequence:  # Add the last sequence if exists
        sequences.append(" ".join(current_sequence))
    return sequences

# Load environment variables from .env file
load_dotenv()

# Print startup information
token = os.environ.get("TELEGRAM_BOT_TOKEN")
if token:
    # Mask the token for security, only show first 10 chars
    masked_token = token[:10] + "..." + token[-5:]
    print(f"Starting bot with token: {masked_token}")
    print("Bot is initializing...")
else:
    print("ERROR: No Telegram token found in environment variables!")

bot = telebot.TeleBot(os.environ.get("TELEGRAM_BOT_TOKEN"))
chat_history = {}  # {chat_id: [list of messages]}
chat_tones = {}  # {chat_id: tone}

@bot.message_handler(commands=['tone'])
def set_tone(message):
    chat_id = message.chat.id
    try:
        tone = message.text.split()[1].lower()
        if tone in ['stoic', 'chaotic', 'pubbie', 'deaf']:
            chat_tones[chat_id] = tone
            bot.reply_to(message, f"Tone set to {tone}.")
        else:
            bot.reply_to(message, "Invalid tone. Use: stoic, chaotic, pubbie, deaf.")
    except IndexError:
        bot.reply_to(message, "Please provide a tone (e.g., /tone pubbie).")

@bot.message_handler(commands=['last'])
def last_messages(message):
    chat_id = message.chat.id
    try:
        n = int(message.text.split()[1])
        if chat_id not in chat_history or len(chat_history[chat_id]) == 0:
            bot.reply_to(message, "No messages to summarize yet!")
            return
        messages = chat_history[chat_id][-n:] if n <= len(chat_history[chat_id]) else chat_history[chat_id]
        tone = chat_tones.get(chat_id, 'stoic')
        
        formatted_messages = []
        if tone == "deaf":
            for msg in messages:
                if msg.get("text"):  # Only process messages with text
                    sequences = extract_all_caps_sequences(msg["text"])
                    for seq in sequences:
                        formatted_messages.append(f"{msg['sender']}: {seq}")
            if not formatted_messages:
                bot.reply_to(message, "I didn't hear anything.")
                return
        else:
            for msg in messages:
                if msg.get("is_image"):
                    formatted_messages.append(f"{msg['sender']} sent an image.")
                elif msg.get("reply_to"):
                    original = msg['reply_to']
                    formatted_messages.append(f"{msg['sender']} replied to {original['sender']}'s message '{original['text']}': {msg['text']}")
                else:
                    formatted_messages.append(f"{msg['sender']}: {msg['text']}")
        
        summary = summarize_messages(formatted_messages, tone)
        bot.reply_to(message, summary)
    except (IndexError, ValueError):
        bot.reply_to(message, "Please provide a valid number (e.g., /last 10).")

@bot.message_handler(func=lambda message: True)
def store_message(message):
    chat_id = message.chat.id
    sender = message.from_user.first_name or message.from_user.username
    msg_data = {
        "sender": sender,
        "text": message.text,
        "is_image": bool(message.photo),
        "reply_to": None
    }
    if message.reply_to_message:
        original_sender = message.reply_to_message.from_user.first_name or message.reply_to_message.from_user.username
        original_text = message.reply_to_message.text or "[non-text message]"
        msg_data["reply_to"] = {
            "sender": original_sender,
            "text": original_text
        }
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(msg_data)
    if len(chat_history[chat_id]) > 100:
        chat_history[chat_id].pop(0)

bot.polling() 