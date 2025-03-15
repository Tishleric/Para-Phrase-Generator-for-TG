# src/agents/delegation_agent.py
# Delegation agent for orchestrating the multi-agent system
"""
This module defines the DelegationAgent class, which serves as the central
orchestrator for the multi-agent system. The delegation agent analyzes
message content and routes requests to the appropriate specialized agents.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from ..sdk_imports import Handoff, function_tool
from .base_agent import BaseAgent
from ..config import get_agent_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DelegationAgent(BaseAgent):
    """
    Delegation agent for orchestrating the multi-agent system.
    
    This agent analyzes message content and routes requests to the
    appropriate specialized agents based on content cues.
    
    Attributes:
        name (str): The name of the agent
        agent (Agent): The OpenAI Agent instance
        specialized_agents (Dict[str, BaseAgent]): Dictionary of specialized agents
    """
    
    def __init__(self):
        """
        Initialize a DelegationAgent instance.
        """
        instructions = """
        You are the delegation agent for a Telegram message summarization bot.
        Your role is to analyze message content and delegate tasks to specialized agents.
        
        When processing a request to summarize messages:
        1. Analyze the message content for special content types:
           - Twitter links
           - Images
           - Football scores or references
        2. Determine which specialized agents to call based on the content
        3. Pass relevant context to each agent
        4. Integrate the results into a coherent summary

        Your job is not to provide the summary directly, but to delegate tasks
        to the appropriate specialized agents and integrate their responses.
        
        Guidelines for delegation:
        - For Twitter links: Call the Twitter agent to extract and summarize tweet content
        - For images: Call the Photo agent to analyze image content and provide descriptions
        - For football references: Call the Football agent to provide context about matches and players
        - For tone-specific summaries: Always call the appropriate tone agent with the results

        Specialized agents can handle multiple instances of their content type
        (e.g., multiple Twitter links or images).
        """
        
        tools = [
            self._detect_content_types,
            self._extract_entities,
            self._check_for_twitter_links,
            self._check_for_football_references,
            self._check_for_photos,
            self._check_for_general_links
        ]
        
        super().__init__(
            name="Delegation Agent",
            instructions=instructions,
            model=get_agent_model("delegation"),
            tools=tools
        )
        
        self.specialized_agents = {}
        logger.info("Initialized Delegation Agent")
        
        # Register specialized agents
        self._register_specialized_agents()
    
    def _register_specialized_agents(self):
        """
        Register all specialized agents with the delegation agent.
        This method is called during initialization to set up agent handoffs.
        """
        # Import here to avoid circular imports
        from . import get_twitter_agent, get_football_agent, get_photo_agent
        
        # Register the Twitter agent
        twitter_agent = get_twitter_agent()
        self.register_agent("twitter", twitter_agent)
        logger.info("Registered Twitter agent with Delegation Agent")
        
        # Register the Football agent
        football_agent = get_football_agent()
        self.register_agent("football", football_agent)
        logger.info("Registered Football agent with Delegation Agent")
        
        # Register the Photo agent
        photo_agent = get_photo_agent()
        self.register_agent("photo", photo_agent)
        logger.info("Registered Photo agent with Delegation Agent")
    
    def register_agent(self, agent_type: str, agent: BaseAgent) -> None:
        """
        Register a specialized agent.
        
        Args:
            agent_type (str): The type of agent (e.g., "twitter", "photo")
            agent (BaseAgent): The agent instance
        """
        self.specialized_agents[agent_type] = agent
        logger.info(f"Registered {agent_type} agent")
    
    @function_tool
    def _detect_content_types(self, messages: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Detect content types in a list of messages.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Dictionary mapping content types to lists of message indices
        """
        content_types = {
            "twitter": [],
            "football": [],
            "image": [],
        }
        
        for i, message in enumerate(messages):
            # Skip messages with no text
            if "text" not in message:
                continue
            
            text = message.get("text", "")
            
            # Check for Twitter links
            if "twitter.com" in text or "x.com" in text:
                content_types["twitter"].append(i)
            
            # Check for football references
            if any(term in text.lower() for term in ["football", "soccer", "match", "goal", "score"]):
                content_types["football"].append(i)
            
            # Check for images
            if 'photo' in message and message['photo']:
                content_types["image"].append(i)
        
        return content_types
    
    @function_tool
    def _check_for_twitter_links(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for Twitter links in a list of messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with Twitter link information
        """
        twitter_data = {
            "has_links": False,
            "links": [],
            "messages": []
        }
        
        # Enhanced Twitter regex to capture more URL formats
        twitter_regex = r"https?://(?:www\.)?(twitter\.com|x\.com|t\.co)/\S+"
        
        for message in messages:
            if "text" not in message:
                continue
                
            text = message.get("text", "")
            # Log the first 50 characters for debugging
            logger.debug(f"Checking text for Twitter links: {text[:50]}...")
            
            matches = re.finditer(twitter_regex, text)
            
            found_links = False
            for match in matches:
                found_links = True
                twitter_data["has_links"] = True
                full_link = match.group(0).strip()
                twitter_data["links"].append(full_link)
                logger.info(f"Found Twitter link: {full_link}")
            
            if found_links:
                twitter_data["messages"].append(message)
        
        return twitter_data
    
    @function_tool
    def _check_for_general_links(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for general web links in a list of messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Dictionary with link information
        """
        link_data = {
            "has_links": False,
            "links": [],
            "messages": []
        }
        
        # General URL regex that captures most common web URLs
        url_regex = r"https?://(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+(?:/[^\s\)\"\']*)?(?:\s|$|\)|\'|\")"
        
        for message in messages:
            if "text" not in message:
                continue
                
            text = message.get("text", "")
            # Extract URLs with regex
            matches = re.finditer(url_regex, text)
            
            found_links = False
            for match in matches:
                found_links = True
                link_data["has_links"] = True
                full_link = match.group(0).strip()
                link_data["links"].append(full_link)
                logger.info(f"Found link: {full_link}")
            
            if found_links:
                link_data["messages"].append(message)
        
        return link_data
    
    @function_tool
    def _check_for_football_references(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for football references in a list of messages.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Dictionary with football reference information
        """
        football_data = {
            "has_references": False,
            "references": [],
            "messages": []
        }
        
        # Simple pattern checks (a more sophisticated version is in the FootballAgent)
        football_patterns = [
            r"\b\d{1,2}[-:]\d{1,2}\b",  # Score pattern like 2-1
            r"\b(?:goal|score|match|game|playing|player|team|football|soccer)\b",
            r"\b(?:premier league|la liga|bundesliga|serie a|ligue 1|champions league)\b",
        ]
        
        for message in messages:
            if "text" not in message:
                continue
                
            text = message.get("text", "").lower()
            
            for pattern in football_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    football_data["has_references"] = True
                    football_data["references"].extend(matches)
                    if message not in football_data["messages"]:
                        football_data["messages"].append(message)
        
        return football_data
    
    @function_tool
    def _check_for_photos(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for photos in a list of messages.
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Dictionary with photo information
        """
        photo_data = {
            "has_photos": False,
            "photo_count": 0,
            "messages": []
        }
        
        for message in messages:
            if 'photo' in message and message['photo']:
                photo_data["has_photos"] = True
                photo_data["photo_count"] += 1
                photo_data["messages"].append(message)
        
        return photo_data
    
    @function_tool
    def _extract_entities(self, messages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract named entities from messages.
        
        This method uses spaCy NLP to identify people, organizations,
        locations, and other entities in message text.
        
        Args:
            messages (List[Dict[str, Any]]): The messages to extract entities from
            
        Returns:
            Dict[str, List[str]]: Dictionary of entity types and their values
        """
        try:
            # Initialize spaCy - we'll use the medium English model
            import spacy
            
            # Try to load spaCy model, downloading if necessary
            try:
                nlp = spacy.load("en_core_web_md")
                logger.info("Loaded spaCy model en_core_web_md")
            except OSError:
                # If model isn't available, download it (first time usage)
                logger.info("Downloading spaCy model en_core_web_md")
                spacy.cli.download("en_core_web_md")
                nlp = spacy.load("en_core_web_md")
            
            # Initialize entity collections
            entities = {
                "people": [],
                "organizations": [],
                "locations": [],
                "other": []
            }
            
            # Process each message
            for message in messages:
                if "text" not in message:
                    continue
                
                text = message.get("text", "")
                if not text:
                    continue
                
                # Process with spaCy
                doc = nlp(text)
                
                # Extract entities
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        entities["people"].append(ent.text)
                    elif ent.label_ in ["ORG", "NORP"]:
                        entities["organizations"].append(ent.text)
                    elif ent.label_ in ["GPE", "LOC"]:
                        entities["locations"].append(ent.text)
                    else:
                        # Store other entity types separately for potential use
                        entities["other"].append(f"{ent.text} ({ent.label_})")
            
            # Remove duplicates and sort
            for entity_type in entities:
                entities[entity_type] = sorted(list(set(entities[entity_type])))
            
            return entities
            
        except ImportError:
            # Fallback if spaCy is not available
            logger.warning("spaCy not available. Using simple entity extraction fallback.")
            return self._extract_entities_simple(messages)
        except Exception as e:
            # General fallback for any errors in entity extraction
            logger.error(f"Error in entity extraction: {str(e)}")
            return self._extract_entities_simple(messages)
    
    def _extract_entities_simple(self, messages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Simple entity extraction fallback when spaCy is not available.
        
        This method uses simple regex patterns to identify potential
        entities based on capitalization and common patterns.
        
        Args:
            messages (List[Dict[str, Any]]): The messages to extract entities from
            
        Returns:
            Dict[str, List[str]]: Dictionary of entity types and their values
        """
        # Initialize entity collections
        entities = {
            "people": [],
            "organizations": [],
            "locations": [],
            "other": []
        }
        
        # Common name prefixes/titles to help identify people
        name_prefixes = ["Mr", "Mrs", "Ms", "Dr", "Prof", "Sir", "Madam", "Miss", "Lord", "Lady"]
        
        # Common organization suffixes to help identify organizations
        org_suffixes = ["Inc", "LLC", "Ltd", "Corp", "Corporation", "Company", "Co", "Foundation", "Association", "Institute"]
        
        # Simple location identifiers (major cities and countries)
        common_locations = [
            "New York", "London", "Paris", "Tokyo", "Beijing", "Moscow", "Berlin", "Rome", "Madrid",
            "USA", "UK", "China", "Russia", "India", "Japan", "Germany", "France", "Italy", "Spain",
            "United States", "United Kingdom", "European Union", "North America", "South America",
            "Africa", "Asia", "Europe", "Australia"
        ]
        
        for message in messages:
            if "text" not in message:
                continue
            
            text = message.get("text", "")
            if not text:
                continue
            
            # Split into sentences to better handle context
            sentences = re.split(r'[.!?]\s+', text)
            
            for sentence in sentences:
                # Look for potential names (words with Mr, Mrs, etc.)
                for prefix in name_prefixes:
                    pattern = rf'\b{prefix}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
                    matches = re.findall(pattern, sentence)
                    entities["people"].extend(matches)
                
                # Look for capitalized phrases that might be organizations
                # This pattern looks for 2+ capitalized words in sequence
                org_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
                org_candidates = re.findall(org_pattern, sentence)
                
                for candidate in org_candidates:
                    # Check if it ends with a common organization suffix
                    if any(candidate.endswith(suffix) for suffix in org_suffixes):
                        entities["organizations"].append(candidate)
                
                # Check for common locations
                for location in common_locations:
                    if location in sentence:
                        entities["locations"].append(location)
            
            # Look for @ mentions as potential people
            mentions = re.findall(r'@(\w+)', text)
            if mentions:
                entities["people"].extend([f"@{mention}" for mention in mentions])
            
            # Add hashtags to other entities
            hashtags = re.findall(r'#(\w+)', text)
            if hashtags:
                entities["other"].extend([f"#{hashtag}" for hashtag in hashtags])
        
        # Remove duplicates and sort
        for entity_type in entities:
            entities[entity_type] = sorted(list(set(entities[entity_type])))
        
        return entities
    
    def process_summary_request(self, messages: List[Dict[str, Any]], tone: str) -> str:
        """
        Process a request to summarize messages.
        
        This is the main entry point for the delegation agent.
        
        Args:
            messages: List of message dictionaries
            tone: The tone to use for the summary
        
        Returns:
            String summary of the messages
        """
        if not messages:
            return "No messages to summarize."
        
        logger.info(f"Processing summary request for {len(messages)} messages with tone {tone}")
        
        # Initialize results from specialized agents
        twitter_result = None
        football_result = None
        photo_result = None
        
        # Format messages for easier processing
        formatted_messages = []
        for i, msg in enumerate(messages):
            sender = msg.get("from", {}).get("username", "Unknown")
            text = msg.get("text", "")
            
            if not text and 'photo' in msg and msg['photo']:
                formatted_messages.append(f"{sender} sent an image.")
            else:
                formatted_messages.append(f"{sender}: {text}")
        
        # Check for Twitter links
        twitter_data = self._check_for_twitter_links(messages)
        if twitter_data["has_links"] and "twitter" in self.specialized_agents:
            twitter_agent = self.specialized_agents["twitter"]
            twitter_result = twitter_agent.process_twitter_links(twitter_data["messages"])
            logger.info("Twitter links processed")
        
        # Check for football references
        football_data = self._check_for_football_references(messages)
        if football_data["has_references"] and "football" in self.specialized_agents:
            football_agent = self.specialized_agents["football"]
            football_result = football_agent.process_football_references(football_data["messages"])
            logger.info("Football references processed")
        
        # Check for photos
        photo_data = self._check_for_photos(messages)
        if photo_data["has_photos"] and "photo" in self.specialized_agents:
            photo_agent = self.specialized_agents["photo"]
            photo_result = photo_agent.process_images(photo_data["messages"])
            logger.info("Photos processed")
        
        # Get the tone agent
        from . import get_tone_agent
        tone_agent = get_tone_agent(tone)
        
        # Create a context object for the tone agent
        context = {
            "messages": formatted_messages,
            "specialized_results": {
                "twitter": twitter_result,
                "football": football_result,
                "photo": photo_result
            }
        }
        
        # Generate the summary using the tone agent
        summary = tone_agent.generate_summary(context)
        
        return summary 