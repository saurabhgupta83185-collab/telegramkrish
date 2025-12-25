"""
Telegram Forward Bot - Helper Utilities
Common utility functions for bot operations
"""

import asyncio
import hashlib
import time
from typing import Optional, Dict, Any, Union, List
from datetime import datetime, timedelta
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserDeactivated, ChatWriteForbidden
from config import Config, ContentType
from utils.logger import bot_logger

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 30, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[float] = []
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if rate limit exceeded"""
        async with self._lock:
            now = time.time()
            
            # Remove old calls outside time window
            self.calls = [call for call in self.calls if now - call < self.time_window]
            
            # Check if we need to wait
            if len(self.calls) >= self.max_calls:
                oldest_call = min(self.calls)
                wait_time = self.time_window - (now - oldest_call) + 1
                if wait_time > 0:
                    bot_logger.warning(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                    await asyncio.sleep(wait_time)
            
            # Record this call
            self.calls.append(now)

class ProgressTracker:
    """Track and calculate progress metrics"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_update = self.start_time
        self.messages_processed = 0
        self.last_message_count = 0
        self.speed_history: List[float] = []
        self.max_history = 10
    
    def update(self, messages_processed: int):
        """Update progress"""
        now = datetime.now()
        self.messages_processed = messages_processed
        
        # Calculate speed
        time_diff = (now - self.last_update).total_seconds()
        if time_diff > 0:
            speed = (messages_processed - self.last_message_count) / time_diff * 60
            self.speed_history.append(speed)
            if len(self.speed_history) > self.max_history:
                self.speed_history.pop(0)
        
        self.last_update = now
        self.last_message_count = messages_processed
    
    def get_speed(self) -> float:
        """Get current speed in messages per minute"""
        if not self.speed_history:
            return 0.0
        return sum(self.speed_history) / len(self.speed_history)
    
    def get_eta(self, remaining_messages: int) -> Optional[timedelta]:
        """Calculate estimated time of arrival"""
        speed = self.get_speed()
        if speed <= 0:
            return None
        
        minutes_remaining = remaining_messages / speed
        return timedelta(minutes=minutes_remaining)
    
    def get_elapsed_time(self) -> timedelta:
        """Get elapsed time"""
        return datetime.now() - self.start_time
    
    def get_formatted_eta(self, remaining_messages: int) -> str:
        """Get formatted ETA string"""
        eta = self.get_eta(remaining_messages)
        if not eta:
            return "Calculating..."
        
        if eta.total_seconds() < 60:
            return f"{int(eta.total_seconds())}s"
        elif eta.total_seconds() < 3600:
            return f"{int(eta.total_seconds() / 60)}m"
        else:
            hours = int(eta.total_seconds() / 3600)
            minutes = int((eta.total_seconds() % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def get_formatted_speed(self) -> str:
        """Get formatted speed string"""
        speed = self.get_speed()
        if speed < 1:
            return f"{speed:.2f}"
        elif speed < 10:
            return f"{speed:.1f}"
        else:
            return f"{int(speed)}"
    
    def get_formatted_elapsed(self) -> str:
        """Get formatted elapsed time"""
        elapsed = self.get_elapsed_time()
        if elapsed.total_seconds() < 60:
            return f"{int(elapsed.total_seconds())}s"
        elif elapsed.total_seconds() < 3600:
            return f"{int(elapsed.total_seconds() / 60)}m"
        else:
            hours = int(elapsed.total_seconds() / 3600)
            minutes = int((elapsed.total_seconds() % 3600) / 60)
            return f"{hours}h {minutes}m"

class MessageContentExtractor:
    """Extract content information from messages"""
    
    @staticmethod
    def get_content_type(message: Message) -> str:
        """Get message content type"""
        
        if message.text:
            return ContentType.TEXT
        elif message.photo:
            return ContentType.PHOTO
        elif message.video:
            return ContentType.VIDEO
        elif message.document:
            return ContentType.DOCUMENT
        elif message.audio:
            return ContentType.AUDIO
        elif message.voice:
            return ContentType.VOICE
        elif message.sticker:
            return ContentType.STICKER
        elif message.animation:
            return ContentType.ANIMATION
        elif message.poll:
            return ContentType.POLL
        elif message.contact:
            return ContentType.CONTACT
        elif message.location:
            return ContentType.LOCATION
        elif message.venue:
            return ContentType.VENUE
        elif message.dice:
            return ContentType.DICE
        elif message.game:
            return ContentType.GAME
        elif message.invoice:
            return ContentType.INVOICE
        elif message.successful_payment:
            return ContentType.SUCCESSFUL_PAYMENT
        elif message.passport_data:
            return ContentType.PASSPORT_DATA
        elif message.proximity_alert_triggered:
            return ContentType.PROXIMITY_ALERT_TRIGGERED
        elif message.voice_chat_scheduled:
            return ContentType.VOICE_CHAT_SCHEDULED
        elif message.voice_chat_started:
            return ContentType.VOICE_CHAT_STARTED
        elif message.voice_chat_ended:
            return ContentType.VOICE_CHAT_ENDED
        elif message.voice_chat_participants_invited:
            return ContentType.VOICE_CHAT_PARTICIPANTS_INVITED
        elif message.web_page:
            return ContentType.WEB_PAGE
        else:
            return "unknown"
    
    @staticmethod
    def get_file_size(message: Message) -> Optional[int]:
        """Get file size from message"""
        
        if message.photo:
            return message.photo.file_size
        elif message.video:
            return message.video.file_size
        elif message.document:
            return message.document.file_size
        elif message.audio:
            return message.audio.file_size
        elif message.voice:
            return message.voice.file_size
        elif message.sticker:
            return message.sticker.file_size
        elif message.animation:
            return message.animation.file_size
        elif message.video_note:
            return message.video_note.file_size
        else:
            return None
    
    @staticmethod
    def get_file_unique_id(message: Message) -> Optional[str]:
        """Get file unique ID from message"""
        
        if message.photo:
            return message.photo.file_unique_id
        elif message.video:
            return message.video.file_unique_id
        elif message.document:
            return message.document.file_unique_id
        elif message.audio:
            return message.audio.file_unique_id
        elif message.voice:
            return message.voice.file_unique_id
        elif message.sticker:
            return message.sticker.file_unique_id
        elif message.animation:
            return message.animation.file_unique_id
        elif message.video_note:
            return message.video_note.file_unique_id
        else:
            return None
    
    @staticmethod
    def generate_content_hash(message: Message) -> str:
        """Generate hash for text content"""
        
        content_parts = []
        
        if message.text:
            content_parts.append(message.text)
        if message.caption:
            content_parts.append(message.caption)
        
        content = "|".join(content_parts)
        return hashlib.md5(content.encode()).hexdigest()

class RetryHandler:
    """Handle retries with exponential backoff"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    async def execute_with_retry(
        self,
        func,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Execute function with retry logic"""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except FloodWait as e:
                # Handle Telegram flood wait
                wait_time = min(e.value, self.max_delay)
                bot_logger.warning(
                    f"FloodWait encountered, waiting {wait_time}s",
                    extra={"attempt": attempt + 1, "max_retries": self.max_retries}
                )
                await asyncio.sleep(wait_time)
                last_exception = e
            except (UserDeactivated, ChatWriteForbidden) as e:
                # Don't retry these errors
                bot_logger.error(
                    f"Non-retryable error: {type(e).__name__}",
                    extra={"error": str(e)}
                )
                raise
            except Exception as e:
                # Retry other exceptions with backoff
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.backoff_factor ** attempt),
                        self.max_delay
                    )
                    bot_logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}, retrying in {delay:.1f}s",
                        extra={"attempt": attempt + 1, "max_retries": self.max_retries, "error": str(e)}
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                else:
                    bot_logger.error(
                        f"All {self.max_retries + 1} attempts failed",
                        extra={"attempt": attempt + 1, "max_retries": self.max_retries, "error": str(e)}
                    )
        
        if last_exception:
            raise last_exception
        return None

