"""
Telegram Forward Bot - Command Handlers
All bot command implementations
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserDeactivated, ChatWriteForbidden
from config import Config, BotState, SuccessMessages, ErrorMessages, StatusFormats
from database import db
from utils.logger import bot_logger
from utils.validators import (
    channel_validator,
    message_validator,
    command_validator,
    input_sanitizer,
    ValidationResult
)
from utils.helpers import (
    FormatHelper,
    RetryHandler,
    FloodProtector,
    progress_tracker
)

class CommandHandler:
    """Handle all bot commands"""
    
    def __init__(self, client: Client):
        self.client = client
        self.current_session: Optional[Dict[str, Any]] = None
        self.is_forwarding = False
        self.flood_protector = FloodProtector()
        self.retry_handler = RetryHandler(max_retries=Config.MAX_RETRIES)
    
    async def start_command(self, message: Message):
        """Handle /start command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/start")
        
        # Create welcome message
        welcome_text = f"""
🚀 **Telegram Forward Bot**

Welcome! This bot can forward ALL messages from one channel to another with industrial-strength reliability.

**Features:**
• Forward all message types (text, media, files up to 2GB)
• Real-time progress tracking
• Automatic error recovery
• Duplicate detection
• Flood protection

**To get started:**
1. Use /set_source to set the source channel
2. Use /set_target to set the destination channel
3. Use /from_id to set starting message ID
4. Use /start to begin forwarding

**Commands:**
• /status - Check current status
• /pause - Pause forwarding
• /resume - Resume forwarding
• /cancel - Cancel current operation

Bot is ready for deployment on Render's free tier with full functionality.
        """
        
        # Create inline keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 Commands", callback_data="help_commands"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("🚀 Quick Start", callback_data="quick_start")
            ]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
    
    async def set_source_command(self, message: Message):
        """Handle /set_source command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/set_source", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text(
                "❌ Please provide a channel ID or username.\n\n"
                "Usage: `/set_source @channel_username` or `/set_source -1001234567890`",
                parse_mode="markdown"
            )
            return
        
        channel_input = input_sanitizer.sanitize_channel_input(args[1])
        
        # Validate channel format
        is_valid, validation_msg = channel_validator.validate_channel_id(channel_input)
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        # Resolve channel
        channel_id, channel_title = await channel_validator.resolve_channel(
            self.client, channel_input
        )
        
        if not channel_id:
            await message.reply_text(ErrorMessages.INVALID_CHANNEL)
            return
        
        # Check access
        has_access, access_msg = await channel_validator.check_channel_access(
            self.client, channel_id, require_admin=False
        )
        
        if not has_access:
            await message.reply_text(f"❌ {access_msg}")
            return
        
        # Save setting
        await db.set_setting("source_channel", str(channel_id))
        await db.set_setting("source_channel_name", channel_title or "Unknown")
        
        await message.reply_text(
            f"✅ Source channel set successfully!\n\n"
            f"📢 **Channel:** {channel_title or channel_input}\n"
            f"🆔 **ID:** `{channel_id}`",
            parse_mode="markdown"
        )
    
    async def set_target_command(self, message: Message):
        """Handle /set_target command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/set_target", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text(
                "❌ Please provide a channel ID or username.\n\n"
                "Usage: `/set_target @channel_username` or `/set_target -1001234567890`",
                parse_mode="markdown"
            )
            return
        
        channel_input = input_sanitizer.sanitize_channel_input(args[1])
        
        # Validate channel format
        is_valid, validation_msg = channel_validator.validate_channel_id(channel_input)
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        # Resolve channel
        channel_id, channel_title = await channel_validator.resolve_channel(
            self.client, channel_input
        )
        
        if not channel_id:
            await message.reply_text(ErrorMessages.INVALID_CHANNEL)
            return
        
        # Check admin access (required for target)
        has_access, access_msg = await channel_validator.check_channel_access(
            self.client, channel_id, require_admin=True
        )
        
        if not has_access:
            await message.reply_text(f"❌ {access_msg}")
            return
        
        # Save setting
        await db.set_setting("target_channel", str(channel_id))
        await db.set_setting("target_channel_name", channel_title or "Unknown")
        
        await message.reply_text(
            f"✅ Target channel set successfully!\n\n"
            f"📢 **Channel:** {channel_title or channel_input}\n"
            f"🆔 **ID:** `{channel_id}`",
            parse_mode="markdown"
        )
    
    async def from_id_command(self, message: Message):
        """Handle /from_id command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/from_id", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text(
                "❌ Please provide a message ID.\n\n"
                "Usage: `/from_id 12345`",
                parse_mode="markdown"
            )
            return
        
        is_valid, msg_id, validation_msg = message_validator.validate_message_id(args[1])
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        await db.set_setting("start_message_id", str(msg_id))
        await message.reply_text(
            f"✅ Starting message ID set to `{msg_id}`\n\n"
            f"Bot will forward all messages from ID {msg_id} onwards.",
            parse_mode="markdown"
        )
    
    async def to_id_command(self, message: Message):
        """Handle /to_id command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/to_id", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text(
                "❌ Please provide a message ID.\n\n"
                "Usage: `/to_id 12345`",
                parse_mode="markdown"
            )
            return
        
        is_valid, msg_id, validation_msg = message_validator.validate_message_id(args[1])
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        await db.set_setting("end_message_id", str(msg_id))
        await message.reply_text(
            f"✅ Ending message ID set to `{msg_id}`\n\n"
            f"Bot will forward messages up to ID {msg_id}.",
            parse_mode="markdown"
        )
    
    async def range_command(self, message: Message):
        """Handle /range command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/range", message.text)
        
        args = message.text.split()
        if len(args) < 3:
            await message.reply_text(
                "❌ Please provide start and end message IDs.\n\n"
                "Usage: `/range 100 200`",
                parse_mode="markdown"
            )
            return
        
        is_valid, range_tuple, validation_msg = message_validator.validate_range(args[1], args[2])
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        start_id, end_id = range_tuple
        
        await db.set_setting("start_message_id", str(start_id))
        await db.set_setting("end_message_id", str(end_id))
        
        message_count = end_id - start_id + 1
        await message.reply_text(
            f"✅ Message range set!\n\n"
            f"📊 **Range:** `{start_id}` to `{end_id}`\n"
            f"📈 **Total messages:** {message_count}",
            parse_mode="markdown"
        )
    
    async def delay_command(self, message: Message):
        """Handle /delay command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/delay", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            current_delay = await db.get_setting("delay", str(Config.DELAY_BETWEEN_MESSAGES))
            await message.reply_text(
                f"📊 Current delay: `{current_delay}s`\n\n"
                f"Usage: `/delay 1.5` (0.1 to 60 seconds)",
                parse_mode="markdown"
            )
            return
        
        is_valid, delay, validation_msg = command_validator.validate_delay(args[1])
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        await db.set_setting("delay", str(delay))
        await message.reply_text(
            f"✅ Delay set to `{delay}s`\n\n"
            f"Bot will wait {delay} seconds between forwarding messages.",
            parse_mode="markdown"
        )
    
    async def speed_command(self, message: Message):
        """Handle /speed command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/speed", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text(
                "❌ Please specify speed mode.\n\n"
                "Usage: `/speed fast|normal|safe`\n\n"
                "• **fast**: 0.5s delay (risky)\n"
                "• **normal**: 1s delay (recommended)\n"
                "• **safe**: 2-3s delay (very safe)"
            )
            return
        
        is_valid, mode, validation_msg = command_validator.validate_speed_mode(args[1])
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        # Map speed modes to delays
        speed_delays = {
            "fast": 0.5,
            "normal": 1.0,
            "safe": 2.5
        }
        
        delay = speed_delays[mode]
        await db.set_setting("delay", str(delay))
        await db.set_setting("speed_mode", mode)
        
        await message.reply_text(
            f"✅ Speed mode set to `{mode}`\n\n"
            f"⚡ **Delay:** {delay}s between messages",
            parse_mode="markdown"
        )
    
    async def retry_command(self, message: Message):
        """Handle /retry command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/retry", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            current_retry = await db.get_setting("max_retries", str(Config.MAX_RETRIES))
            await message.reply_text(
                f"📊 Current retry count: `{current_retry}`\n\n"
                f"Usage: `/retry 5` (0 to 10 retries)"
            )
            return
        
        is_valid, count, validation_msg = command_validator.validate_retry_count(args[1])
        if not is_valid:
            await message.reply_text(f"❌ {validation_msg}")
            return
        
        await db.set_setting("max_retries", str(count))
        await message.reply_text(
            f"✅ Retry count set to `{count}`\n\n"
            f"Bot will attempt {count} retries for failed messages.",
            parse_mode="markdown"
        )
    
    async def flood_protect_command(self, message: Message):
        """Handle /flood_protect command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/flood_protect", message.text)
        
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            current = await db.get_setting("flood_protect", str(Config.FLOOD_PROTECT))
            await message.reply_text(
                f"📊 Flood protection: `{current}`\n\n"
                f"Usage: `/flood_protect on|off`"
            )
            return
        
        mode = args[1].lower()
        if mode not in ["on", "off"]:
            await message.reply_text("❌ Invalid option. Use `on` or `off`.")
            return
        
        enabled = mode == "on"
        await db.set_setting("flood_protect", str(enabled))
        
        status = "enabled" if enabled else "disabled"
        await message.reply_text(f"✅ Flood protection {status}!")
    
    async def pause_command(self, message: Message):
        """Handle /pause command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/pause")
        
        if not self.is_forwarding:
            await message.reply_text("❌ No forwarding operation is currently running.")
            return
        
        self.is_forwarding = False
        
        # Update session status
        if self.current_session:
            await db.update_progress(
                self.current_session["id"],
                self.current_session["last_message_id"],
                {
                    "successful": self.current_session.get("successful_count", 0),
                    "failed": self.current_session.get("failed_count", 0),
                    "duplicate": self.current_session.get("duplicate_count", 0),
                    "deleted": self.current_session.get("deleted_count", 0),
                    "skipped": self.current_session.get("skipped_count", 0),
                    "filtered": self.current_session.get("filtered_count", 0)
                },
                status=BotState.PAUSED
            )
        
        await message.reply_text(SuccessMessages.PAUSED)
    
    async def resume_command(self, message: Message):
        """Handle /resume command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/resume")
        
        # Check if there's a paused session
        active_session = await db.get_active_session()
        if not active_session:
            await message.reply_text("❌ No paused forwarding session found.")
            return
        
        # Resume forwarding
        await message.reply_text(SuccessMessages.RESUMED)
        
        # Start forwarding from saved position
        asyncio.create_task(self._resume_forwarding(active_session))
    
    async def cancel_command(self, message: Message):
        """Handle /cancel command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/cancel")
        
        if not self.is_forwarding and not self.current_session:
            await message.reply_text("❌ No operation to cancel.")
            return
        
        # Stop forwarding
        self.is_forwarding = False
        
        # Save progress
        if self.current_session:
            await db.update_progress(
                self.current_session["id"],
                self.current_session["last_message_id"],
                {
                    "successful": self.current_session.get("successful_count", 0),
                    "failed": self.current_session.get("failed_count", 0),
                    "duplicate": self.current_session.get("duplicate_count", 0),
                    "deleted": self.current_session.get("deleted_count", 0),
                    "skipped": self.current_session.get("skipped_count", 0),
                    "filtered": self.current_session.get("filtered_count", 0)
                },
                status="cancelled"
            )
        
        self.current_session = None
        await message.reply_text(SuccessMessages.CANCELLED)
    
    async def reset_command(self, message: Message):
        """Handle /reset command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/reset")
        
        # Double confirmation
        args = message.text.split()
        if len(args) < 2 or args[1] != "confirm":
            await message.reply_text(
                "⚠️ **WARNING: This will reset ALL bot data!**\n\n"
                "This action cannot be undone.\n\n"
                "To confirm, type: `/reset confirm`",
                parse_mode="markdown"
            )
            return
        
        # Reset all data
        await db.reset_all()
        
        # Reset state
        self.is_forwarding = False
        self.current_session = None
        
        await message.reply_text("✅ All data has been reset!")
    
    async def status_command(self, message: Message):
        """Handle /status command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/status")
        
        # Get current settings
        source_channel = await db.get_setting("source_channel", "Not set")
        target_channel = await db.get_setting("target_channel", "Not set")
        source_name = await db.get_setting("source_channel_name", "Unknown")
        target_name = await db.get_setting("target_channel_name", "Unknown")
        start_id = await db.get_setting("start_message_id", "Not set")
        end_id = await db.get_setting("end_message_id", "Not set")
        delay = await db.get_setting("delay", str(Config.DELAY_BETWEEN_MESSAGES))
        speed_mode = await db.get_setting("speed_mode", "normal")
        
        # Get active session
        active_session = await db.get_active_session()
        
        # Get statistics
        stats = await db.get_statistics()
        
        # Format status message
        status_text = f"""
📊 **BOT STATUS**
━━━━━━━━━━━━━━━━━━━━

🔧 **Configuration:**
📤 Source: {source_name} (`{source_channel}`)
📥 Target: {target_name} (`{target_channel}`)
📍 Start ID: `{start_id}`
📍 End ID: `{end_id}`
⏱ Delay: `{delay}s` ({speed_mode} mode)

📈 **Statistics:**
📊 Total forwarded: {stats['total_messages_forwarded']:,}
❌ Total errors: {stats['total_errors']:,}
🔄 Total sessions: {stats['total_sessions']:,}
⚡ Recent sessions: {stats['recent_sessions']:,}

🔄 **Current Session:**
        """
        
        if active_session:
            session_info = f"""
🆔 Session ID: `{active_session['id']}`
📍 Last message: `{active_session['last_message_id']}`
✅ Successful: {active_session['successful_count']:,}
❌ Failed: {active_session['failed_count']:,}
♻️ Duplicates: {active_session['duplicate_count']:,}
🟢 Status: `{active_session['status']}`
            """
            status_text += session_info
        else:
            status_text += "\n`No active session`\n"
        
        status_text += "\n💡 Use /help for command list"
        
        await message.reply_text(status_text, parse_mode="markdown")
    
    async def stats_command(self, message: Message):
        """Handle /stats command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/stats")
        
        stats = await db.get_statistics()
        
        # Calculate success rate
        total_attempts = stats['total_messages_forwarded'] + stats['total_errors']
        success_rate = (stats['total_messages_forwarded'] / total_attempts * 100) if total_attempts > 0 else 0
        
        uptime = datetime.now() - datetime.fromtimestamp(message.date)
        
        stats_text = f"""
