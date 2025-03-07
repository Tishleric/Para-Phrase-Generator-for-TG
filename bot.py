# bot.py
# Main file to run the Telegram bot for message summarization
import telebot
import os
from summarizer import summarize_messages

bot = telebot.TeleBot(os.environ.get("TELEGRAM_BOT_TOKEN"))
chat_history = {}  # {chat_id: [list of messages]}
chat_tones = {}  # {chat_id: tone}

@bot.message_handler(commands=['tone'])
def set_tone(message):
    chat_id = message.chat.id
    try:
        tone = message.text.split()[1].lower()
        if tone in ['stoic', 'chaotic', 'funny', 'deaf']:
            chat_tones[chat_id] = tone
            bot.reply_to(message, f"Tone set to {tone}.")
        else:
            bot.reply_to(message, "Invalid tone. Use: stoic, chaotic, funny, deaf.")
    except IndexError:
        bot.reply_to(message, "Please provide a tone (e.g., /tone funny).")

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
        summary = summarize_messages(messages, tone)
        bot.reply_to(message, summary)
    except (IndexError, ValueError):
        bot.reply_to(message, "Please provide a valid number (e.g., /last 10).")

@bot.message_handler(func=lambda message: True)
def store_message(message):
    chat_id = message.chat.id
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(message.text)
    if len(chat_history[chat_id]) > 100:
        chat_history[chat_id].pop(0)

bot.polling() 