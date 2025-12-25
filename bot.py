"""
Telegram Forward Bot - Main Application
Industrial-strength Telegram message forwarding bot

Features:
- Forward ALL message types including large files up to 2GB
- Real-time progress tracking with dual status formats
- Automatic error recovery and retry mechanisms
- Flood protection with adaptive delays
- Duplicate detection and filtering
- Session persistence and crash recovery
- Comprehensive logging and monitoring
- Deployable on Render's free tier

Author: Expert Python Developer with 100+ years experience
Version: 1.0.0
"""

import asyncio
import os
import sys
import signal
from typing import Optional
from pyrogram import Client, filters
from pyrogram.errors import UserDeactivated, ChatWriteForbidden, FloodWait
from pyrogram.types import Message
from config import Config, BotState
from database import db

from handlers.commands import setup_command_handlers
from handlers.forwarding import setup_forwarding_handler
from handlers.status import setup_status_handler

# Version information
__version__ = "1.0.0"
__author__ = "Expert Python Developer"
__description__ = "Industrial-strength Telegram message forwarding bot"

class TelegramForwardBot:
    """Main bot application class"""
    
    def __init__(self):
        # Validate configuration
        Config.validate()
        
        # Setup logging
        setup_logging(Config.LOG_LEVEL)
        bot_logger.info("Telegram Forward Bot starting up", extra={"version": __version__})
        
        # Initialize Pyrogram client
        self.client = Client(
            "telegram_forward_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workdir="./sessions",
            plugins=dict(root="handlers")
        )
        
        # Setup handlers
        self._setup_handlers()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        # Bot state
        self.is_running = False
        self.shutdown_event = asyncio.Event()
    
    def _setup_handlers(self):
        """Setup all bot handlers"""
        
        # Setup command handlers
        setup_command_handlers(self.client)
        
        # Setup forwarding handler
        setup_forwarding_handler(self.client)
        
        # Setup status handler
        setup_status_handler(self.client)
        
        bot_logger.info("All handlers configured successfully")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        
        def signal_handler(signum, frame):
            bot_logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.graceful_shutdown())
        
        # Handle SIGTERM (for container orchestration)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Handle SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def start(self):
        """Start the bot"""
        
        try:
            bot_logger.info("Starting Telegram Forward Bot...")
            
            # Connect to database
            await db.connect()
            await db.initialize()
            bot_logger.info("Database initialized successfully")
            
            # Start the client
            await self.client.start()
            bot_logger.info("Pyrogram client started successfully")
            
            # Set bot state
            self.is_running = True
            
            # Check for active sessions and recover if needed
            await self._check_and_recover_sessions()
            
            # Log startup completion
            bot_info = await self.client.get_me()
            bot_logger.info(
                "Bot started successfully",
                extra={
                    "bot_username": bot_info.username,
                    "bot_id": bot_info.id,
                    "is_bot": bot_info.is_bot
                }
            )
            
            # Send startup notification if target channel is configured
            await self._send_startup_notification()
            
            # Keep the bot running
            await self.shutdown_event.wait()
            
        except Exception as e:
            bot_logger.critical(
                f"Failed to start bot: {e}",
                extra={"error": str(e)}
            )
            raise
    
    async def graceful_shutdown(self):
        """Gracefully shutdown the bot"""
        
        bot_logger.info("Initiating graceful shutdown...")
        
        try:
            # Stop forwarding operations
            from handlers.forwarding import forwarding_handler
            if forwarding_handler:
                forwarding_handler.stop_forwarding()
            
            # Save all active sessions
            await self._save_active_sessions()
            
            # Stop the client
            if self.client.is_connected:
                await self.client.stop()
                bot_logger.info("Pyrogram client stopped")
            
            # Close database connection
            await db.close()
            
            # Set shutdown event
            self.shutdown_event.set()
            
            bot_logger.info("Bot shutdown completed gracefully")
            
        except Exception as e:
            bot_logger.error(
                f"Error during graceful shutdown: {e}",
                extra={"error": str(e)}
            )
    
    async def _check_and_recover_sessions(self):
        """Check for active sessions and recover if needed"""
        
        try:
            # Get active session
            active_session = await db.get_active_session()
            
            if active_session:
                bot_logger.info(
                    "Found active session, attempting recovery",
                    extra={
                        "session_id": active_session["id"],
                        "last_message_id": active_session["last_message_id"],
                        "status": active_session["status"]
                    }
                )
                
                # Send recovery notification
                await self._send_recovery_notification(active_session)
                
        except Exception as e:
            bot_logger.error(
                f"Failed to check for active sessions: {e}",
                extra={"error": str(e)}
            )
    
    async def _save_active_sessions(self):
        """Save all active sessions before shutdown"""
        
        try:
            active_session = await db.get_active_session()
            if active_session:
                # Update session status to indicate it was interrupted
                await db.update_progress(
                    active_session["id"],
                    active_session["last_message_id"],
                    {
                        "successful": active_session.get("successful_count", 0),
                        "failed": active_session.get("failed_count", 0),
                        "duplicate": active_session.get("duplicate_count", 0),
                        "deleted": active_session.get("deleted_count", 0),
                        "skipped": active_session.get("skipped_count", 0),
                        "filtered": active_session.get("filtered_count", 0)
                    },
                    status="interrupted"
                )
                
                bot_logger.info(
                    "Active session saved",
                    extra={"session_id": active_session["id"]}
                )
                
        except Exception as e:
            bot_logger.error(
                f"Failed to save active sessions: {e}",
                extra={"error": str(e)}
            )
    
    async def _send_startup_notification(self):
        """Send startup notification to configured channel"""
        
        try:
            target_channel = await db.get_setting("target_channel")
            if target_channel:
                startup_text = f"""
🚀 **BOT STARTED SUCCESSFULLY**
━━━━━━━━━━━━━━━━━━━━

✅ **Status:** Online and ready
📅 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 **Version:** {__version__}

**Configuration:**
• Database: {Config.DATABASE_PATH}
• Log Level: {Config.LOG_LEVEL}
• Flood Protection: {Config.FLOOD_PROTECT}
• Max Retries: {Config.MAX_RETRIES}

**Commands available:**
• /start - Initialize bot
• /status - Check status
• /help - Show help

Bot is ready to forward messages!
                """
                
                await self.client.send_message(int(target_channel), startup_text)
                bot_logger.info("Startup notification sent")
                
        except Exception as e:
            bot_logger.warning(
                f"Failed to send startup notification: {e}",
                extra={"error": str(e)}
            )
    
    async def _send_recovery_notification(self, session: dict):
        """Send session recovery notification"""
        
        try:
            target_channel = await db.get_setting("target_channel")
            if target_channel:
                recovery_text = f"""
🔄 **SESSION RECOVERY DETECTED**
━━━━━━━━━━━━━━━━━━━━

🆔 **Session ID:** `{session['id']}`
📍 **Last Message:** `{session['last_message_id']}`
🟢 **Previous Status:** `{session['status']}`
⏱ **Last Active:** {session.get('updated_at', 'Unknown')}

**To resume forwarding:**
1. Use `/resume` to continue from last position
2. Use `/status` to check current state
3. Use `/from_id [new_id]` to change start position

💾 All progress has been preserved.
                """
                
                await self.client.send_message(int(target_channel), recovery_text)
                bot_logger.info("Recovery notification sent")
                
        except Exception as e:
            bot_logger.error(
                f"Failed to send recovery notification: {e}",
                extra={"error": str(e)}
            )

async def main():
    """Main entry point"""
    
    try:
        # Create bot instance
        bot = TelegramForwardBot()
        
        # Start the bot
        await bot.start()
        
    except KeyboardInterrupt:
        bot_logger.info("Received KeyboardInterrupt, shutting down...")
    except Exception as e:
        bot_logger.critical(
            f"Fatal error in main: {e}",
            extra={"error": str(e)}
        )
        sys.exit(1)

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: This bot requires Python 3.8 or higher")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(main())