📈 **BOT STATISTICS**
━━━━━━━━━━━━━━━━━━━━

📊 **Lifetime Stats:**
📤 Messages forwarded: {stats['total_messages_forwarded']:,}
❌ Total errors: {stats['total_errors']:,}
🔄 Total sessions: {stats['total_sessions']:,}
📈 Success rate: {success_rate:.1f}%

⏱ **Session Info:**
⚡ Avg success/session: {stats['average_success_rate']:.1f}
📅 Recent sessions: {stats['recent_sessions']:,}
💻 Uptime: {FormatHelper.format_duration(uptime.total_seconds())}

🎯 **Performance:**
⚡ Current speed: {progress_tracker.get_formatted_speed()} msgs/min
⏱ Total time: {progress_tracker.get_formatted_elapsed()}
        """
        
        await message.reply_text(stats_text, parse_mode="markdown")
    
    async def failed_command(self, message: Message):
        """Handle /failed command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/failed")
        
        # Get active session
        active_session = await db.get_active_session()
        if not active_session:
            await message.reply_text("❌ No active session found.")
            return
        
        # Get failed messages
        failed_messages = await db.get_failed_messages(active_session['id'], limit=20)
        
        if not failed_messages:
            await message.reply_text("✅ No failed messages found!")
            return
        
        # Format failed messages
        failed_text = f"""
❌ **FAILED MESSAGES**
━━━━━━━━━━━━━━━━━━━━

🆔 **Session:** `{active_session['id']}`
📊 **Total failed:** {len(failed_messages)}

**Recent failures:**
        """
        
        for fail in failed_messages[:10]:
            fail_info = f"""
📍 ID: `{fail['message_id']}`
📝 Error: {FormatHelper.truncate_text(fail['error_message'], 40)}
📦 Size: {FormatHelper.format_file_size(fail['file_size'] or 0) if fail['file_size'] else 'N/A'}
🔄 Retries: {fail['retry_count']}
⏱ Time: {fail['timestamp']}
            """
            failed_text += fail_info + "\n"
        
        await message.reply_text(failed_text, parse_mode="markdown")
    
    async def help_command(self, message: Message):
        """Handle /help command"""
        
        bot_logger.log_command_usage(message.from_user.id, "/help")
        
        help_text = """
🤖 **TELEGRAM FORWARD BOT - HELP**
━━━━━━━━━━━━━━━━━━━━

**📋 Core Commands:**
• `/start` - Initialize bot and show menu
• `/status` - Show current status and stats
• `/pause` - Pause current forwarding
• `/resume` - Resume from last position
• `/cancel` - Cancel current operation

**⚙️ Configuration:**
• `/set_source [id/@username]` - Set source channel
• `/set_target [id/@username]` - Set target channel
• `/from_id [message_id]` - Set start message ID
• `/to_id [message_id]` - Set end message ID
• `/range [start] [end]` - Set message range

**🎚 Speed & Safety:**
• `/delay [seconds]` - Set delay (0.1-60s)
• `/speed [fast|normal|safe]` - Set speed mode
• `/retry [count]` - Set retry attempts (0-10)
• `/flood_protect [on|off]` - Toggle flood protection

**📊 Monitoring:**
• `/stats` - Show bot statistics
• `/failed` - Show failed messages

**🔄 Session:**
• `/reset` - Reset all data (dangerous!)

**Examples:**
```
/set_source @my_source_channel
/set_target -1001234567890
/from_id 1
/speed normal
```
        """
        
        await message.reply_text(help_text, parse_mode="markdown")
    
    async def _resume_forwarding(self, session: Dict[str, Any]):
        """Resume forwarding from saved session"""
        
        bot_logger.log_session_recovered(session['id'], session['last_message_id'])
        
        # Update session status
        await db.update_progress(
            session['id'],
            session['last_message_id'],
            {},
            status=BotState.FORWARDING
        )
        
        # Start forwarding
        from handlers.forwarding import ForwardingHandler
        forwarding_handler = ForwardingHandler(self.client)
        
        await forwarding_handler.start_forwarding(
            source_channel=session['source_channel_id'],
            target_channel=session['target_channel_id'],
            start_message_id=session['last_message_id'],
            session_id=session['id']
        )

