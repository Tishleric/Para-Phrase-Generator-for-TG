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
    
    This class provides the built-in web search functionality from OpenAI.
    
    Usage:
        tools = [WebSearchTool().as_tool()]
    """
    
    @staticmethod
    def as_tool() -> Dict:
        """
        Get the web search tool definition using OpenAI's built-in capability.
        
        Returns:
            Dict: A web search tool definition
        """
        return {
            "type": "web_search"
        }


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
    
    This class provides a tool for analyzing images directly from Telegram messages
    using OpenAI's vision-capable models. It extracts text content, identifies objects,
    and generates descriptive summaries of images.
    
    The tool leverages the fetch_telegram_file utility to retrieve image data
    from Telegram servers before processing it with OpenAI's API.
    
    Usage:
        tools = [ImageAnalysisTool().as_tool()]
    """
    
    def __init__(self):
        """
        Initialize the ImageAnalysisTool with OpenAI client and file fetching capability.
        
        Requires:
            - OPENAI_API_KEY environment variable
            - TELEGRAM_BOT_TOKEN environment variable (used by fetch_telegram_file)
        """
        # Import here to avoid circular imports
        import os
        import base64
        from openai import OpenAI
        from ..utils import fetch_telegram_file
        
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.fetch_telegram_file = fetch_telegram_file
    
    def analyze_image(self, file_id: str) -> Dict[str, Any]:
        """
        Analyze an image using OpenAI's vision-capable models.
        
        This method retrieves the image from Telegram servers using its file_id,
        then sends it to OpenAI's API for analysis. The analysis includes
        text extraction, object identification, and descriptive summary.
        
        Args:
            file_id (str): The Telegram file ID of the image to analyze
            
        Returns:
            Dict[str, Any]: Analysis results including:
                - text_content: Any text detected in the image
                - objects: List of objects identified in the image
                - description: Detailed description of the image
                - error: Error message if processing failed
        """
        import io
        import logging
        import base64
        import traceback
        
        logger = logging.getLogger(__name__)
        
        try:
            # Fetch the image data from Telegram
            logger.info(f"Fetching image with file_id: {file_id}")
            image_data = self.fetch_telegram_file(file_id)
            
            if not image_data:
                logger.error(f"Failed to fetch image with file_id: {file_id}")
                return {
                    "text_content": "",
                    "objects": [],
                    "description": "Failed to process the image.",
                    "error": "Image data could not be retrieved."
                }
            
            # Convert image data to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Use GPT-4o for image analysis (vision-capable model)
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Vision-capable model
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an AI that analyzes images. Identify text, objects, and provide a description."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this image and provide text content, objects, and a description."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Extract the analysis
            analysis = response.choices[0].message.content
            
            # Parse the analysis for structured data
            # This is a simple implementation; could be more sophisticated
            text_content = ""
            objects = []
            description = analysis
            
            # Look for text content section
            text_match = re.search(r'(?i)text content:?(.*?)(?:objects:|description:|$)', analysis, re.DOTALL)
            if text_match:
                text_content = text_match.group(1).strip()
            
            # Look for objects section
            objects_match = re.search(r'(?i)objects:?(.*?)(?:text content:|description:|$)', analysis, re.DOTALL)
            if objects_match:
                objects_text = objects_match.group(1).strip()
                # Split by commas or newlines
                objects = [obj.strip() for obj in re.split(r'[,\n]', objects_text) if obj.strip()]
            
            # Look for description section
            desc_match = re.search(r'(?i)description:?(.*?)(?:text content:|objects:|$)', analysis, re.DOTALL)
            if desc_match:
                description = desc_match.group(1).strip()
            
            return {
                "text_content": text_content,
                "objects": objects,
                "description": description,
                "full_analysis": analysis  # Include the full analysis for reference
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "text_content": "",
                "objects": [],
                "description": "Failed to analyze the image due to an error.",
                "error": str(e)
            }
    
    def as_tool(self) -> Dict:
        """
        Get the image analysis tool definition for the OpenAI Assistants API.
        
        Returns:
            Dict: An image analysis tool definition
        """
        return function_tool(
            name="analyze_image",
            description="Analyze an image from Telegram to extract text, identify objects, and provide a description",
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