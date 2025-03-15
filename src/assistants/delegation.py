"""
Delegation Assistant Implementation

This module provides the DelegationAssistant class, which orchestrates the specialized
assistants for the Para-Phrase Generator.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
import json
import traceback

from .manager import AssistantsManager
from .tools import (
    function_tool, WebSearchTool, TelegramMessageLinkTool,
    TwitterSummaryTool, FootballInfoTool, ImageAnalysisTool
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DelegationAssistant:
    """
    Delegation Assistant for the Para-Phrase Generator.
    
    This class orchestrates the specialized assistants, delegating tasks to them
    based on the content of the messages to be summarized.
    
    Attributes:
        assistants_manager (AssistantsManager): The assistants manager
        assistant_id (str): The ID of the delegation assistant
        twitter_assistant_id (str): The ID of the Twitter assistant
        football_assistant_id (str): The ID of the football assistant
        photo_assistant_id (str): The ID of the photo assistant
        tone_assistants (Dict[str, str]): Dictionary mapping tones to assistant IDs
    """
    
    def __init__(self, assistants_manager: Optional[AssistantsManager] = None):
        """
        Initialize the DelegationAssistant.
        
        Args:
            assistants_manager (AssistantsManager, optional): The assistants manager.
                Defaults to None, which creates a new AssistantsManager instance.
        """
        self.assistants_manager = assistants_manager or AssistantsManager()
        self.assistant_id = None
        self.twitter_assistant_id = None
        self.football_assistant_id = None
        self.photo_assistant_id = None
        self.tone_assistants = {}  # {tone: assistant_id}
        
        # Initialize the assistants
        self._initialize_assistants()
    
    def _initialize_assistants(self):
        """
        Initialize all assistants needed for delegation.
        """
        self._initialize_delegation_assistant()
        self._initialize_twitter_assistant()
        self._initialize_football_assistant()
        self._initialize_photo_assistant()
        self._initialize_tone_assistants()
    
    def _initialize_delegation_assistant(self):
        """
        Initialize the delegation assistant.
        """
        logger.info("Initializing delegation assistant...")
        
        # Define the tools for the delegation assistant
        tools = [
            WebSearchTool().as_tool(),
            function_tool(
                name="check_for_twitter_links",
                description="Check if the messages contain Twitter links",
                parameters={
                    "type": "object",
                    "properties": {
                        "has_twitter_links": {
                            "type": "boolean",
                            "description": "Whether the messages contain Twitter links"
                        },
                        "links": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of Twitter links found in the messages"
                        }
                    },
                    "required": ["has_twitter_links", "links"]
                }
            ),
            function_tool(
                name="check_for_football_references",
                description="Check if the messages contain references to football matches or teams",
                parameters={
                    "type": "object",
                    "properties": {
                        "has_football_references": {
                            "type": "boolean",
                            "description": "Whether the messages contain references to football"
                        },
                        "references": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of football references found in the messages"
                        }
                    },
                    "required": ["has_football_references", "references"]
                }
            ),
            function_tool(
                name="check_for_photos",
                description="Check if the messages contain photos",
                parameters={
                    "type": "object",
                    "properties": {
                        "has_photos": {
                            "type": "boolean",
                            "description": "Whether the messages contain photos"
                        },
                        "photo_message_ids": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            },
                            "description": "List of message IDs that contain photos"
                        }
                    },
                    "required": ["has_photos", "photo_message_ids"]
                }
            ),
            function_tool(
                name="check_for_sports_references",
                description="Check if the messages contain references to sports other than football",
                parameters={
                    "type": "object",
                    "properties": {
                        "has_sports_references": {
                            "type": "boolean",
                            "description": "Whether the messages contain references to sports other than football"
                        },
                        "sports": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of sports mentioned in the messages"
                        },
                        "references": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of sports references found in the messages"
                        }
                    },
                    "required": ["has_sports_references", "sports", "references"]
                }
            ),
            function_tool(
                name="get_user_profiles",
                description="Get information about users from their profiles",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of user IDs to get profiles for"
                        }
                    },
                    "required": ["user_ids"]
                }
            )
        ]
        
        # Define the instructions for the delegation assistant
        instructions = """
        You are a delegation assistant for the Para-Phrase Generator, a Telegram bot that summarizes messages.
        
        Your task is to analyze messages and delegate tasks to specialized assistants based on the content.
        
        When summarizing messages, you should:
        1. Check for Twitter links and delegate their processing to the Twitter assistant
        2. Check for football references and delegate their processing to the Football assistant
        3. Check for photos and delegate their processing to the Photo assistant
        4. Check for references to other sports and use the web search tool to find information
        5. Get user profiles to personalize the summary
        6. Generate a summary in the requested tone
        
        You can use the web search tool to find information about sports or other topics mentioned in the messages.
        
        The summary should be concise, informative, and match the requested tone. It should include:
        - Key points from the conversation
        - Information from Twitter links
        - Information about football matches or teams
        - Descriptions of photos
        - Information about other sports
        - Personalized references to users based on their profiles
        
        Always format the summary in a way that's easy to read and understand.
        """
        
        # Check if the assistant already exists
        existing_assistants = self.assistants_manager.list_assistants(name="Delegation Assistant")
        
        if existing_assistants:
            # Use the existing assistant
            self.assistant_id = existing_assistants[0].id
            logger.info(f"Using existing delegation assistant: {self.assistant_id}")
        else:
            # Create a new assistant
            assistant = self.assistants_manager.create_assistant(
                name="Delegation Assistant",
                instructions=instructions,
                tools=tools,
                model="gpt-4o"
            )
            self.assistant_id = assistant.id
            logger.info(f"Created new delegation assistant: {self.assistant_id}")
    
    def _initialize_twitter_assistant(self):
        """
        Initialize the Twitter assistant.
        """
        logger.info("Initializing Twitter assistant...")
        
        # Define the tools for the Twitter assistant
        tools = [
            TwitterSummaryTool().as_tool(),
            WebSearchTool().as_tool()
        ]
        
        # Define the instructions for the Twitter assistant
        instructions = """
        You are the Twitter assistant for a Telegram message summarization bot.
        Your role is to extract and summarize content from Twitter links.
        
        When processing Twitter links:
        1. Extract the key information from the tweets
        2. Provide a concise summary of the content
        3. Include relevant context (author, engagement stats, etc.) if available
        4. Format the summary in a way that can be integrated into the overall message summary
        
        Twitter URLs can be from twitter.com, x.com, or t.co domains.
        For URLs you cannot access directly, use the web search tool to find information.
        
        Your output should be a JSON array of tweet summaries, with each summary containing:
        - url: The original URL
        - summary: A concise summary of the tweet
        - author: The tweet author (if available)
        - context: Any additional context
        """
        
        # Create the Twitter assistant
        assistant = self.assistants_manager.create_assistant(
            name="Twitter Assistant",
            instructions=instructions,
            model="gpt-4o",
            tools=tools
        )
        
        self.twitter_assistant_id = assistant.id
        logger.info(f"Twitter assistant initialized with ID {self.twitter_assistant_id}")
    
    def _initialize_football_assistant(self):
        """
        Initialize the football assistant.
        """
        logger.info("Initializing football assistant...")
        
        # Define the tools for the football assistant
        tools = [
            WebSearchTool().as_tool()
        ]
        
        # Define the instructions for the football assistant
        instructions = """
        You are a football information assistant for the Para-Phrase Generator.
        
        Your task is to provide information about football matches, teams, and players mentioned in messages.
        
        When processing football references, you should:
        1. Use the web search tool to find real-time information about matches, scores, teams, and players
        2. Provide concise and accurate information about the football references
        3. Focus on the most relevant and recent information
        
        Your responses should be informative and to the point, focusing on the specific football references provided.
        """
        
        # Check if the assistant already exists
        existing_assistants = self.assistants_manager.list_assistants(name="Football Assistant")
        
        if existing_assistants:
            # Use the existing assistant
            self.football_assistant_id = existing_assistants[0].id
            logger.info(f"Using existing football assistant: {self.football_assistant_id}")
        else:
            # Create a new assistant
            assistant = self.assistants_manager.create_assistant(
                name="Football Assistant",
                instructions=instructions,
                tools=tools,
                model="gpt-4o"
            )
            self.football_assistant_id = assistant.id
            logger.info(f"Created new football assistant: {self.football_assistant_id}")
    
    def _initialize_photo_assistant(self):
        """
        Initialize the Photo assistant.
        """
        logger.info("Initializing Photo assistant...")
        
        # Define the tools for the Photo assistant
        tools = [
            ImageAnalysisTool().as_tool()
        ]
        
        # Define the instructions for the Photo assistant
        instructions = """
        You are the Photo assistant for a Telegram message summarization bot.
        Your role is to analyze and describe images shared in a Telegram chat.
        
        When analyzing images:
        1. Identify the key elements and subjects in the image
        2. Provide a concise description of the image content
        3. Note any text visible in the image
        4. Format the description in a way that can be integrated into the overall message summary
        
        Your output should be a JSON array of image descriptions, with each description containing:
        - message_id: The ID of the message containing the image
        - description: A concise description of the image
        - text_content: Any text visible in the image (if any)
        - objects: Key objects identified in the image
        - context: Any additional context
        """
        
        # Create the Photo assistant
        assistant = self.assistants_manager.create_assistant(
            name="Photo Assistant",
            instructions=instructions,
            model="gpt-4o",
            tools=tools
        )
        
        self.photo_assistant_id = assistant.id
        logger.info(f"Photo assistant initialized with ID {self.photo_assistant_id}")
    
    def _initialize_tone_assistants(self):
        """
        Initialize the tone assistants.
        """
        logger.info("Initializing tone assistants...")
        
        # Available tones
        tones = ["stoic", "chaotic", "pubbie", "deaf"]
        
        # Define the tools for the tone assistants
        tools = [
            TelegramMessageLinkTool().as_tool()
        ]
        
        for tone in tones:
            # Define the instructions for the tone assistant
            if tone == "stoic":
                instructions = """
                You are the Stoic tone assistant for a Telegram message summarization bot.
                Your role is to generate summaries of Telegram messages in a stoic tone.
                
                A stoic tone has the following characteristics:
                - Calm and rational
                - Unemotional and detached
                - Factual and straightforward
                - Focused on logic and reason
                - Brief and to the point
                
                When generating summaries:
                1. Focus on the key information and events
                2. Use simple, declarative statements
                3. Avoid emotional language or expressions
                4. Maintain a detached perspective
                5. Be concise and clear
                
                Include information from specialized assistants (Twitter, Football, Photo)
                if provided.
                
                Use the generate_telegram_link tool to create links to the original messages
                for key points in your summary. This allows users to click directly to the 
                referenced messages.
                """
            elif tone == "chaotic":
                instructions = """
                You are the Chaotic tone assistant for a Telegram message summarization bot.
                Your role is to generate summaries of Telegram messages in a chaotic tone.
                
                A chaotic tone has the following characteristics:
                - Energetic and unpredictable
                - Randomly EMPHASIZED words
                - Lots of exclamation marks!!!
                - Fragmented thoughts and tangents
                - Jumps between topics
                - Uses emojis 😂 and internet slang
                
                When generating summaries:
                1. Focus on the most exciting or dramatic parts
                2. Use varied punctuation and capitalization FOR EMPHASIS
                3. Insert random commentary and reactions
                4. Be expressive and emotional
                5. Use a casual, conversational style
                
                Include information from specialized assistants (Twitter, Football, Photo)
                if provided.
                
                Use the generate_telegram_link tool to create links to the original messages
                for key points in your summary. This allows users to click directly to the 
                referenced messages.
                """
            elif tone == "pubbie":
                instructions = """
                You are the Pubbie tone assistant for a Telegram message summarization bot.
                Your role is to generate summaries of Telegram messages in a pubbie tone.
                
                A pubbie tone has the following characteristics:
                - Casual and conversational, like a chat at a pub
                - British pub slang and expressions
                - References to drinking, sports, and pub culture
                - Friendly and warm
                - Slightly irreverent humor
                
                When generating summaries:
                1. Use British pub expressions ("cheers", "mate", "bloody", etc.)
                2. Keep it casual and friendly
                3. Include light jokes or commentary
                4. Reference pub culture where appropriate
                5. Use a conversational style
                
                Include information from specialized assistants (Twitter, Football, Photo)
                if provided.
                
                Use the generate_telegram_link tool to create links to the original messages
                for key points in your summary. This allows users to click directly to the 
                referenced messages.
                """
            elif tone == "deaf":
                instructions = """
                You are the Deaf tone assistant for a Telegram message summarization bot.
                Your role is to generate summaries of Telegram messages in a deaf tone.
                
                A deaf tone focuses exclusively on ALL CAPS messages or segments of messages.
                ONLY INCLUDE content that was originally in ALL CAPS in your summary.
                
                When generating summaries:
                1. ONLY include content that was in ALL CAPS
                2. Ignore any message content that wasn't in ALL CAPS
                3. If no ALL CAPS content exists, state that no shouting was detected
                4. Keep the ALL CAPS format in your summary
                5. Use similar emphasis and energy as the original ALL CAPS messages
                
                Include information from specialized assistants (Twitter, Football, Photo)
                only if they contain ALL CAPS content.
                
                Use the generate_telegram_link tool to create links to the original messages
                for key points in your summary. This allows users to click directly to the 
                referenced messages.
                """
            
            # Create the tone assistant
            assistant = self.assistants_manager.create_assistant(
                name=f"{tone.capitalize()} Tone Assistant",
                instructions=instructions,
                model="gpt-3.5-turbo-0125",  # Using 3.5 for cost efficiency on simple tasks
                tools=tools
            )
            
            self.tone_assistants[tone] = assistant.id
            logger.info(f"{tone.capitalize()} tone assistant initialized with ID {self.tone_assistants[tone]}")
    
    async def process_summary_request(
        self,
        messages: List[Dict[str, Any]],
        tone: str,
        message_mapping: Optional[Dict[int, Dict]] = None
    ) -> str:
        """
        Process a summary request.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries
            tone (str): The tone to use for the summary
            message_mapping (Optional[Dict[int, Dict]]): Mapping of message IDs to messages
            
        Returns:
            str: The summary
        """
        logger.info(f"Processing summary request with {len(messages)} messages in {tone} tone")
        
        # Create a thread for the delegation assistant
        thread = self.assistants_manager.create_thread()
        
        # Format the messages for the delegation assistant
        formatted_messages = self._format_messages_for_delegation(messages)
        
        # Add the formatted messages to the thread
        self.assistants_manager.add_message(
            thread_id=thread.id,
            role="user",
            content=f"Please summarize these messages in a {tone} tone:\n\n{formatted_messages}"
        )
        
        # Run the delegation assistant
        run = await self.assistants_manager.create_run(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )
        
        # Wait for the run to complete
        run = await self.assistants_manager.wait_for_run(thread_id=thread.id, run_id=run.id)
        
        # Process the results
        delegation_results = self._process_delegation_results(
            self.assistants_manager.get_run_content(thread_id=thread.id, run_id=run.id)
        )
        
        # Process Twitter content if needed
        twitter_summaries = []
        if delegation_results.get("has_twitter_links", False):
            twitter_links = delegation_results.get("twitter_links", [])
            if twitter_links:
                twitter_summaries = await self._process_twitter_content(twitter_links, thread.id)
        
        # Process football content if needed
        football_info = {}
        if delegation_results.get("has_football_references", False):
            football_references = delegation_results.get("football_references", [])
            if football_references:
                football_info = await self._process_football_content(football_references, thread.id)
        
        # Process photo content if needed
        photo_descriptions = []
        if delegation_results.get("has_photos", False):
            photo_message_ids = delegation_results.get("photo_message_ids", [])
            if photo_message_ids:
                photo_descriptions = await self._process_photo_content(photo_message_ids, messages, thread.id)
        
        # Process sports content if needed
        sports_info = {}
        if delegation_results.get("has_sports_references", False):
            sports = delegation_results.get("sports", [])
            sports_references = delegation_results.get("sports_references", [])
            if sports and sports_references:
                sports_info = await self._process_sports_content(sports, sports_references, thread.id)
        
        # Get user profiles if needed
        user_profiles = {}
        if delegation_results.get("user_ids", []):
            user_ids = delegation_results.get("user_ids", [])
            if user_ids:
                user_profiles = await self._get_user_profiles(user_ids)
        
        # Create a new thread for the tone-specific assistant
        tone_thread = self.assistants_manager.create_thread()
        
        # Prepare the content for the tone-specific assistant
        tone_content = f"Please summarize these messages in a {tone} tone:\n\n{formatted_messages}\n\n"
        
        # Add Twitter summaries if available
        if twitter_summaries:
            tone_content += "\nTwitter content:\n"
            for summary in twitter_summaries:
                tone_content += f"- {summary.get('url')}: {summary.get('summary')}\n"
        
        # Add football information if available
        if football_info:
            tone_content += "\nFootball information:\n"
            for reference, info in football_info.items():
                tone_content += f"- {reference}: {info}\n"
        
        # Add photo descriptions if available
        if photo_descriptions:
            tone_content += "\nPhoto descriptions:\n"
            for description in photo_descriptions:
                tone_content += f"- {description.get('description')}\n"
        
        # Add sports information if available
        if sports_info:
            tone_content += "\nSports information:\n"
            for sport, info in sports_info.items():
                tone_content += f"- {sport}: {info}\n"
        
        # Add user profiles if available
        if user_profiles:
            tone_content += "\nUser profiles:\n"
            for user_id, profile in user_profiles.items():
                tone_content += f"- User {user_id}: {profile}\n"
        
        # Add the content to the tone-specific thread
        self.assistants_manager.add_message(
            thread_id=tone_thread.id,
            role="user",
            content=tone_content
        )
        
        # Get the assistant ID for the requested tone
        tone_assistant_id = self.tone_assistants.get(tone)
        
        if not tone_assistant_id:
            logger.warning(f"No assistant found for tone {tone}, using stoic tone")
            tone_assistant_id = self.tone_assistants.get("stoic")
        
        # Run the tone-specific assistant
        tone_run = await self.assistants_manager.create_run(
            thread_id=tone_thread.id,
            assistant_id=tone_assistant_id
        )
        
        # Wait for the run to complete
        tone_run = await self.assistants_manager.wait_for_run(thread_id=tone_thread.id, run_id=tone_run.id)
        
        # Get the summary from the tone-specific assistant
        summary = self.assistants_manager.get_run_content(thread_id=tone_thread.id, run_id=tone_run.id)
        
        return summary
    
    def _format_messages_for_delegation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format messages for the delegation assistant.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries
        
        Returns:
            str: Formatted messages
        """
        formatted_messages = []
        
        for msg in messages:
            # Get basic message info
            message_id = msg.get("message_id")
            from_user = msg.get("from", {})
            username = from_user.get("username", "Unknown")
            text = msg.get("text", "")
            date = msg.get("date", "")
            
            # Check for photos
            has_photo = "photo" in msg
            photo_info = ""
            if has_photo:
                photo_info = " [Contains photo]"
            
            # Check for reply
            reply_to = msg.get("reply_to_message")
            reply_info = ""
            if reply_to:
                reply_username = reply_to.get("from", {}).get("username", "Unknown")
                reply_info = f" [In reply to {reply_username}]"
            
            # Format the message
            formatted_message = f"Message ID: {message_id} | {username}{photo_info}{reply_info}: {text}"
            formatted_messages.append(formatted_message)
        
        return "\n".join(formatted_messages)
    
    def _process_delegation_results(self, delegation_content: str) -> Dict[str, Any]:
        """
        Process the delegation assistant's response to extract delegation decisions.
        
        Args:
            delegation_content (str): Content from the delegation assistant
        
        Returns:
            Dict[str, Any]: Extracted delegation decisions
        """
        results = {
            "twitter_links": [],
            "football_references": [],
            "photo_message_ids": []
        }
        
        # Extract Twitter links
        twitter_match = re.search(
            r'check_for_twitter_links\s*\(\s*{[^}]*"links"\s*:\s*\[(.*?)\][^}]*}\s*\)',
            delegation_content,
            re.DOTALL
        )
        if twitter_match:
            links_str = twitter_match.group(1)
            # Extract the links from the string
            links = re.findall(r'"([^"]+)"', links_str)
            results["twitter_links"] = links
        
        # Extract football references
        football_match = re.search(
            r'check_for_football_references\s*\(\s*{[^}]*"references"\s*:\s*\[(.*?)\][^}]*}\s*\)',
            delegation_content,
            re.DOTALL
        )
        if football_match:
            refs_str = football_match.group(1)
            # Extract the references from the string
            refs = re.findall(r'"([^"]+)"', refs_str)
            results["football_references"] = refs
        
        # Extract photo message IDs
        photo_match = re.search(
            r'check_for_photos\s*\(\s*{[^}]*"photo_message_ids"\s*:\s*\[(.*?)\][^}]*}\s*\)',
            delegation_content,
            re.DOTALL
        )
        if photo_match:
            ids_str = photo_match.group(1)
            # Extract the message IDs from the string
            ids = re.findall(r'(\d+)', ids_str)
            results["photo_message_ids"] = [int(id) for id in ids]
        
        return results
    
    async def _process_twitter_content(
        self,
        twitter_links: List[str],
        thread_id: str
    ) -> List[Dict[str, str]]:
        """
        Process Twitter links using the Twitter assistant.
        
        Args:
            twitter_links (List[str]): List of Twitter links
            thread_id (str): The thread ID for the delegation
        
        Returns:
            List[Dict[str, str]]: List of Twitter summaries
        """
        if not twitter_links:
            return []
        
        logger.info(f"Processing {len(twitter_links)} Twitter links")
        
        # Create a new thread for the Twitter assistant
        twitter_thread = await self.assistants_manager.async_create_thread()
        twitter_thread_id = twitter_thread.id
        
        # Add the Twitter links to the thread
        await self.assistants_manager.thread_manager.async_add_message(
            thread_id=twitter_thread_id,
            content=f"Summarize the following Twitter links:\n\n{json.dumps(twitter_links)}",
            role="user"
        )
        
        # Run the Twitter assistant
        twitter_run = await self.assistants_manager.async_run_assistant(
            assistant_id=self.twitter_assistant_id,
            thread_id=twitter_thread_id
        )
        
        # Wait for the run to complete
        completed_twitter_run = await self.assistants_manager._async_run_until_complete(
            thread_id=twitter_thread_id,
            run_id=twitter_run.id,
            timeout=60
        )
        
        if completed_twitter_run.status != "completed":
            logger.error(f"Twitter assistant run failed with status {completed_twitter_run.status}")
            return []
        
        # Get the latest message from the Twitter assistant
        twitter_response = await self.assistants_manager.async_get_latest_message(twitter_thread_id)
        
        if not twitter_response:
            logger.error("No response from Twitter assistant")
            return []
        
        # Extract the content from the Twitter response
        twitter_content = self.assistants_manager.get_message_content(twitter_response)
        
        # Parse the Twitter content
        try:
            # Look for a JSON array in the response
            json_match = re.search(r'\[\s*{.*}\s*\]', twitter_content, re.DOTALL)
            if json_match:
                twitter_summaries = json.loads(json_match.group(0))
            else:
                # If no JSON array is found, try to structure the response
                twitter_summaries = []
                for link in twitter_links:
                    summary = {"url": link, "summary": "No summary available"}
                    twitter_summaries.append(summary)
            
            return twitter_summaries
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Twitter response as JSON: {twitter_content}")
            return []
    
    async def _process_football_content(
        self,
        football_references: List[str],
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Process football references using the Football assistant.
        
        Args:
            football_references (List[str]): List of football references
            thread_id (str): The thread ID for the delegation
        
        Returns:
            Dict[str, Any]: Football context information
        """
        if not football_references:
            return {"has_football_references": False, "references": []}
        
        logger.info(f"Processing {len(football_references)} football references")
        
        # Create a new thread for the Football assistant
        football_thread = await self.assistants_manager.async_create_thread()
        football_thread_id = football_thread.id
        
        # Add the football references to the thread
        await self.assistants_manager.thread_manager.async_add_message(
            thread_id=football_thread_id,
            content=f"Provide context for the following football references:\n\n{json.dumps(football_references)}",
            role="user"
        )
        
        # Run the Football assistant
        football_run = await self.assistants_manager.async_run_assistant(
            assistant_id=self.football_assistant_id,
            thread_id=football_thread_id
        )
        
        # Wait for the run to complete
        completed_football_run = await self.assistants_manager._async_run_until_complete(
            thread_id=football_thread_id,
            run_id=football_run.id,
            timeout=60
        )
        
        if completed_football_run.status != "completed":
            logger.error(f"Football assistant run failed with status {completed_football_run.status}")
            return {"has_football_references": True, "references": []}
        
        # Get the latest message from the Football assistant
        football_response = await self.assistants_manager.async_get_latest_message(football_thread_id)
        
        if not football_response:
            logger.error("No response from Football assistant")
            return {"has_football_references": True, "references": []}
        
        # Extract the content from the Football response
        football_content = self.assistants_manager.get_message_content(football_response)
        
        # Parse the Football content
        try:
            # Look for a JSON object in the response
            json_match = re.search(r'{.*}', football_content, re.DOTALL)
            if json_match:
                football_context = json.loads(json_match.group(0))
            else:
                # If no JSON object is found, create a simple structure
                football_context = {
                    "has_football_references": True,
                    "references": [{"text": ref, "context": "No context available"} for ref in football_references]
                }
            
            return football_context
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Football response as JSON: {football_content}")
            return {"has_football_references": True, "references": []}
    
    async def _process_photo_content(
        self,
        photo_message_ids: List[int],
        messages: List[Dict[str, Any]],
        thread_id: str
    ) -> List[Dict[str, Any]]:
        """
        Process photos using the Photo assistant.
        
        Args:
            photo_message_ids (List[int]): List of message IDs that contain photos
            messages (List[Dict[str, Any]]): List of message dictionaries
            thread_id (str): The thread ID for the delegation
        
        Returns:
            List[Dict[str, Any]]: List of photo descriptions
        """
        if not photo_message_ids:
            return []
        
        logger.info(f"Processing {len(photo_message_ids)} photos")
        
        # Extract the photo messages
        photo_messages = [msg for msg in messages if msg.get("message_id") in photo_message_ids]
        
        if not photo_messages:
            logger.warning("No photo messages found")
            return []
        
        # Create a message for the Photo assistant
        user_message = {
            "role": "user",
            "content": f"Please analyze the following {len(photo_messages)} photos from a Telegram chat and provide descriptions."
        }
        
        # Add the message to the thread
        self.assistants_manager.add_message(thread_id, user_message)
        
        # Process each photo message
        photo_descriptions = []
        for photo_message in photo_messages:
            message_id = photo_message.get("message_id")
            username = photo_message.get("from", {}).get("username", "Unknown")
            
            # Extract photo data
            photos = photo_message.get("photo", [])
            if not photos:
                continue
                
            # Get the largest photo (last in the array)
            photo = photos[-1]
            file_id = photo.get("file_id")
            
            if not file_id:
                continue
                
            # Create a tool call for the photo analysis
            tool_call = {
                "type": "function",
                "function": {
                    "name": "analyze_image",
                    "arguments": json.dumps({"file_id": file_id})
                }
            }
            
            # Add the tool call to the thread
            try:
                # Create a run with the tool call
                run = self.assistants_manager.create_run(
                    thread_id=thread_id,
                    assistant_id=self.photo_assistant_id,
                    tools=[tool_call]
                )
                
                # Wait for the run to complete
                run_result = await self.assistants_manager.wait_for_run(thread_id, run.id)
                
                # Get the messages from the run
                messages = self.assistants_manager.list_messages(thread_id)
                
                # Extract the photo description from the messages
                for message in messages:
                    if message.role == "assistant" and message.content:
                        content = message.content[0].text.value
                        
                        # Try to parse the content as JSON
                        try:
                            description_data = json.loads(content)
                            description_data["message_id"] = message_id
                            photo_descriptions.append(description_data)
                        except json.JSONDecodeError:
                            # If parsing fails, use the content as is
                            description = {
                                "message_id": message_id,
                                "description": content,
                                "text_content": "",
                                "objects": [],
                                "context": f"Photo shared by {username}"
                            }
                            photo_descriptions.append(description)
            except Exception as e:
                logger.error(f"Error processing photo: {e}")
                # Add a placeholder description
                description = {
                    "message_id": message_id,
                    "description": f"Photo shared by {username}. [Error processing image: {str(e)}]",
                    "text_content": "",
                    "objects": [],
                    "context": "Error during image analysis"
                }
                photo_descriptions.append(description)
        
        return photo_descriptions
    
    async def _process_sports_content(
        self,
        sports: List[str],
        sports_references: List[str],
        thread_id: str
    ) -> Dict[str, str]:
        """
        Process sports content using web search.
        
        Args:
            sports (List[str]): List of sports mentioned in the messages
            sports_references (List[str]): List of sports references found in the messages
            thread_id (str): The ID of the thread
            
        Returns:
            Dict[str, str]: Dictionary mapping sports to information
        """
        logger.info(f"Processing sports content: {sports}")
        
        # Create a new thread for the web search
        search_thread = self.assistants_manager.create_thread()
        
        # Prepare the content for the web search
        search_content = "Please search for information about the following sports references:\n\n"
        
        for i, (sport, reference) in enumerate(zip(sports, sports_references)):
            search_content += f"{i+1}. Sport: {sport}, Reference: {reference}\n"
        
        # Add the content to the search thread
        self.assistants_manager.add_message(
            thread_id=search_thread.id,
            role="user",
            content=search_content
        )
        
        # Create a web search assistant
        web_search_assistant = self.assistants_manager.create_assistant(
            name="Sports Web Search Assistant",
            instructions="""
            You are a sports information assistant. Your task is to search for information about sports references.
            
            For each sports reference, use the web search tool to find the most relevant and recent information.
            
            Provide concise and accurate information about each reference, focusing on:
            - Match results and scores
            - Team or player statistics
            - Recent news or developments
            
            Format your response as a dictionary where the keys are the sports and the values are the information.
            """,
            tools=[WebSearchTool().as_tool()],
            model="gpt-4o"
        )
        
        # Run the web search assistant
        search_run = await self.assistants_manager.create_run(
            thread_id=search_thread.id,
            assistant_id=web_search_assistant.id
        )
        
        # Wait for the run to complete
        search_run = await self.assistants_manager.wait_for_run(thread_id=search_thread.id, run_id=search_run.id)
        
        # Get the search results
        search_results = self.assistants_manager.get_run_content(thread_id=search_thread.id, run_id=search_run.id)
        
        # Parse the search results
        sports_info = {}
        
        try:
            # Try to parse the results as a dictionary
            import re
            import json
            
            # Look for a dictionary-like structure in the results
            dict_pattern = r'\{[^{}]*\}'
            dict_match = re.search(dict_pattern, search_results)
            
            if dict_match:
                dict_str = dict_match.group(0)
                sports_info = json.loads(dict_str)
            else:
                # If no dictionary is found, create a simple mapping
                for sport, reference in zip(sports, sports_references):
                    sports_info[sport] = f"Information about {reference}"
        except Exception as e:
            logger.error(f"Error parsing sports search results: {e}")
            logger.error(traceback.format_exc())
            
            # Fallback: create a simple mapping
            for sport, reference in zip(sports, sports_references):
                sports_info[sport] = f"Information about {reference}"
        
        return sports_info
    
    async def _get_user_profiles(self, user_ids: List[str]) -> Dict[str, str]:
        """
        Get user profiles from the vector store.
        
        Args:
            user_ids (List[str]): List of user IDs
            
        Returns:
            Dict[str, str]: Dictionary mapping user IDs to profile summaries
        """
        logger.info(f"Getting user profiles for {len(user_ids)} users")
        
        # Import the profile store
        from ..vector_store import UserProfileStore
        profile_store = UserProfileStore()
        
        # Get the profiles
        profiles = {}
        
        for user_id in user_ids:
            try:
                profile = profile_store.get_user_profile(user_id)
                
                if profile:
                    # Extract interests
                    interests = profile_store.extract_user_interests(user_id)
                    
                    # Create a summary of the profile
                    summary = f"User {user_id}"
                    
                    # Add basic information
                    metadata = profile.get("metadata", {})
                    if metadata.get("first_name"):
                        summary += f", {metadata['first_name']}"
                    
                    if metadata.get("last_name"):
                        summary += f" {metadata['last_name']}"
                    
                    if metadata.get("username"):
                        summary += f" (@{metadata['username']})"
                    
                    # Add interests
                    if interests:
                        summary += ". Interests: "
                        interest_parts = []
                        
                        for category, items in interests.items():
                            if items:
                                interest_parts.append(f"{category}: {', '.join(items)}")
                        
                        summary += "; ".join(interest_parts)
                    
                    profiles[user_id] = summary
                else:
                    profiles[user_id] = f"No profile found for user {user_id}"
            except Exception as e:
                logger.error(f"Error getting profile for user {user_id}: {e}")
                logger.error(traceback.format_exc())
                profiles[user_id] = f"Error getting profile for user {user_id}"
        
        return profiles 