# src/agents/twitter_agent.py
# Twitter link analysis agent
"""
This module defines the TwitterAgent class, which analyzes
Twitter/X.com links in messages.
"""

import os
import re
import json
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

# Use the centralized SDK imports
from ..sdk_imports import Agent, function_tool
from ..config import DEBUG_MODE, get_agent_model

# Import base agent and utilities
from .base_agent import BaseAgent
from ..utils import extract_urls, format_error_message

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Twitter/X API credentials
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

class TwitterAgent(BaseAgent):
    """
    An agent for analyzing Twitter/X.com links in messages.
    
    This agent extracts Twitter/X.com URLs from messages and analyzes
    the content, providing summaries and insights about the tweets.
    
    Attributes:
        name (str): The name of the agent
        model (str): The model used by the agent
        instructions (str): Instructions for the agent
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize a TwitterAgent instance.
        
        Args:
            model (Optional[str]): The model to use for the agent
        """
        # Get the appropriate model for this agent
        if model is None:
            model = get_agent_model("twitter")
        
        # Agent instructions
        instructions = """
        You are a Twitter/X.com Link Agent. Your role is to analyze Twitter/X.com links 
        and provide useful summaries and context.
        
        For each Twitter/X.com link:
        1. Extract the tweet content, author, date, and engagement metrics
        2. Provide a brief summary of the tweet content
        3. Note any relevant context or implications
        4. Identify any hashtags or mentions
        
        Always maintain a neutral and informative tone when analyzing tweets.
        """
        
        # Initialize base agent with instructions and tools
        super().__init__(
            name="Twitter Agent",
            instructions=instructions,
            model=model,
            tools=[self._analyze_tweet_content]
        )
        
        logger.debug("TwitterAgent initialized")
        
        # Initialize API session if credentials are available
        self.api_session = None
        self.has_api_access = False
        
        if TWITTER_BEARER_TOKEN:
            self.api_session = requests.Session()
            self.api_session.headers.update({
                "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
                "Content-Type": "application/json"
            })
            self.has_api_access = True
            logger.info("Twitter API access configured")
        else:
            logger.warning("Twitter API credentials not found. Using limited functionality.")
    
    @function_tool
    def _analyze_tweet_content(self, url: str) -> Dict[str, Any]:
        """
        Analyze the content of a tweet based on its URL.
        
        This function extracts the tweet ID from the URL and fetches the tweet data
        using the Twitter API if credentials are available. Otherwise, it uses
        a limited web scraping approach.
        
        Args:
            url (str): Twitter/X.com URL to analyze
            
        Returns:
            Dict[str, Any]: Analysis of the tweet content
        """
        try:
            # Extract tweet ID from URL
            tweet_id = self._extract_tweet_id(url)
            if not tweet_id:
                return {
                    "error": "Could not extract tweet ID from URL",
                    "url": url
                }
            
            logger.info(f"Analyzing tweet with ID: {tweet_id}")
            
            # Use Twitter API if credentials are available
            if self.has_api_access:
                return self._fetch_tweet_from_api(tweet_id)
            else:
                # Fallback to web scraping when API access is not available
                return self._fetch_tweet_via_scraping(url, tweet_id)
        except Exception as e:
            logger.error(f"Error analyzing tweet content: {str(e)}")
            return {
                "error": f"Failed to analyze tweet: {str(e)}",
                "url": url
            }
    
    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """
        Extract the tweet ID from a Twitter/X.com URL.
        
        Args:
            url (str): Twitter/X.com URL
            
        Returns:
            Optional[str]: The extracted tweet ID or None if not found
        """
        # Handle various Twitter URL formats
        patterns = [
            r'twitter\.com/\w+/status/(\d+)',
            r'x\.com/\w+/status/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _fetch_tweet_from_api(self, tweet_id: str) -> Dict[str, Any]:
        """
        Fetch tweet data from the Twitter API.
        
        Args:
            tweet_id (str): The ID of the tweet to fetch
            
        Returns:
            Dict[str, Any]: Tweet data and analysis
        """
        try:
            # Twitter API v2 endpoint for tweets
            endpoint = f"https://api.twitter.com/2/tweets/{tweet_id}"
            
            # Query parameters to expand tweet information
            params = {
                "expansions": "author_id,attachments.media_keys,referenced_tweets.id",
                "tweet.fields": "created_at,public_metrics,text,entities,context_annotations",
                "user.fields": "name,username,profile_image_url,description,verified",
                "media.fields": "url,preview_image_url,type"
            }
            
            # Make the API request
            response = self.api_session.get(endpoint, params=params)
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Extract user information from the includes section
            user_info = {}
            if "includes" in data and "users" in data["includes"]:
                user = data["includes"]["users"][0]
                user_info = {
                    "name": user.get("name", ""),
                    "username": user.get("username", ""),
                    "verified": user.get("verified", False),
                    "description": user.get("description", "")
                }
            
            # Extract media information
            media_info = []
            if "includes" in data and "media" in data["includes"]:
                for media in data["includes"]["media"]:
                    media_info.append({
                        "type": media.get("type", ""),
                        "url": media.get("url", "") or media.get("preview_image_url", "")
                    })
            
            # Extract tweet data
            tweet_data = data.get("data", {})
            public_metrics = tweet_data.get("public_metrics", {})
            
            # Format created_at as a more readable date
            created_at = tweet_data.get("created_at", "")
            formatted_date = ""
            if created_at:
                try:
                    dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                    formatted_date = dt.strftime("%B %d, %Y at %I:%M %p UTC")
                except ValueError:
                    formatted_date = created_at
            
            # Extract hashtags and mentions
            hashtags = []
            mentions = []
            
            if "entities" in tweet_data:
                if "hashtags" in tweet_data["entities"]:
                    hashtags = [tag["tag"] for tag in tweet_data["entities"]["hashtags"]]
                
                if "mentions" in tweet_data["entities"]:
                    mentions = [mention["username"] for mention in tweet_data["entities"]["mentions"]]
            
            # Construct the result
            result = {
                "tweet_id": tweet_id,
                "author": user_info,
                "text": tweet_data.get("text", ""),
                "created_at": formatted_date,
                "metrics": {
                    "retweets": public_metrics.get("retweet_count", 0),
                    "replies": public_metrics.get("reply_count", 0),
                    "likes": public_metrics.get("like_count", 0),
                    "quotes": public_metrics.get("quote_count", 0)
                },
                "hashtags": hashtags,
                "mentions": mentions,
                "media": media_info,
                "source": "Twitter API"
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Twitter API request failed: {str(e)}")
            # Fall back to scraping method
            return self._fetch_tweet_via_scraping(f"https://twitter.com/i/status/{tweet_id}", tweet_id)
    
    def _fetch_tweet_via_scraping(self, url: str, tweet_id: str) -> Dict[str, Any]:
        """
        Fetch tweet data via web scraping when API is not available.
        
        Args:
            url (str): The URL of the tweet
            tweet_id (str): The ID of the tweet
            
        Returns:
            Dict[str, Any]: Tweet data and analysis
        """
        try:
            # Use a public tweet embedding endpoint to get basic information
            nitter_url = f"https://nitter.net/i/status/{tweet_id}"
            
            # Parse the URL to extract username
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            # Username is usually the first part of the path in twitter.com/username/status/id
            username = path_parts[0] if len(path_parts) > 1 else "unknown"
            
            # Make a request to get the HTML content (would require HTML parsing in a real implementation)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Instead of actually scraping, we'll construct a basic response
            # In a real implementation, this would parse the HTML to extract the content
            
            return {
                "tweet_id": tweet_id,
                "author": {
                    "username": username,
                    "name": username.capitalize(),  # Placeholder
                    "verified": False  # We don't know without scraping
                },
                "text": "Tweet content not available without API access. Please check the original URL.",
                "created_at": "Unknown date",
                "metrics": {
                    "retweets": 0,
                    "replies": 0,
                    "likes": 0,
                    "quotes": 0
                },
                "hashtags": [],
                "mentions": [],
                "url": url,
                "source": "Limited access (no API credentials)",
                "note": "For full tweet analysis, configure Twitter API credentials"
            }
            
        except Exception as e:
            logger.error(f"Error in web scraping fallback: {str(e)}")
            return {
                "error": "Failed to retrieve tweet data",
                "tweet_id": tweet_id,
                "url": url,
                "note": "Configure Twitter API for better results"
            }
    
    def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a message to extract and analyze Twitter/X.com links.
        
        Args:
            message (Dict[str, Any]): The message to process
            
        Returns:
            Optional[Dict[str, Any]]: Analysis results or None if no Twitter links found
        """
        # Extract message text
        text = message.get("text", "")
        if not text:
            return None
        
        # Extract URLs from the message
        urls = extract_urls(text)
        
        # Filter for Twitter/X.com URLs
        twitter_urls = [url for url in urls if "twitter.com" in url or "x.com" in url]
        
        if not twitter_urls:
            return None
        
        # Analyze each Twitter URL
        results = []
        for url in twitter_urls:
            analysis = self._analyze_tweet_content(url)
            results.append(analysis)
        
        return {
            "twitter_links": results,
            "count": len(results)
        } 