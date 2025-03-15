# Product Context - Para-Phrase Generator

## Why This Project Exists
The Para-Phrase Generator (Telegram Message Summarization Bot) was created to solve the problem of information overload in group chats. Users often return to active group conversations and find dozens or hundreds of unread messages, making it time-consuming to catch up on important discussions. This bot provides a quick way to get the essence of recent conversations without having to read every message.

## Problems It Solves
1. **Information Overload**: Condenses large message volumes into concise summaries
2. **Time Management**: Saves users from having to read every message to stay informed
3. **Contextual Awareness**: Helps users quickly understand ongoing discussions they've missed
4. **Engagement Barrier**: Lowers the barrier to re-engage with active conversations after absence

## How It Works
1. The bot listens to all messages in a group chat and stores them in memory (up to a defined limit of 100 messages)
2. Users can request summaries of the last N messages using the `/last N` command
3. Summaries are generated using Anthropic's Claude 3.7 Sonnet API
4. Users can customize the tone of summaries using the `/tone` command with options:
   - **stoic**: Formal, concise, and informative (ideal for business chats)
   - **chaotic**: Random, humorous, and slightly unpredictable (for fun group chats)
   - **pubbie**: Chatty British football enthusiast style with slang and wit
   - **deaf**: A special mode that only "hears" text written in ALL CAPS

## User Experience Goals
1. **Simplicity**: Commands should be intuitive and easy to remember (`/last N`, `/tone X`)
2. **Personality**: Tone options make summaries engaging and fit different chat contexts
3. **Accuracy**: Summaries should capture key points and action items from conversations
4. **Responsiveness**: Bot should generate summaries quickly (within seconds)
5. **Adaptability**: Works well for various types of group chats (professional, social, hobby-focused)

## Core User Journeys
1. **Returning User**: Opens chat → Sees many unread messages → Uses `/last 50` → Gets a quick summary → Can now participate without feeling lost
2. **Tone Customization**: User wants a more entertaining summary → Uses `/tone pubbie` → Future summaries have British football fan flair
3. **Focus on Emphasis**: In a noisy chat, user wants to see only emphasized points → Uses `/tone deaf` → Gets summary of only the ALL CAPS content 