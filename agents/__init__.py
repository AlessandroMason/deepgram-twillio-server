"""
Agents package for Deepgram Voice Agent configurations
Contains constants and examples for different agent types
"""

from .constants import *
from .constants_generic import *

__all__ = [
    # Personal agent constants
    'INITIAL_PROMPT',
    'GREETING', 
    'USER_ID',
    'DIARY_DAYS',
    'DIARY_MAX_ENTRIES',
    'DIARY_MAX_CHARS',
    'FALLBACK_DIARY',
    'CONTACTS',
    'EMAIL_SERVICE_CONFIG',
    'EMAIL_TRIGGER_FORMAT',
    'UPDATED_INITIAL_PROMPT',
    
    # Generic agent constants
    'INITIAL_PROMPT_GENERIC',
    'GREETING_GENERIC',
    'DIARY_DAYS_GENERIC',
    'DIARY_MAX_ENTRIES_GENERIC',
    'DIARY_MAX_CHARS_GENERIC',
    'FALLBACK_DIARY_GENERIC',
    'CACHE_TTL'
]
