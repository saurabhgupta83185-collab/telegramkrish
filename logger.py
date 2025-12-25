"""
Telegram Forward Bot - Logging Module
Advanced logging with rotation and structured output
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "message_id"):
            log_data["message_id"] = record.message_id
        if hasattr(record, "channel_id"):
            log_data["channel_id"] = record.channel_id
        if hasattr(record, "file_size"):
            log_data["file_size"] = record.file_size
        if hasattr(record, "content_type"):
            log_data["content_type"] = record.content_type
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration
        if hasattr(record, "error"):
            log_data["error"] = str(record.error)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console"""
        
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]
        
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)

def setup_logging(
    level: str = "INFO",
    log_file: str = "bot.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """Setup comprehensive logging"""
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler("errors.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Bot-specific logger
    bot_logger = logging.getLogger("telegram_forward_bot")
    bot_logger.setLevel(logging.DEBUG)
    
    # Suppress verbose logs from libraries
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    
    # Log setup completion
    bot_logger.info("Logging setup completed", extra={
        "log_level": level,
        "log_file": log_file,
        "max_file_size": max_file_size,
        "backup_count": backup_count
    })

class BotLogger:
    """Enhanced logger with bot-specific functionality"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _add_context(self, extra: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Add context to log extra data"""
        if extra is None:
            extra = {}
        extra.update(kwargs)
        return extra
    
    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Debug log with context"""
        self.logger.debug(msg, extra=self._add_context(extra, **kwargs))
    
    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Info log with context"""
        self.logger.info(msg, extra=self._add_context(extra, **kwargs))
    
    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Warning log with context"""
        self.logger.warning(msg, extra=self._add_context(extra, **kwargs))
    
    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Error log with context"""
        self.logger.error(msg, extra=self._add_context(extra, **kwargs))
    
    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Critical log with context"""
        self.logger.critical(msg, extra=self._add_context(extra, **kwargs))
    
    def exception(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Exception log with context"""
        self.logger.exception(msg, extra=self._add_context(extra, **kwargs))
    
    def log_forwarding_start(
        self,
        session_id: int,
        source_channel: str,
        target_channel: str,
        start_message_id: int
    ):
        """Log forwarding session start"""
        self.info(
            f"Forwarding session started",
            extra={
                "event_type": "forwarding_start",
                "session_id": session_id,
                "source_channel": source_channel,
                "target_channel": target_channel,
                "start_message_id": start_message_id
            }
        )
    
    def log_forwarding_progress(
        self,
        session_id: int,
        message_id: int,
        content_type: str,
        file_size: Optional[int] = None,
        duration: Optional[float] = None
    ):
        """Log forwarding progress"""
        self.debug(
            f"Forwarded message {message_id}",
            extra={
                "event_type": "forwarding_progress",
                "session_id": session_id,
                "message_id": message_id,
                "content_type": content_type,
                "file_size": file_size,
                "duration": duration
            }
        )
    
    def log_forwarding_error(
        self,
        session_id: int,
        message_id: int,
        error: Exception,
        content_type: Optional[str] = None,
        file_size: Optional[int] = None,
        retry_count: int = 0
    ):
        """Log forwarding error"""
        self.error(
            f"Failed to forward message {message_id}: {str(error)}",
            extra={
                "event_type": "forwarding_error",
                "session_id": session_id,
                "message_id": message_id,
                "content_type": content_type,
                "file_size": file_size,
                "retry_count": retry_count,
                "error": str(error)
            }
        )
    
    def log_command_usage(
        self,
        user_id: int,
        command: str,
        args: Optional[str] = None
    ):
        """Log command usage"""
        self.info(
            f"Command used: {command}",
            extra={
                "event_type": "command_usage",
                "user_id": user_id,
                "command": command,
                "args": args
            }
        )
    
    def log_session_recovered(self, session_id: int, last_message_id: int):
        """Log session recovery"""
        self.info(
            f"Session recovered",
            extra={
                "event_type": "session_recovery",
                "session_id": session_id,
                "last_message_id": last_message_id
            }
        )

# Global bot logger instance
bot_logger = BotLogger("telegram_forward_bot")