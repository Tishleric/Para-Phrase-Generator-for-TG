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
        Initialize all assistants.
        """
        logger.info("Initializing assistants...")
        
        # Initialize the delegation assistant
        self._initialize_delegation_assistant()
        
        # Initialize the specialized assistants
        self._initialize_twitter_assistant()
        self._initialize_football_assistant()
        self._initialize_photo_assistant()
        self._initialize_tone_assistants()
        
        # Initialize the sports assistant
        self._initialize_sports_assistant()
        
        logger.info("All assistants initialized.")
    
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
    
    def _initialize_sports_assistant(self):
        """
        Initialize the sports information assistant.
        """
        logger.info("Initializing sports information assistant...")
        
        # Define the tools for the sports assistant
        tools = [
            WebSearchTool().as_tool()
        ]
        
        # Define the instructions for the sports assistant
        instructions = """
        You are a sports information assistant. Your task is to search for information about sports references.
        
        For each sports reference, use the web search tool to find the most relevant and recent information.
        
        Provide concise and accurate information about each reference, focusing on:
        - Match results and scores
        - Team or player statistics
        - Recent news or developments
        
        Format your response as a dictionary where the keys are the sports and the values are the information.
        """
        
        # Check if the assistant already exists
        existing_assistants = self.assistants_manager.list_assistants(name="Sports Information Assistant")
        
        if existing_assistants:
            # Use the existing assistant
            self.sports_assistant_id = existing_assistants[0].id
            logger.info(f"Using existing sports information assistant: {self.sports_assistant_id}")
        else:
            # Create a new assistant
            assistant = self.assistants_manager.create_assistant(
                name="Sports Information Assistant",
                instructions=instructions,
                tools=tools,
                model="gpt-4o"
            )
            self.sports_assistant_id = assistant.id
            logger.info(f"Created new sports information assistant: {self.sports_assistant_id}")
    
    async def process_summary_request(
        self,
        messages: List[Dict[str, Any]],
        tone: str,
        message_mapping: Optional[Dict[int, Dict]] = None
    ) -> str:
        """
        Process a summary request.
        
        Args:
            messages (List[Dict[str, Any]]): The messages to summarize
            tone (str): The tone to use for the summary
            message_mapping (Dict[int, Dict], optional): Mapping of message IDs to messages.
                Used for message linking. Defaults to None.
        
        Returns:
            str: The summary
        """
        import logging
        from ..config import ADD_MESSAGE_LINKS, ENABLE_IMAGE_ANALYSIS, MAX_LINKS_PER_SUMMARY
        
        logger = logging.getLogger(__name__)
        
        if not messages:
            return "No messages to summarize."
        
        # Get or create a thread ID
        thread_id = str(id(messages))
        
        try:
            # Format the messages for delegation
            formatted_messages = self._format_messages_for_delegation(messages)
            
            # Create a message for the delegation assistant
            delegation_message = f"Here are the messages to summarize:\n\n{formatted_messages}\n\nTone: {tone}\n\nPlease analyze these messages and determine which specialized assistants should be used to process different parts. Focus on identifying Twitter/X links, images/photos, sports-related content, and other specialized content."
            
            # Submit the message to the delegation assistant
            logger.info(f"Submitting request to delegation assistant with thread ID: {thread_id}")
            
            try:
                delegation_response = await self.assistants_manager.submit_message(
                    self.assistant_id,
                    delegation_message,
                    thread_id
                )
            except Exception as e:
                logger.error(f"Failed to submit message to delegation assistant: {e}")
                logger.error(traceback.format_exc())
                return f"Error: Failed to process with delegation assistant. Details: {str(e)}"
            
            # Process the delegation results
            try:
                delegation_results = self._process_delegation_results(delegation_response)
                logger.info(f"Delegation results: {delegation_results}")
            except Exception as e:
                logger.error(f"Failed to process delegation results: {e}")
                logger.error(traceback.format_exc())
                return f"Error: Failed to process delegation results. Details: {str(e)}"
            
            # Process Twitter links if found
            twitter_summaries = []
            if delegation_results.get("twitter_links"):
                twitter_links = delegation_results["twitter_links"]
                logger.info(f"Processing {len(twitter_links)} Twitter links")
                try:
                    twitter_summaries = await self._process_twitter_content(twitter_links, thread_id)
                except Exception as e:
                    logger.error(f"Failed to process Twitter links: {e}")
                    logger.error(traceback.format_exc())
                    # Continue with the summary even if Twitter processing fails
            
            # Process football references if found
            football_info = {}
            if delegation_results.get("football_references"):
                football_references = delegation_results["football_references"]
                logger.info(f"Processing {len(football_references)} football references")
                try:
                    football_info = await self._process_football_content(football_references, thread_id)
                except Exception as e:
                    logger.error(f"Failed to process football references: {e}")
                    logger.error(traceback.format_exc())
                    # Continue with the summary even if football processing fails
            
            # Process photo content if found and if image analysis is enabled
            photo_descriptions = []
            if delegation_results.get("photo_message_ids") and ENABLE_IMAGE_ANALYSIS:
                photo_message_ids = delegation_results["photo_message_ids"]
                logger.info(f"Processing {len(photo_message_ids)} photos")
                try:
                    photo_descriptions = await self._process_photo_content(photo_message_ids, messages, thread_id)
                except Exception as e:
                    logger.error(f"Failed to process photos: {e}")
                    logger.error(traceback.format_exc())
                    # Continue with the summary even if photo processing fails
            
            # Process sports content if found
            sports_info = {}
            if delegation_results.get("sports_references") and delegation_results.get("sports"):
                sports = delegation_results["sports"]
                sports_references = delegation_results["sports_references"]
                logger.info(f"Processing sports references for {sports}")
                try:
                    sports_info = await self._process_sports_content(sports, sports_references, thread_id)
                except Exception as e:
                    logger.error(f"Failed to process sports references: {e}")
                    logger.error(traceback.format_exc())
                    # Continue with the summary even if sports processing fails
            
            # Process user profiles if needed
            user_profiles = {}
            if delegation_results.get("user_ids"):
                user_ids = delegation_results["user_ids"]
                logger.info(f"Processing {len(user_ids)} user profiles")
                try:
                    user_profiles = await self._get_user_profiles(user_ids)
                except Exception as e:
                    logger.error(f"Failed to process user profiles: {e}")
                    logger.error(traceback.format_exc())
                    # Continue with the summary even if profile processing fails
            
            # Determine which tone assistant to use
            if tone in self.tone_assistants:
                tone_assistant_id = self.tone_assistants[tone]
            else:
                # Fall back to stoic tone if the requested tone is not available
                logger.warning(f"Tone {tone} not available, falling back to stoic")
                tone_assistant_id = self.tone_assistants["stoic"]
            
            # Create a message for the tone-specific assistant
            tone_message = f"Please summarize the following messages in a {tone} tone:\n\n{formatted_messages}"
            
            # Add Twitter summary information if available
            if twitter_summaries:
                twitter_info = "\n\nTwitter/X Link Information:\n"
                for i, summary in enumerate(twitter_summaries):
                    twitter_info += f"{i+1}. {summary.get('url', 'Unknown URL')}: {summary.get('summary', 'No summary available')}\n"
                tone_message += twitter_info
            
            # Add football information if available
            if football_info:
                football_data = "\n\nFootball Information:\n"
                for team, info in football_info.items():
                    football_data += f"{team}: {info}\n"
                tone_message += football_data
            
            # Add photo descriptions if available
            if photo_descriptions:
                photo_data = "\n\nPhoto Content:\n"
                for i, photo in enumerate(photo_descriptions):
                    photo_data += f"Photo {i+1}: {photo.get('description', 'No description')}"
                    if photo.get("text_content"):
                        photo_data += f" (Text: {photo['text_content']})"
                    photo_data += "\n"
                tone_message += photo_data
            
            # Add sports information if available
            if sports_info:
                sports_data = "\n\nSports Information:\n"
                for sport, info in sports_info.items():
                    sports_data += f"{sport}: {info}\n"
                tone_message += sports_data
            
            # Add user profile information if available
            if user_profiles:
                profile_data = "\n\nUser Profiles:\n"
                for user_id, profile in user_profiles.items():
                    profile_data += f"User {user_id}: {profile}\n"
                tone_message += profile_data
            
            # Submit the message to the tone-specific assistant
            logger.info(f"Submitting request to {tone} tone assistant")
            try:
                tone_response = await self.assistants_manager.submit_message(
                    tone_assistant_id,
                    tone_message,
                    thread_id
                )
            except Exception as e:
                logger.error(f"Failed to submit message to tone assistant: {e}")
                logger.error(traceback.format_exc())
                return f"Error: Failed to generate summary with {tone} tone. Details: {str(e)}"
            
            # Add links to the summary if configured
            if ADD_MESSAGE_LINKS and message_mapping:
                from ..assistants.linking import find_reference_candidates, add_links_to_summary
                
                try:
                    # Find reference candidates in the summary
                    chat_id = messages[0].get("chat", {}).get("id", "") if messages else ""
                    candidates = find_reference_candidates(messages, tone_response)
                    
                    # Add links to the summary
                    linked_summary = add_links_to_summary(
                        tone_response, 
                        candidates, 
                        str(chat_id),
                        max_links=MAX_LINKS_PER_SUMMARY
                    )
                    
                    return linked_summary
                except Exception as e:
                    logger.error(f"Failed to add links to summary: {e}")
                    logger.error(traceback.format_exc())
                    # Return the unlinked summary if linking fails
                    return tone_response
            
            return tone_response
            
        except Exception as e:
            logger.error(f"Error processing summary request: {e}")
            logger.error(traceback.format_exc())
            
            # Provide a detailed error message
            error_details = str(e)
            error_type = type(e).__name__
            
            return f"Error generating summary: {error_type} occurred. Details: {error_details}. Please check logs for more information."
    
    def _format_messages_for_delegation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format messages for the delegation assistant.
        
        Args:
            messages (List[Dict[str, Any]]): List of message dictionaries
        
        Returns:
            str: Formatted messages as a string
        """
        import re
        
        formatted_messages = []
        
        # URL regex pattern that matches common URL formats
        url_pattern = re.compile(
            r'(https?://)?'  # http:// or https:// (optional)
            r'((?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'  # domain
            r'(/[^/\s]*)?'   # path (optional)
        )
        
        # Twitter/X URL pattern
        twitter_pattern = re.compile(
            r'https?://(twitter\.com|x\.com)/[a-zA-Z0-9_]+/status/\d+'
        )
        
        # Image/photo recognition pattern
        photo_pattern = re.compile(r'\bphoto\b|\bimage\b|\bpicture\b', re.IGNORECASE)
        
        for message in messages:
            user_info = f"User {message.get('from', {}).get('id', 'unknown')}"
            username = message.get('from', {}).get('username')
            if username:
                user_info += f" (@{username})"
            
            text = message.get('text', '')
            
            # Process URLs with special handling
            if text:
                # Highlight Twitter/X links
                text = twitter_pattern.sub(r'[TWITTER_LINK: \g<0>]', text)
                
                # Mark other URLs clearly
                text = url_pattern.sub(r'[URL: \g<0>]', text)
            
            # Check if the message has a photo
            if 'photo' in message:
                photo_id = message.get('photo', [{}])[-1].get('file_id', '')
                text += f" [PHOTO: {photo_id}]"
            
            # Check for other media types
            if 'document' in message:
                file_name = message.get('document', {}).get('file_name', 'unnamed_file')
                file_id = message.get('document', {}).get('file_id', '')
                text += f" [DOCUMENT: {file_name} ({file_id})]"
            
            if 'video' in message:
                file_id = message.get('video', {}).get('file_id', '')
                text += f" [VIDEO: {file_id}]"
            
            if 'voice' in message:
                file_id = message.get('voice', {}).get('file_id', '')
                text += f" [VOICE: {file_id}]"
            
            # Format reply messages
            reply_to = message.get('reply_to_message')
            if reply_to:
                reply_text = reply_to.get('text', '')
                if reply_text:
                    # Truncate long replies
                    if len(reply_text) > 50:
                        reply_text = reply_text[:47] + '...'
                    text = f"[In reply to: \"{reply_text}\"] {text}"
            
            formatted_message = f"{user_info}: {text}"
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
        Process sports content using the sports information assistant.
        
        Args:
            sports (List[str]): List of sports to process
            sports_references (List[str]): List of sports references to process
            thread_id (str): The thread ID for the delegation
        
        Returns:
            Dict[str, str]: Dictionary mapping sports to information
        """
        if not sports or not sports_references:
            return {}
        
        logger.info(f"Processing sports information for {sports}")
        
        # Create a new thread for the sports assistant
        sports_thread = await self.assistants_manager.async_create_thread()
        sports_thread_id = sports_thread.id
        
        # Create the content for the sports assistant
        sports_content = f"Please provide information about the following sports references:\n\n"
        sports_content += f"Sports: {', '.join(sports)}\n\n"
        sports_content += f"References: {', '.join(sports_references)}\n\n"
        sports_content += "Please search for recent information and provide a concise summary for each sport."
        
        # Add the content to the thread
        await self.assistants_manager.thread_manager.async_add_message(
            thread_id=sports_thread_id,
            content=sports_content,
            role="user"
        )
        
        # Run the sports assistant
        sports_run = await self.assistants_manager.async_run_assistant(
            assistant_id=self.sports_assistant_id,
            thread_id=sports_thread_id
        )
        
        # Wait for the run to complete
        completed_sports_run = await self.assistants_manager._async_run_until_complete(
            thread_id=sports_thread_id,
            run_id=sports_run.id,
            timeout=60
        )
        
        if completed_sports_run.status != "completed":
            logger.error(f"Sports assistant run failed with status {completed_sports_run.status}")
            return {}
        
        # Get the latest message from the sports assistant
        sports_response = await self.assistants_manager.async_get_latest_message(sports_thread_id)
        
        if not sports_response:
            logger.error("No response from sports assistant")
            return {}
        
        # Extract the content from the sports response
        sports_content = self.assistants_manager.get_message_content(sports_response)
        
        # Parse the sports content as a dictionary
        try:
            # Look for JSON content in the response
            json_match = re.search(r'{.*}', sports_content, re.DOTALL)
            if json_match:
                sports_info = json.loads(json_match.group(0))
            else:
                # If no JSON found, try to extract key-value pairs
                sports_info = {}
                for sport in sports:
                    sport_lower = sport.lower()
                    # Try to extract information about this sport
                    sport_match = re.search(
                        rf'{sport}\s*:\s*(.*?)(?=\n\n|\n[A-Z]|\Z)',
                        sports_content,
                        re.IGNORECASE | re.DOTALL
                    )
                    if sport_match:
                        sports_info[sport] = sport_match.group(1).strip()
        
            return sports_info
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse sports content: {e}")
            logger.error(f"Sports content: {sports_content}")
            return {}
    
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