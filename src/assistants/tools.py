"""
Assistants API Tools

This module provides tool definitions for use with the OpenAI Assistants API.
"""

import json
from typing import Dict, List, Any, Optional, Union, Callable


def function_tool(name: str, description: str, parameters: Optional[Dict] = None) -> Dict:
    """
    Create a function tool for the OpenAI Assistants API.
    
    Args:
        name (str): The name of the function
        description (str): A description of what the function does
        parameters (Dict, optional): The parameters schema for the function.
            Defaults to None.
    
    Returns:
        Dict: A function tool definition
    """
    function = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
        }
    }
    
    if parameters:
        function["function"]["parameters"] = parameters
    else:
        function["function"]["parameters"] = {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    return function


class WebSearchTool:
    """
    Web search tool for the OpenAI Assistants API.
    
    This class provides a web search tool that can be used with the OpenAI Assistants API.
    The actual search is performed by OpenAI's built-in search capability.
    
    Usage:
        tools = [WebSearchTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the web search tool definition.
        
        Returns:
            Dict: A web search tool definition
        """
        try:
            # First try with web_search type - newer OpenAI API versions
            return {
                "type": "web_search"
            }
        except Exception as e:
            # If web_search isn't supported (older API or restricted environment),
            # fall back to a function-based implementation
            if "invalid_value" in str(e).lower() or "web_search" in str(e).lower():
                return function_tool(
                    name="web_search",
                    description="Search the web for information",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                )
            else:
                # If it's another type of error, re-raise it
                raise


class CodeInterpreterTool:
    """
    Code interpreter tool for the OpenAI Assistants API.
    
    This class provides a code interpreter tool that can be used with the OpenAI
    Assistants API. The code interpreter allows assistants to execute Python code
    in a sandboxed environment.
    
    Usage:
        tools = [CodeInterpreterTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the code interpreter tool definition.
        
        Returns:
            Dict: A code interpreter tool definition
        """
        return {
            "type": "code_interpreter"
        }


class FileSearchTool:
    """
    File search tool for the OpenAI Assistants API.
    
    This class provides a file search tool that can be used with the OpenAI Assistants API.
    The file search tool allows assistants to search through and retrieve information
    from files that have been attached to them.
    
    Usage:
        tools = [FileSearchTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the file search tool definition.
        
        Returns:
            Dict: A file search tool definition
        """
        return {
            "type": "file_search"
        }


class FileReaderTool:
    """
    File reader tool for the OpenAI Assistants API.
    
    This class provides a file reader tool that can be used with the OpenAI Assistants API.
    The file reader tool allows assistants to read files through a custom function call.
    
    Usage:
        tools = [FileReaderTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the file reader tool definition.
        
        Returns:
            Dict: A file reader tool definition
        """
        return function_tool(
            name="read_file",
            description="Read the contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The ID of the file to read"
                    }
                },
                "required": ["file_id"]
            }
        )


class TelegramMessageLinkTool:
    """
    Telegram message link tool for the OpenAI Assistants API.
    
    This class provides a tool that generates links to Telegram messages.
    
    Usage:
        tools = [TelegramMessageLinkTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the Telegram message link tool definition.
        
        Returns:
            Dict: A Telegram message link tool definition
        """
        return function_tool(
            name="generate_telegram_link",
            description="Generate a link to a Telegram message",
            parameters={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "The ID of the chat"
                    },
                    "message_id": {
                        "type": "integer",
                        "description": "The ID of the message"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to use as the link text"
                    }
                },
                "required": ["chat_id", "message_id", "text"]
            }
        )


class TwitterSummaryTool:
    """
    Twitter summary tool for the OpenAI Assistants API.
    
    This class provides a tool that summarizes Twitter posts.
    
    Usage:
        tools = [TwitterSummaryTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the Twitter summary tool definition.
        
        Returns:
            Dict: A Twitter summary tool definition
        """
        return function_tool(
            name="summarize_twitter_post",
            description="Summarize a Twitter post",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the Twitter post to summarize"
                    }
                },
                "required": ["url"]
            }
        )


class FootballInfoTool:
    """
    Football information tool for the OpenAI Assistants API.
    
    This class provides a tool that retrieves information about football matches and teams.
    
    Usage:
        tools = [FootballInfoTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the football information tool definition.
        
        Returns:
            Dict: A football information tool definition
        """
        return function_tool(
            name="get_football_info",
            description="Retrieve information about football matches and teams",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query about football matches or teams"
                    }
                },
                "required": ["query"]
            }
        )


