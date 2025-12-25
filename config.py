"""
Telegram Forward Bot - Configuration Module
Industrial-strength configuration management for production deployment
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration with validation and defaults"""
    
    # Core Telegram API credentials
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_database.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
    
    # Performance settings
    DELAY_BETWEEN_MESSAGES: float = float(os.getenv("DELAY_BETWEEN_MESSAGES", "1.0"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    FLOOD_PROTECT: bool = os.getenv("FLOOD_PROTECT", "true").lower() == "true"
    
    # Status update intervals
    STATUS_UPDATE_INTERVAL: int = int(os.getenv("STATUS_UPDATE_INTERVAL", "5"))
    PROGRESS_SAVE_INTERVAL: int = int(os.getenv("PROGRESS_SAVE_INTERVAL", "10"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File handling
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "2048"))  # 2GB default
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1048576"))  # 1MB chunks
    
    # Session management
    SESSION_SAVE_INTERVAL: int = int(os.getenv("SESSION_SAVE_INTERVAL", "10"))
    AUTO_RECONNECT: bool = os.getenv("AUTO_RECONNECT", "true").lower() == "true"
    
    # Status message settings
    STATUS_MESSAGE_ID: Optional[int] = None
    STATUS_CHAT_ID: Optional[int] = None
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.API_ID or cls.API_ID == 0:
            raise ValueError("API_ID is required and must be a valid integer")
        if not cls.API_HASH:
            raise ValueError("API_HASH is required")
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        return True
    
    @classmethod
    def setup_logging(cls) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=cls.LOG_FORMAT,
            handlers=[
                logging.FileHandler("bot.log"),
                logging.StreamHandler()
            ]
        )

# Bot states
class BotState:
    """Bot operational states"""
    IDLE = "idle"
    FORWARDING = "forwarding"
    PAUSED = "paused"
    FAILED = "failed"
    RECOVERING = "recovering"

# Message content types
class ContentType:
    """Supported message content types"""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    STICKER = "sticker"
    ANIMATION = "animation"
    POLL = "poll"
    CONTACT = "contact"
    LOCATION = "location"
    VENUE = "venue"
    DICE = "dice"
    GAME = "game"
    INVOICE = "invoice"
    SUCCESSFUL_PAYMENT = "successful_payment"
    PASSPORT_DATA = "passport_data"
    PROXIMITY_ALERT_TRIGGERED = "proximity_alert_triggered"
    VOICE_CHAT_SCHEDULED = "voice_chat_scheduled"
    VOICE_CHAT_STARTED = "voice_chat_started"
    VOICE_CHAT_ENDED = "voice_chat_ended"
    VOICE_CHAT_PARTICIPANTS_INVITED = "voice_chat_participants_invited"
    WEB_PAGE = "web_page"
    POLL_ANSWER = "poll_answer"
    CHAT_JOIN_REQUEST = "chat_join_request"

# Error messages
class ErrorMessages:
    """Standardized error messages"""
    INVALID_CHANNEL = "❌ Invalid channel ID or username. Please check and try again."
    NO_ACCESS = "❌ Bot doesn't have access to the specified channel."
    NOT_ADMIN = "❌ Bot must be an administrator in the destination channel."
    FORWARDING_RESTRICTED = "❌ Forwarding is restricted in the source channel."
    FLOOD_WAIT = "⚠️ Flood wait detected. Bot will pause and resume automatically."
    FILE_TOO_BIG = "❌ File size exceeds Telegram limits."
    SESSION_EXPIRED = "❌ Session expired. Please login again."
    UNKNOWN_ERROR = "❌ An unknown error occurred. Check logs for details."

# Success messages
class SuccessMessages:
    """Standardized success messages"""
    STARTED = "✅ Forwarding started successfully!"
    PAUSED = "⏸️ Forwarding paused. Use /resume to continue."
    RESUMED = "▶️ Forwarding resumed from last position."
    CANCELLED = "❌ Forwarding cancelled. Progress saved."
    COMPLETED = "🎉 Forwarding completed successfully!"
    SETTINGS_SAVED = "✅ Settings saved successfully!"
    CHANNEL_SET = "✅ Channel set successfully!"

# Status formats
class StatusFormats:
    """Status message formats"""
    
    DECORATIVE = """╔════❰ ғᴏʀᴡᴀʀᴅ sᴛᴀᴛᴜs  ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼🕵 ғᴇᴛᴄʜᴇᴅ Msɢ : {total_messages}
║┃
║┣⪼✅ sᴜᴄᴄᴇғᴜʟʟʏ Fᴡᴅ : {success_count}
║┃
║┣⪼👥 ᴅᴜᴘʟɪᴄᴀᴛᴇ Msɢ : {duplicate_count}
║┃
║┣⪼🗑 ᴅᴇʟᴇᴛᴇᴅ Msɢ : {deleted_count}
║┃
║┣⪼🪆 Sᴋɪᴘᴘᴇᴅ Msɢ : {skipped_count}
║┃
║┣⪼🔁 Fɪʟᴛᴇʀᴇᴅ Msɢ : {filtered_count}
║┃
║┣⪼📊 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: {status}
║┃
║┣⪼𖨠 Pᴇʀᴄᴇɴᴛᴀɢᴇ: {percentage} %
║╰━━━━━━━━━━━━━━━➣ 
╚════❰ {completion_status} ❱══❍⊱❁۪۪"""

    TECHNICAL = """🚀 MIGRATION LIVE STATUS
━━━━━━━━━━━━━━━━━━━━
📤 Source: {source_name}
📥 Target: {target_name}
━━━━━━━━━━━━━━━━━━━━
📊 Progress Details:
✅ Success: {success}
❌ Failed: {failed}
♻️ Duplicate: {duplicate}
━━━━━━━━━━━━━━━━━━━━
⚡ Speed: {messages_per_minute} msgs/min
⏱ Time Elapsed: {elapsed_time}
📂 Currently Processing: ID {current_msg_id}
━━━━━━━━━━━━━━━━━━━━
🟢 Bot Status: {status}"""

    FAILURE = """⚠️ FORWARDING FAILED
━━━━━━━━━━━━━━━━━━━━
🆔 Message ID: {msg_id}
📝 Content Type: {type}
📦 File Size: {size} MB
❌ Error: {error_message}
🔄 Retry Attempt: {attempt_number}
━━━━━━━━━━━━━━━━━━━━
📍 Last Success ID: {last_success_id}
💾 Progress Saved

Use /retry to attempt again
Use /skip to skip this message
Use /resume to continue from next"""

# Progress bar
class ProgressBar:
    """Progress bar utilities"""
    
    @staticmethod
    def create(progress: float, length: int = 20) -> str:
        """Create a progress bar"""
        filled = int(length * progress)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {progress:.1%}"
    
    @staticmethod
    def create_detailed(current: int, total: int, length: int = 20) -> str:
        """Create a detailed progress bar"""
        progress = current / total if total > 0 else 0
        filled = int(length * progress)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {current}/{total} ({progress:.1%})"