#!/usr/bin/env python
"""
Example script demonstrating the agent-based architecture using the OpenAI Agents SDK.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import from our SDK imports
from src.sdk_imports import (
    Agent, Runner, RunConfig, function_tool, WebSearchTool, ModelSettings,
    set_default_openai_key
)

# Set up API key
api_key = os.environ.get("OPENAI_API_KEY")
if api_key:
    set_default_openai_key(api_key)
else:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Define function tools
@function_tool
def get_current_time() -> str:
    """Get the current time."""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@function_tool
def analyze_message(text: str) -> dict:
    """Analyze a message for tone and key topics."""
    # This would normally involve more complex analysis
    result = {
        "length": len(text),
        "contains_question": "?" in text,
        "topics": ["Sample topic detection - would be more sophisticated in real implementation"]
    }
    return result

# Define specialized agents
def create_twitter_agent():
    """Create a Twitter link processing agent."""
    agent = Agent(
        name="Twitter Link Agent",
        instructions="""You analyze Twitter/X posts from links shared in conversations.
        Extract key information including:
        - The author's username
        - The main content/point of the tweet
        - Any hashtags or mentions
        - Sentiment (positive, negative, neutral)
        
        Summarize this information in a concise way that provides context to the conversation.
        """,
        model="gpt-3.5-turbo",
        tools=[WebSearchTool()]
    )
    return agent

def create_photo_agent():
    """Create a photo content analysis agent."""
    agent = Agent(
        name="Photo Analysis Agent",
        instructions="""You analyze the content of photos shared in conversations.
        Describe the image contents clearly and concisely, noting:
        - Main subjects/objects
        - Setting/background
        - Activities happening
        - Text content if present
        - Whether it appears to be a meme
        
        Summarize what you see in a natural, conversational way.
        """,
        model="gpt-4o"  # Using vision-capable model
    )
    return agent

def create_football_agent():
    """Create a football score/match information agent."""
    agent = Agent(
        name="Football Score Agent",
        instructions="""You provide context about football matches mentioned in conversations.
        When football teams or scores are mentioned:
        - Identify the teams
        - Provide context about recent matches
        - Explain significance of scores/results
        - Add relevant league standings if helpful
        
        Your goal is to enhance the conversation with relevant football context.
        """,
        model="gpt-3.5-turbo",
        tools=[WebSearchTool(), get_current_time]
    )
    return agent

def create_delegation_agent():
    """Create the main delegation agent that routes to specialized agents."""
    # Create specialized agents
    twitter_agent = create_twitter_agent()
    photo_agent = create_photo_agent()
    football_agent = create_football_agent()
    
    # Create the delegation agent with handoffs
    agent = Agent(
        name="Delegation Agent",
        instructions="""You are the main coordinator for a message summarization system.
        Analyze the messages and determine if they contain:
        - Twitter/X links (hand off to Twitter Link Agent)
        - Photos/images (hand off to Photo Analysis Agent)
        - Football references (hand off to Football Score Agent)
        
        If none of these special cases apply, process the message yourself by:
        1. Identifying key topics and themes
        2. Noting sentiment and tone
        3. Summarizing the main points
        
        Always maintain a natural, conversational tone in your summaries.
        """,
        model="gpt-3.5-turbo",
        tools=[analyze_message, get_current_time],
        handoffs=[twitter_agent, photo_agent, football_agent],
        model_settings=ModelSettings(temperature=0.7)
    )
    return agent

async def process_messages(messages, tone="stoic"):
    """Process a batch of messages using the agent architecture."""
    # Format messages for the agent
    formatted_messages = f"""
    The following is a conversation between several users:
    
    {messages}
    
    Summarize this conversation in a {tone} tone.
    """
    
    # Create and run the delegation agent
    delegation_agent = create_delegation_agent()
    
    message_count = len(messages.split('\n'))
    logger.info(f"Processing {message_count} messages with {tone} tone...")
    result = await Runner.run(
        delegation_agent,
        input=formatted_messages,
        run_config=RunConfig(workflow_name=f"Message Summary - {tone} tone")
    )
    
    return result.final_output

async def main():
    """Run example cases demonstrating different agent capabilities."""
    # Example 1: Regular conversation
    conversation1 = """
    Alice: Hey everyone, what are we doing this weekend?
    Bob: I was thinking we could go to that new restaurant downtown.
    Charlie: SOUNDS GREAT TO ME! I'M STARVING!
    Alice: What time should we meet?
    Bob: How about 7pm?
    Charlie: I'll be there. CANT WAIT TO TRY THEIR FAMOUS DESSERT!
    """
    
    # Example 2: Football reference
    conversation2 = """
    David: Did you see the match yesterday? Barcelona 3-1 Real Madrid was amazing!
    Eva: Yeah, Messi was on fire! Two goals and an assist.
    Frank: I can't believe Chelsea lost 0-2 to Arsenal though.
    David: That's three losses in a row for them now.
    """
    
    # Example 3: Twitter reference
    conversation3 = """
    Grace: Check out this tweet from Elon Musk: https://twitter.com/elonmusk/status/1234567890
    Henry: That's interesting. Did you see this response? https://x.com/user/status/9876543210
    Grace: Yeah, the whole thread is blowing up.
    """
    
    # Process each conversation with different tones
    summary1 = await process_messages(conversation1, tone="stoic")
    print("\nRegular Conversation Summary (Stoic):")
    print(summary1)
    
    summary2 = await process_messages(conversation2, tone="pubbie")
    print("\nFootball Conversation Summary (Pubbie):")
    print(summary2)
    
    summary3 = await process_messages(conversation3, tone="chaotic")
    print("\nTwitter Conversation Summary (Chaotic):")
    print(summary3)

if __name__ == "__main__":
    asyncio.run(main()) 