class ImageAnalysisTool:
    """
    Image analysis tool for the OpenAI Assistants API.
    
    This class provides a tool that analyzes images from Telegram using file IDs.
    
    Usage:
        tools = [ImageAnalysisTool().as_tool()]
    """
    
    def __init__(self):
        """
        Initialize the ImageAnalysisTool.
        """
        import os
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            import logging
            logging.warning("No Telegram bot token found. Image analysis will not work properly.")
    
    def analyze_image(self, file_id: str) -> Dict[str, Any]:
        """
        Analyze an image from a Telegram file ID.
        
        Args:
            file_id (str): The Telegram file ID of the image to analyze
            
        Returns:
            Dict[str, Any]: Analysis of the image content
        """
        import logging
        import requests
        import base64
        from openai import OpenAI
        
        logger = logging.getLogger(__name__)
        
        try:
            if not self.bot_token:
                return {
                    "error": "No Telegram bot token configured",
                    "description": "Image could not be analyzed because no Telegram bot token is configured."
                }
            
            # Get the file path from Telegram
            file_info_url = f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}"
            file_info_response = requests.get(file_info_url)
            file_info = file_info_response.json()
            
            if not file_info.get("ok"):
                return {
                    "error": "Failed to get file info from Telegram",
                    "description": f"Error: {file_info.get('description', 'Unknown error')}"
                }
            
            # Get the file path
            file_path = file_info["result"]["file_path"]
            
            # Construct the download URL
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            
            # Download the image
            image_response = requests.get(download_url)
            if image_response.status_code != 200:
                return {
                    "error": "Failed to download image from Telegram",
                    "description": f"HTTP status code: {image_response.status_code}"
                }
            
            # Encode the image as base64
            image_base64 = base64.b64encode(image_response.content).decode('utf-8')
            
            # Use OpenAI's vision capabilities to analyze the image
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a visual analysis assistant. Describe the image in detail, noting visible objects, people, text, colors, and context."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please analyze this image and describe what you see:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Extract the analysis from the response
            analysis = response.choices[0].message.content
            
            # Structure the analysis
            return {
                "description": analysis,
                "file_id": file_id,
                "text_content": self._extract_text_content(analysis),
                "objects": self._extract_objects(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                "error": f"Failed to analyze image: {str(e)}",
                "description": "An error occurred while analyzing the image."
            }
    
    def _extract_text_content(self, analysis: str) -> str:
        """
        Extract text content from the analysis.
        
        Args:
            analysis (str): The analysis text
            
        Returns:
            str: Extracted text content
        """
        import re
        
        # Look for text content in the analysis
        text_patterns = [
            r"The text (?:says|reads) [\"']([^\"']+)[\"']",
            r"There is text that says [\"']([^\"']+)[\"']",
            r"The text [\"']([^\"']+)[\"'] is visible",
            r"Text visible: [\"']([^\"']+)[\"']"
        ]
        
        for pattern in text_patterns:
            matches = re.findall(pattern, analysis)
            if matches:
                return " ".join(matches)
        
        # If no text was found via patterns but "text" is mentioned
        if "text" in analysis.lower():
            # Look for sentence containing "text"
            text_sentences = [s for s in analysis.split('.') if "text" in s.lower()]
            if text_sentences:
                return text_sentences[0].strip()
        
        return ""
    
    def _extract_objects(self, analysis: str) -> List[str]:
        """
        Extract objects from the analysis.
        
        Args:
            analysis (str): The analysis text
            
        Returns:
            List[str]: Extracted objects
        """
        import re
        
        # Extract objects using patterns
        object_patterns = [
            r"I can see ([^\.]+)",
            r"The image shows ([^\.]+)",
            r"There (?:is|are) ([^\.]+)",
            r"The photo contains ([^\.]+)"
        ]
        
        objects = []
        for pattern in object_patterns:
            matches = re.findall(pattern, analysis)
            for match in matches:
                # Split by commas and "and" to get individual objects
                items = re.split(r',|\sand\s', match)
                objects.extend([item.strip() for item in items if item.strip()])
        
        # Remove duplicates
        return list(set(objects))
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the image analysis tool definition.
        
        Returns:
            Dict: An image analysis tool definition
        """
        return function_tool(
            name="analyze_image",
            description="Analyze an image from a Telegram file ID",
            parameters={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The Telegram file ID of the image to analyze"
                    }
                },
                "required": ["file_id"]
            }
        ) 