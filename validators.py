"""
Telegram Forward Bot - Validators
Input validation and sanitization utilities
"""

import re
from typing import Optional, Tuple, Union
from pyrogram import Client
from pyrogram.errors import (
    UsernameInvalid,
    UsernameNotOccupied,
    PeerIdInvalid,
    ChannelInvalid,
    ChatIdInvalid
)
from utils.logger import bot_logger

class ChannelValidator:
    """Validate channel inputs and permissions"""
    
    @staticmethod
    def validate_channel_id(channel_id: str) -> Tuple[bool, str]:
        """Validate channel ID format"""
        
        # Check if it's a numeric ID
        if channel_id.lstrip('-').isdigit():
            return True, "Valid numeric ID"
        
        # Check if it's a username
        if channel_id.startswith('@'):
            username = channel_id[1:]
            if len(username) < 5 or len(username) > 32:
                return False, "Username must be between 5 and 32 characters"
            if not username.replace('_', '').replace('.', '').isalnum():
                return False, "Username can only contain letters, numbers, underscores, and periods"
            return True, "Valid username"
        
        # Check if it's an invite link
        invite_pattern = r'(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me)/(?:joinchat/)?([a-zA-Z0-9_-]+)'
        if re.match(invite_pattern, channel_id):
            return True, "Valid invite link"
        
        return False, "Invalid channel ID format"
    
    @staticmethod
    async def resolve_channel(
        client: Client,
        channel_input: str
    ) -> Tuple[Optional[Union[str, int]], Optional[str]]:
        """Resolve channel input to ID and title"""
        
        try:
            # Handle different input types
            if channel_input.lstrip('-').isdigit():
                # Numeric ID
                channel_id = int(channel_input)
                try:
                    chat = await client.get_chat(channel_id)
                    return chat.id, chat.title
                except (PeerIdInvalid, ChatIdInvalid):
                    bot_logger.error(f"Cannot access chat with ID {channel_id}")
                    return None, None
            
            elif channel_input.startswith('@'):
                # Username
                username = channel_input
                try:
                    chat = await client.get_chat(username)
                    return chat.id, chat.title
                except (UsernameInvalid, UsernameNotOccupied):
                    bot_logger.error(f"Cannot access chat with username {username}")
                    return None, None
            
            elif '/' in channel_input:
                # Invite link
                try:
                    chat = await client.get_chat(channel_input)
                    return chat.id, chat.title
                except Exception as e:
                    bot_logger.error(f"Cannot access chat with invite link: {e}")
                    return None, None
            
            else:
                # Try as username without @
                try:
                    chat = await client.get_chat(f"@{channel_input}")
                    return chat.id, chat.title
                except Exception:
                    # Try as numeric ID
                    try:
                        chat_id = int(channel_input)
                        chat = await client.get_chat(chat_id)
                        return chat.id, chat.title
                    except Exception:
                        return None, None
        
        except Exception as e:
            bot_logger.error(f"Error resolving channel {channel_input}: {e}")
            return None, None
    
    @staticmethod
    async def check_channel_access(
        client: Client,
        channel_id: Union[str, int],
        require_admin: bool = False
    ) -> Tuple[bool, str]:
        """Check bot access to channel"""
        
        try:
            chat = await client.get_chat(channel_id)
            
            # Check if it's a channel
            if chat.type not in ["channel", "supergroup"]:
                return False, "The specified chat is not a channel"
            
            # Check permissions
            if require_admin:
                member = await client.get_chat_member(chat.id, "me")
                
                if chat.type == "channel":
                    # For channels, check if we're an admin
                    if not member.can_post_messages:
                        return False, "Bot needs posting permission in the destination channel"
                else:
                    # For supergroups, check admin rights
                    if not (member.can_send_messages and member.can_send_media_messages):
                        return False, "Bot needs send messages and media permissions"
            
            return True, "Access verified"
        
        except Exception as e:
            return False, f"Cannot access channel: {str(e)}"

