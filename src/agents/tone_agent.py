# src/agents/tone_agent.py
# Tone-specific agent for message summarization
"""
This module defines the ToneAgent class, which handles tone-specific
summarization of messages.
"""

import logging
from typing import Dict, List, Optional, Any
from src.sdk_imports import function_tool
from .base_agent import BaseAgent
from ..config import get_agent_model, MAX_BASE_TOKENS, TOKENS_PER_MESSAGE, MAX_TOTAL_TOKENS
from ..utils import format_messages_for_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ToneAgent(BaseAgent):
    """
    Tone-specific agent for message summarization.
    
    This agent generates summaries using a specific tone (stoic, chaotic, 
    pubbie, deaf).
    
    Attributes:
        name (str): The name of the agent
        tone (str): The tone for summarization
        agent (Agent): The OpenAI Agent instance
    """
    
    def __init__(self, tone: str):
        """
        Initialize a ToneAgent instance.
        
        Args:
            tone (str): The tone for summarization (stoic, chaotic, pubbie, deaf)
        """
        self.tone = tone.lower()
        
        # Define tone-specific instructions
        tone_instructions = {
            "stoic": "Summarize messages in three paragraphs or less, using a formal, concise manner with no emotional language. Focus exclusively on factual information and action items. Use short, direct sentences with minimal adjectives. Present information chronologically and avoid commentary. Your tone should be professional and businesslike, similar to an executive briefing.",
            "chaotic": "Summarize messages in three paragraphs or less, using an energetic and playful style. Occasionally interpret events creatively. Use colorful language and witty observations. Add dramatic flair where possible. Make entertaining observations that highlight amusing contrasts or ironies. Keep the summary accurate while using hyperbole for effect.",
            "pubbie": "Summarize messages in three paragraphs or less, as a chatty British football enthusiast. Use British slang (both modern and old-fashioned), mild self-deprecation, and witty observations. Keep it lighthearted but coherent. Reference football metaphors when relevant. Use phrases like 'bloody hell,' 'mate,' 'proper,' 'cheeky,' etc. Be amusing while conveying all important information accurately.",
            "deaf": "In three paragraphs or less, only summarize text that appears in CAPITAL LETTERS from the messages, ignoring all lowercase text. Treat this like someone who can only 'hear' shouted text. If there are no capital letter sections, respond with 'I COULDN'T HEAR ANYTHING CLEARLY IN THOSE MESSAGES.' If you find capital letters, summarize just those parts in a clear, direct way, also using capital letters in your response."
        }
        
        # Use default instructions if tone not found
        instruction = tone_instructions.get(
            self.tone, 
            tone_instructions["stoic"]
        )
        
        # Create agent instructions
        instructions = f"""
        You are a message summarization agent that uses a {self.tone} tone.
        
        {instruction}
        
        When summarizing messages:
        1. Focus on capturing the key points and important information
        2. Maintain the {self.tone} tone throughout the summary
        3. Keep the summary concise but informative
        4. Include references to all participants mentioned in the messages
        """
        
        # Define function tools
        tools = [
            self._count_tokens,
            self._analyze_sentiment
        ]
        
        super().__init__(
            name=f"{self.tone.capitalize()} Tone Agent",
            instructions=instructions,
            model=get_agent_model("tone_summary"),
            tools=tools
        )
        
        logger.info(f"Initialized {self.tone} Tone Agent")
    
    @function_tool
    def _count_tokens(self, text: str) -> int:
        """
        Count the approximate number of tokens in a text.
        
        Args:
            text (str): The text to count tokens for
            
        Returns:
            int: Approximate token count (estimated as words/0.75)
        """
        # Rough estimation: 1 token ≈ 0.75 words
        word_count = len(text.split())
        return int(word_count / 0.75)
    
    @function_tool
    def _analyze_sentiment(self, messages: List[str]) -> Dict[str, Any]:
        """
        Analyze the sentiment of messages.
        
        Args:
            messages (List[str]): List of message strings
            
        Returns:
            Dict[str, Any]: Sentiment analysis results
        """
        if not messages:
            return {"overall": "neutral", "positive": 0, "negative": 0, "neutral": 0}
        
        # Simple keyword-based sentiment analysis
        positive_words = ["good", "great", "excellent", "happy", "like", "love", "awesome"]
        negative_words = ["bad", "terrible", "awful", "sad", "hate", "dislike", "poor"]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for msg in messages:
            msg_lower = msg.lower()
            
            pos = sum(1 for word in positive_words if word in msg_lower)
            neg = sum(1 for word in negative_words if word in msg_lower)
            
            if pos > neg:
                positive_count += 1
            elif neg > pos:
                negative_count += 1
            else:
                neutral_count += 1
        
        # Determine overall sentiment
        total = positive_count + negative_count + neutral_count
        if total == 0:
            overall = "neutral"
        elif positive_count > negative_count and positive_count > neutral_count:
            overall = "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            overall = "negative"
        else:
            overall = "neutral"
        
        return {
            "overall": overall,
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count
        }
    
    def summarize(self, messages: List[Dict[str, Any]]) -> str:
        """
        Summarize messages using the agent's tone.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries
            
        Returns:
            str: The generated summary
        """
        # Format messages for this tone
        formatted_messages = format_messages_for_summary(messages, self.tone)
        
        if not formatted_messages:
            if self.tone == "deaf":
                return "I COULDN'T HEAR ANYTHING CLEARLY IN THOSE MESSAGES."
            return "No messages to summarize."
        
        # Calculate max_tokens dynamically: base + tokens per message, capped at max
        max_tokens = min(MAX_BASE_TOKENS + TOKENS_PER_MESSAGE * len(formatted_messages), MAX_TOTAL_TOKENS)
        
        # Prepare input for the agent
        messages_text = "\n".join(formatted_messages)
        
        input_text = f"""
        Summarize the following messages in a {self.tone} tone:
        
        {messages_text}
        """
        
        # Process with the agent
        response = self.process(input_text)
        return response
    
    def generate_summary(self, context: Dict[str, Any]) -> str:
        """
        Generate a summary using the agent's tone and specialized agent results.
        
        This method is called by the delegation agent to generate a summary
        that incorporates results from specialized agents.
        
        Args:
            context: Dictionary containing messages and specialized agent results
                - messages: List of formatted message strings
                - specialized_results: Dictionary mapping agent types to results
                    - twitter: Twitter link analysis results (or None)
                    - football: Football reference analysis results (or None)
                    - photo: Photo content analysis results (or None)
            
        Returns:
            str: The generated summary
        """
        messages = context.get("messages", [])
        specialized_results = context.get("specialized_results", {})
        
        if not messages:
            if self.tone == "deaf":
                return "I COULDN'T HEAR ANYTHING CLEARLY IN THOSE MESSAGES."
            return "No messages to summarize."
        
        # Calculate max_tokens dynamically: base + tokens per message, capped at max
        max_tokens = min(MAX_BASE_TOKENS + TOKENS_PER_MESSAGE * len(messages), MAX_TOTAL_TOKENS)
        
        # Prepare input for the agent
        messages_text = "\n".join(messages)
        
        # Add specialized content information
        special_content = ""
        
        # Add Twitter results if available
        twitter_result = specialized_results.get("twitter")
        if twitter_result:
            special_content += f"\n\nTwitter Links Information:\n{twitter_result}"
        
        # Add Football results if available
        football_result = specialized_results.get("football")
        if football_result:
            special_content += f"\n\nFootball References Information:\n{football_result}"
        
        # Add Photo results if available
        photo_result = specialized_results.get("photo")
        if photo_result:
            special_content += f"\n\nImage Content Information:\n{photo_result}"
        
        input_text = f"""
        Summarize the following messages in a {self.tone} tone.
        
        Messages:
        {messages_text}
        {special_content}
        """
        
        # Process with the agent
        response = self.process(input_text)
        return response 