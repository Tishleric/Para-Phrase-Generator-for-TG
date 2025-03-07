# summarizer.py
# Handles message summarization using Claude 3.7 Sonnet from Anthropic
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import os

# Use environment variable for API key
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def summarize_messages(messages, tone):
    # Base instruction
    base_prompt = "Summarize the following messages:\n\n" + "\n".join(messages) + "\n\n"

    # Tone-specific instructions
    tone_instructions = {
        "stoic": "Summarize these messages in a formal, concise manner with no emotional language. Focus exclusively on factual information and action items. Use short, direct sentences with minimal adjectives. Present information chronologically and avoid commentary or humor. Your tone should be professional and businesslike, similar to an executive briefing.",
        "chaotic": "Summarize these messages in an unpredictable, mischievous style. Occasionally insert a deliberate but plausible misinterpretation of events. Use exaggerated language, and playful insults. Create drama where possible. Be provocative and stir things up with comments that might cause reactions. Maintain a balance where about 70% of your summary is accurate but 30% contains exaggerations or minor fabrications for entertainment. Make it obvious when you're being hyperbolic.",
        "funny": "Summarize these messages as a chatty British pub regular who supports Fulham FC. Use British slang (both modern and old-fashioned), mild self-deprecation, and witty observations. Imagine you're a bit tipsy but still coherent. Occasionally reference football (especially Fulham) even when not directly relevant. Use phrases like \"bloody hell,\" \"mate,\" \"proper,\" \"cheeky,\" \"knackered,\" etc. Be amusing but still convey all the important information accurately.",
        "deaf": "Summarize these messages as if you're a robot that frequently mishears words and focuses on odd details. Be literal, miss emotional subtext, and occasionally fixate on fashion or Kanye West references even when none exist. Express apathy toward the task itself. Mention your support of Arsenal FC while sparsely admitting jealousy of Fulham when contextually appropriate. Use flat, mechanical language interspersed with random enthusiasm about unimportant details. Be dismissive but still summarize the core information."
    }
    
    # Add tone guidance
    prompt = f"{HUMAN_PROMPT}{base_prompt}Do this in a {tone} tone: {tone_instructions.get(tone, tone_instructions['stoic'])}.{AI_PROMPT}"
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error summarizing: {str(e)}" 