class MessageValidator:
    """Validate message inputs"""
    
    @staticmethod
    def validate_message_id(message_id: str) -> Tuple[bool, Optional[int], str]:
        """Validate message ID"""
        
        try:
            msg_id = int(message_id)
            if msg_id <= 0:
                return False, None, "Message ID must be positive"
            return True, msg_id, "Valid message ID"
        except ValueError:
            return False, None, "Message ID must be a number"
    
    @staticmethod
    def validate_range(start_id: str, end_id: str) -> Tuple[bool, Optional[Tuple[int, int]], str]:
        """Validate message ID range"""
        
        valid_start, start, start_msg = MessageValidator.validate_message_id(start_id)
        valid_end, end, end_msg = MessageValidator.validate_message_id(end_id)
        
        if not valid_start:
            return False, None, f"Invalid start ID: {start_msg}"
        if not valid_end:
            return False, None, f"Invalid end ID: {end_msg}"
        
        if start > end:
            return False, None, "Start ID must be less than or equal to end ID"
        
        return True, (start, end), "Valid range"

class CommandValidator:
    """Validate command arguments"""
    
    @staticmethod
    def validate_delay(delay_str: str) -> Tuple[bool, Optional[float], str]:
        """Validate delay value"""
        
        try:
            delay = float(delay_str)
            if delay < 0.1:
                return False, None, "Delay must be at least 0.1 seconds"
            if delay > 60:
                return False, None, "Delay cannot exceed 60 seconds"
            return True, delay, "Valid delay"
        except ValueError:
            return False, None, "Delay must be a number"
    
    @staticmethod
    def validate_retry_count(count_str: str) -> Tuple[bool, Optional[int], str]:
        """Validate retry count"""
        
        try:
            count = int(count_str)
            if count < 0:
                return False, None, "Retry count cannot be negative"
            if count > 10:
                return False, None, "Retry count cannot exceed 10"
            return True, count, "Valid retry count"
        except ValueError:
            return False, None, "Retry count must be an integer"
    
    @staticmethod
    def validate_speed_mode(mode: str) -> Tuple[bool, Optional[str], str]:
        """Validate speed mode"""
        
        valid_modes = ["fast", "normal", "safe"]
        mode_lower = mode.lower()
        
        if mode_lower in valid_modes:
            return True, mode_lower, "Valid speed mode"
        else:
            return False, None, f"Invalid speed mode. Must be one of: {', '.join(valid_modes)}"

class InputSanitizer:
    """Sanitize user inputs"""
    
    @staticmethod
    def sanitize_channel_input(channel_input: str) -> str:
        """Sanitize channel input"""
        
        # Remove extra whitespace
        channel_input = channel_input.strip()
        
        # Remove URL prefixes if present
        channel_input = re.sub(r'^https?://(?:www\.)?(?:t\.me|telegram\.me)/', '', channel_input)
        
        # Ensure @ prefix for usernames
        if not channel_input.startswith('@') and not channel_input.lstrip('-').isdigit():
            channel_input = f'@{channel_input}'
        
        return channel_input
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 100) -> str:
        """Sanitize text input"""
        
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Trim whitespace
        text = text.strip()
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length - 3] + '...'
        
        return text
    
    @staticmethod
    def sanitize_command_args(args: str) -> List[str]:
        """Sanitize command arguments"""
        
        if not args.strip():
            return []
        
        # Split by whitespace, respecting quotes
        import shlex
        try:
            return shlex.split(args)
        except ValueError:
            # Fallback to simple split
            return args.split()

class ValidationResult:
    """Validation result container"""
    
    def __init__(self, is_valid: bool, value: Optional[Any] = None, error: Optional[str] = None):
        self.is_valid = is_valid
        self.value = value
        self.error = error
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        if self.is_valid:
            return f"Valid: {self.value}"
        else:
            return f"Invalid: {self.error}"

# Global validators
channel_validator = ChannelValidator()
message_validator = MessageValidator()
command_validator = CommandValidator()
input_sanitizer = InputSanitizer()