class FloodProtector:
    """Flood protection with adaptive delays"""
    
    def __init__(self, initial_delay: float = 1.0):
        self.current_delay = initial_delay
        self.min_delay = 0.5
        self.max_delay = 10.0
        self.last_flood_time: Optional[datetime] = None
        self.flood_count = 0
    
    async def wait(self, base_delay: Optional[float] = None):
        """Wait with flood protection"""
        
        delay = base_delay or self.current_delay
        
        # Check if we recently had a flood
        if self.last_flood_time:
            time_since_flood = (datetime.now() - self.last_flood_time).total_seconds()
            if time_since_flood < 60:  # Within last minute
                delay = min(delay * 2, self.max_delay)
            else:
                # Gradually reduce delay
                self.current_delay = max(self.current_delay * 0.9, self.min_delay)
        
        await asyncio.sleep(delay)
    
    def on_flood(self):
        """Handle flood detection"""
        self.last_flood_time = datetime.now()
        self.flood_count += 1
        self.current_delay = min(self.current_delay * 1.5, self.max_delay)
        bot_logger.warning(
            f"Flood detected, increasing delay to {self.current_delay:.1f}s",
            extra={"flood_count": self.flood_count, "new_delay": self.current_delay}
        )
    
    def reset(self):
        """Reset flood protection"""
        self.current_delay = self.min_delay
        self.last_flood_time = None
        self.flood_count = 0

class FormatHelper:
    """Helper for formatting data"""
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        if i == 0:
            return f"{int(size)} {size_names[i]}"
        elif size < 10:
            return f"{size:.2f} {size_names[i]}"
        elif size < 100:
            return f"{size:.1f} {size_names[i]}"
        else:
            return f"{int(size)} {size_names[i]}"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human readable format"""
        
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def format_percentage(current: int, total: int) -> str:
        """Format percentage"""
        
        if total == 0:
            return "0.0%"
        
        percentage = (current / total) * 100
        return f"{percentage:.1f}%"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """Truncate text to maximum length"""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown characters"""
        
        escape_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
        
        for char in escape_chars:
            text = text.replace(char, f"\\{char}")
        
        return text

# Global instances
rate_limiter = RateLimiter()
progress_tracker = ProgressTracker()