# Global command handler instance
command_handler = None

def setup_command_handlers(client: Client):
    """Setup all command handlers"""
    global command_handler
    command_handler = CommandHandler(client)
    
    # Register command handlers
    client.on_message(filters.command("start") & filters.private)(command_handler.start_command)
    client.on_message(filters.command("set_source") & filters.private)(command_handler.set_source_command)
    client.on_message(filters.command("set_target") & filters.private)(command_handler.set_target_command)
    client.on_message(filters.command("from_id") & filters.private)(command_handler.from_id_command)
    client.on_message(filters.command("to_id") & filters.private)(command_handler.to_id_command)
    client.on_message(filters.command("range") & filters.private)(command_handler.range_command)
    client.on_message(filters.command("delay") & filters.private)(command_handler.delay_command)
    client.on_message(filters.command("speed") & filters.private)(command_handler.speed_command)
    client.on_message(filters.command("retry") & filters.private)(command_handler.retry_command)
    client.on_message(filters.command("flood_protect") & filters.private)(command_handler.flood_protect_command)
    client.on_message(filters.command("pause") & filters.private)(command_handler.pause_command)
    client.on_message(filters.command("resume") & filters.private)(command_handler.resume_command)
    client.on_message(filters.command("cancel") & filters.private)(command_handler.cancel_command)
    client.on_message(filters.command("reset") & filters.private)(command_handler.reset_command)
    client.on_message(filters.command("status") & filters.private)(command_handler.status_command)
    client.on_message(filters.command("stats") & filters.private)(command_handler.stats_command)
    client.on_message(filters.command("failed") & filters.private)(command_handler.failed_command)
    client.on_message(filters.command("help") & filters.private)(command_handler.help_command)