"""
Assistants Module

This module provides assistants for the Para-Phrase Generator, including:
- Delegation Assistant: Routes tasks to specialized assistants
- Profile Assistant: Manages user profiles for personalized summaries
- Various specialized assistants for content processing
"""

# Import core assistants
from .delegation import DelegationAssistant
from .profile_assistant import ProfileAssistant
from .manager import AssistantsManager

# Import core utilities
from .linking import (
    create_message_mapping, 
    find_reference_candidates, 
    add_links_to_summary,
    generate_telegram_link
)

# Import tools
from .tools import (
    WebSearchTool,
    TwitterSummaryTool,
    FootballInfoTool,
    ImageAnalysisTool,
    TelegramMessageLinkTool,
    function_tool
)

# For convenience, expose the main classes at the module level
__all__ = [
    'DelegationAssistant',
    'ProfileAssistant',
    'AssistantsManager',
    'create_message_mapping',
    'find_reference_candidates',
    'add_links_to_summary',
    'generate_telegram_link',
    'WebSearchTool',
    'TwitterSummaryTool',
    'FootballInfoTool',
    'ImageAnalysisTool',
    'TelegramMessageLinkTool',
    'function_tool'
] 