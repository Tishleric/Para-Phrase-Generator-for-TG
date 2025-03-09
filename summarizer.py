# summarizer.py
# Handles message summarization using Claude 3.7 Sonnet from Anthropic
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Use environment variable for API key
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def summarize_messages(messages, tone):
    # Base instruction
    base_prompt = "Summarize the following messages:\n\n" + "\n".join(messages) + "\n\n"

    # Calculate max_tokens dynamically: 250 base + 10 per message, max 500
    max_tokens = min(250 + 10 * len(messages), 500)

    # Tone-specific instructions
    tone_instructions = {
        "stoic": "Summarize these messages in three paragraphs or less, using a formal, concise manner with no emotional language. Focus exclusively on factual information and action items. Use short, direct sentences with minimal adjectives. Present information chronologically and avoid commentary. Your tone should be professional and businesslike, similar to an executive briefing.",
        "chaotic": "Summarize these messages in three paragraphs or less, using an energetic and playful style. Occasionally interpret events creatively. Use colorful language and witty observations. Add dramatic flair where possible. Make entertaining observations that highlight amusing contrasts or ironies. Keep the summary accurate while using hyperbole for effect.",
        "pubbie": "Summarize these messages in three paragraphs or less, as a chatty British football enthusiast. Use British slang (both modern and old-fashioned), mild self-deprecation, and witty observations. Keep it lighthearted but coherent. Reference football metaphors when relevant. Use phrases like \"bloody hell,\" \"mate,\" \"proper,\" \"cheeky,\" etc. Be amusing while conveying all important information accurately.",
        "deaf": "In three paragraphs or less, only summarize text that appears in CAPITAL LETTERS from the messages, ignoring all lowercase text. Treat this like someone who can only 'hear' shouted text. If there are no capital letter sections, respond with 'I COULDN'T HEAR ANYTHING CLEARLY IN THOSE MESSAGES.' If you find capital letters, summarize just those parts in a clear, direct way, also using capital letters in your response."
    }
    # Add tone guidance
    prompt = f"{HUMAN_PROMPT}{base_prompt}Do this in a {tone} tone: {tone_instructions.get(tone, tone_instructions['stoic'])}.{AI_PROMPT}"
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error summarizing: {str(e)}" 