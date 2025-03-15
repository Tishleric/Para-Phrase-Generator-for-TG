"""
Photo Content Analysis Agent for the Para-Phrase Generator.

This agent is responsible for analyzing image content from Telegram messages and
generating textual descriptions that can be included in the overall summary.

It uses OpenAI's vision capabilities to analyze images and extract their content.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import base64
import logging
import re
import requests
import os
from io import BytesIO
from PIL import Image

from src.sdk_imports import (
    Agent, function_tool, SDK_AVAILABLE
)
from src.agents.base_agent import BaseAgent
from src.config import DEBUG_MODE, get_agent_model, DEAF_TONE_SKIP_FEATURES

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the maximum image size for processing
MAX_IMAGE_WIDTH = 1024
MAX_IMAGE_HEIGHT = 1024
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024  # 4MB

class PhotoAgent(BaseAgent):
    """
    Agent responsible for analyzing image content from Telegram messages.
    
    This agent uses OpenAI's vision capabilities to analyze images and extract 
    meaningful descriptions that can be included in the summary.
    """
    
    def __init__(self, model: Optional[str] = None, current_tone: Optional[str] = None):
        """
        Initialize the Photo Agent.
        
        Args:
            model: The model to use for image analysis (must support vision capabilities)
            current_tone: The current conversation tone
        """
        # Store the current tone
        self.current_tone = current_tone or "stoic"
        
        # Skip initialization for deaf tone
        if self.current_tone == "deaf" and "photo" in DEAF_TONE_SKIP_FEATURES:
            logger.info("PhotoAgent initialization skipped for deaf tone")
            self.is_active = False
            return

        # Otherwise, continue with normal initialization
        self.is_active = True
        
        # Get the appropriate model for this agent
        if model is None:
            model = get_agent_model("photo")
        
        # Check if the model has vision capabilities
        self.has_vision_capabilities = self._check_vision_capabilities(model)
        
        # Agent instructions
        instructions = """
        You are a Photo Analysis Agent specializing in understanding and describing images.
        
        For each image you analyze:
        1. Provide a detailed description of the visual content
        2. Identify key objects, people, text, and other elements
        3. Infer context and meaning when possible
        4. Note any text visible in the image
        5. If appropriate, suggest relevant topics or themes
        
        Be thorough but concise in your analysis, focusing on what's most relevant.
        If an image contains inappropriate content, politely note this without describing it in detail.
        """
        
        # Initialize base agent with instructions and tools
        super().__init__(
            name="Photo Analysis Agent",
            instructions=instructions,
            model=model,
            tools=[self._analyze_image]
        )
        
        logger.debug(f"PhotoAgent initialized with model {model}, vision capabilities: {self.has_vision_capabilities}")
    
    def _check_vision_capabilities(self, model: str) -> bool:
        """
        Check if the model has vision capabilities.
        
        Args:
            model (str): The model to check
            
        Returns:
            bool: True if the model has vision capabilities, False otherwise
        """
        # List of models known to have vision capabilities
        vision_models = [
            "gpt-4o", "gpt-4-vision", "gpt-4-turbo-vision", 
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
            "claude-3-5-sonnet"
        ]
        
        # Check if the model is in the vision models list
        for vision_model in vision_models:
            if vision_model in model.lower():
                return True
        
        # Default to False for unknown models
        return False
    
    @function_tool
    def _analyze_image(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze an image from a URL.
        
        This function downloads an image from a URL and uses OpenAI's vision capabilities
        to analyze and describe the image content.
        
        Args:
            image_url (str): URL of the image to analyze
            
        Returns:
            Dict[str, Any]: Analysis of the image content
        """
        try:
            logger.info(f"Analyzing image from URL: {image_url}")
            
            # Use OpenAI's API with vision capabilities to analyze the image
            from openai import OpenAI
            
            # Initialize OpenAI client
            client = OpenAI()
            
            # Download and prepare the image
            image_data = self._prepare_image(image_url)
            if not image_data:
                return {
                    "error": "Failed to download or process image",
                    "url": image_url
                }
            
            # Encode image as base64 for API
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # For models with vision capabilities
            if self.has_vision_capabilities:
                # Create a chat completion with the image
                response = client.chat.completions.create(
                    model="gpt-4o", # Hard-coded for reliable vision capability
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
                
                # Parse the analysis to extract structured information
                return self._structure_image_analysis(analysis, image_url)
            else:
                # For models without vision capabilities
                return {
                    "error": "The current model does not support image analysis",
                    "url": image_url,
                    "note": "Configure a vision-capable model like GPT-4o for image analysis"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            return {
                "error": f"Failed to analyze image: {str(e)}",
                "url": image_url
            }
    
    def _prepare_image(self, image_url: str) -> Optional[bytes]:
        """
        Download, validate, and prepare an image for analysis.
        
        Args:
            image_url (str): URL of the image to download
            
        Returns:
            Optional[bytes]: The processed image data, or None if processing failed
        """
        try:
            # Download the image
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image: {content_type}")
                return None
            
            # Read the image data
            image_data = BytesIO(response.content)
            
            # Validate and process the image
            with Image.open(image_data) as img:
                # Convert to RGB if needed
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Resize if too large
                if img.width > MAX_IMAGE_WIDTH or img.height > MAX_IMAGE_HEIGHT:
                    # Calculate new dimensions while preserving aspect ratio
                    ratio = min(MAX_IMAGE_WIDTH / img.width, MAX_IMAGE_HEIGHT / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    
                    # Resize the image
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert the processed image back to bytes
                output = BytesIO()
                img.save(output, format='JPEG', quality=85)
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Error preparing image: {str(e)}")
            return None
    
    def _structure_image_analysis(self, analysis: str, image_url: str) -> Dict[str, Any]:
        """
        Structure the raw text analysis into a more usable format.
        
        Args:
            analysis (str): The raw text analysis from the vision model
            image_url (str): The original image URL
            
        Returns:
            Dict[str, Any]: Structured analysis results
        """
        # Extract potential sections from the analysis
        result = {
            "description": analysis,
            "url": image_url,
            "objects": [],
            "text_content": "",
            "people": [],
            "scene_type": "",
            "colors": []
        }
        
        # Extract objects (using a simple approach)
        object_patterns = [
            r"I can see ([^\.]+)",
            r"The image shows ([^\.]+)",
            r"There (?:is|are) ([^\.]+)",
            r"The photo contains ([^\.]+)"
        ]
        
        for pattern in object_patterns:
            matches = re.findall(pattern, analysis)
            for match in matches:
                # Split by commas and "and" to get individual objects
                items = re.split(r',|\sand\s', match)
                result["objects"].extend([item.strip() for item in items if item.strip()])
        
        # Remove duplicates
        result["objects"] = list(set(result["objects"]))
        
        # Extract text content
        text_patterns = [
            r"The text (?:says|reads) [\"']([^\"']+)[\"']",
            r"There is text that says [\"']([^\"']+)[\"']",
            r"The text [\"']([^\"']+)[\"'] is visible",
            r"Text visible: [\"']([^\"']+)[\"']"
        ]
        
        for pattern in text_patterns:
            matches = re.findall(pattern, analysis)
            if matches:
                result["text_content"] = " ".join(matches)
                break
        
        # If no text was found via patterns but "text" is mentioned
        if not result["text_content"] and "text" in analysis.lower():
            # Look for sentence containing "text"
            text_sentences = [s for s in analysis.split('.') if "text" in s.lower()]
            if text_sentences:
                result["text_content"] = text_sentences[0].strip()
        
        return result
    
    def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a message to extract and analyze photos.
        
        Args:
            message (Dict[str, Any]): The message to process
            
        Returns:
            Optional[Dict[str, Any]]: Analysis results or None if no photos found
        """
        # Skip processing for deaf tone
        if not self.is_active:
            return None
            
        # Check if the message contains a photo
        if "photo" not in message:
            return None
        
        photo_data = message.get("photo", [])
        if not photo_data or not isinstance(photo_data, list):
            return None
        
        results = []
        
        for photo in photo_data:
            # Extract file_id (for Telegram)
            file_id = photo.get("file_id")
            
            if not file_id:
                logger.warning(f"No file_id for photo in message {message.get('message_id', 'unknown')}")
                continue
            
            # For Telegram integration, we'd need the bot token and API
            # to get an actual file URL. Since we don't have that in this
            # implementation, we'll create a placeholder URL for demonstration
            
            # In a real Telegram bot implementation:
            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            
            if bot_token:
                # If we have a bot token, we can construct a real URL
                # 1. Get the file path first
                file_info_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
                try:
                    file_info = requests.get(file_info_url).json()
                    if file_info.get("ok") and "result" in file_info:
                        file_path = file_info["result"]["file_path"]
                        # 2. Construct the download URL
                        photo_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                        
                        # 3. Analyze the image
                        analysis = self._analyze_image(photo_url)
                        results.append(analysis)
                    else:
                        logger.error(f"Failed to get file info: {file_info}")
                except Exception as e:
                    logger.error(f"Error getting file info: {str(e)}")
            else:
                # If we don't have a bot token, we'll use a dummy URL for demonstration
                # In a real implementation, this would be replaced with actual file processing
                sender = message.get('from', {}).get('username', 'Unknown')
                logger.info(f"No bot token available, using dummy URL for photo from {sender}")
                
                # Here, in a real implementation, we would use the actual image data
                # For now, just return a placeholder result
                results.append({
                    "error": "No bot token configured for photo download",
                    "note": "Configure a Telegram bot token to enable photo analysis",
                    "sender": sender
                })
        
        if results:
            return {
                "photo_analyses": results,
                "count": len(results)
            }
        
        return None
    
    def process_images(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """
        Process images from a list of messages and generate descriptions.
        
        This is the main method to call from outside the agent.
        
        Args:
            messages: List of Telegram message dictionaries
            
        Returns:
            String containing descriptions of images found, or None if no images
        """
        if not messages:
            return None
        
        # Filter for messages with photos
        photo_messages = [msg for msg in messages if 'photo' in msg and msg['photo']]
        
        if not photo_messages:
            return None
        
        logger.info(f"Processing {len(photo_messages)} messages with photos")
        
        if SDK_AVAILABLE:
            # Import RunContext here to avoid circular imports
            from src.sdk_imports import RunContext
            
            context = RunContext()
            result = self.agent.run(
                messages=[{"role": "user", "content": "Please analyze the photos in these messages and provide descriptions."}],
                context=context,
                tools=[
                    lambda: self.process_message(msg) for msg in photo_messages
                ]
            )
            
            if result.output and result.output.content:
                return result.output.content
            return "Images were detected but could not be analyzed."
        else:
            # Use direct processing when SDK isn't available
            try:
                # Call the process_message method directly
                processed_photos = [self.process_message(msg) for msg in photo_messages]
                
                if not processed_photos:
                    return "Images were detected but could not be analyzed."
                
                # Format the results
                descriptions = []
                for i, photo in enumerate(processed_photos):
                    if photo:
                        sender = photo.get("sender", "Unknown")
                        description = photo.get("description", "No description available")
                        caption = photo.get("caption", "")
                        
                        if caption:
                            descriptions.append(f"Image {i+1}: Shared by {sender} with caption '{caption}': {description}")
                        else:
                            descriptions.append(f"Image {i+1}: Shared by {sender}: {description}")
                    else:
                        descriptions.append(f"Image {i+1}: Analysis failed")
                
                return "Images in the conversation:\n" + "\n".join(descriptions)
            except Exception as e:
                logger.error(f"Error in process_images fallback: {e}")
                return f"Images were detected but processing failed: {str(e)}" 