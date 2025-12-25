"""
Telegram Forward Bot - Status Handler
Real-time status updates and progress tracking
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message
from config import Config, StatusFormats, BotState
from utils.helpers import ProgressTracker, FormatHelper
from utils.logger import bot_logger

class StatusHandler:
    """Handle real-time status updates"""
    
    def __init__(self, client: Client):
        self.client = client
        self.status_messages: Dict[int, Message] = {}
        self.update_tasks: Dict[int, asyncio.Task] = {}
        self.progress_tracker = ProgressTracker()
    
    async def create_status_message(
        self,
        chat_id: int,
        session_id: int,
        source_name: str,
        target_name: str
    ) -> Message:
        """Create initial status message"""
        
        status_text = StatusFormats.DECORATIVE.format(
            total_messages=0,
            success_count=0,
            duplicate_count=0,
            deleted_count=0,
            skipped_count=0,
            filtered_count=0,
            status="Initializing...",
            percentage=0.0,
            completion_status="Starting..."
        )
        
        message = await self.client.send_message(chat_id, status_text)
        self.status_messages[session_id] = message
        
        return message
    
    async def update_status(
        self,
        session_id: int,
        counters: Dict[str, int],
        current_message_id: int,
        total_messages: int,
        status: str = BotState.FORWARDING
    ):
        """Update status message"""
        
        if session_id not in self.status_messages:
            return
        
        try:
            # Calculate progress
            progress = (current_message_id / total_messages) * 100 if total_messages > 0 else 0
            
            # Format decorative status
            decorative_text = StatusFormats.DECORATIVE.format(
                total_messages=total_messages,
                success_count=counters.get("successful", 0),
                duplicate_count=counters.get("duplicate", 0),
                deleted_count=counters.get("deleted", 0),
                skipped_count=counters.get("skipped", 0),
                filtered_count=counters.get("filtered", 0),
                status=status,
                percentage=progress,
                completion_status=self._get_completion_status(progress)
            )
            
            # Update status message
            message = self.status_messages[session_id]
            await message.edit_text(decorative_text)
            
        except Exception as e:
            bot_logger.warning(
                f"Failed to update status message: {e}",
                extra={"session_id": session_id, "error": str(e)}
            )
    
    async def update_technical_status(
        self,
        session_id: int,
        source_name: str,
        target_name: str,
        counters: Dict[str, int],
        current_message_id: int
    ):
        """Update technical status format"""
        
        if session_id not in self.status_messages:
            return
        
        try:
            # Calculate metrics
            speed = self.progress_tracker.get_speed()
            elapsed = self.progress_tracker.get_elapsed_time()
            
            # Format technical status
            technical_text = StatusFormats.TECHNICAL.format(
                source_name=source_name,
                target_name=target_name,
                success=counters.get("successful", 0),
                failed=counters.get("failed", 0),
                duplicate=counters.get("duplicate", 0),
                messages_per_minute=f"{speed:.1f}",
                elapsed_time=FormatHelper.format_duration(elapsed.total_seconds()),
                current_msg_id=current_message_id,
                status="RUNNING"
            )
            
            # Update status message
            message = self.status_messages[session_id]
            await message.edit_text(technical_text)
            
        except Exception as e:
            bot_logger.warning(
                f"Failed to update technical status: {e}",
                extra={"session_id": session_id, "error": str(e)}
            )
    
    async def show_failure_notification(
        self,
        session_id: int,
        message_id: int,
        content_type: str,
        file_size: Optional[int],
        error_message: str,
        attempt_number: int,
        last_success_id: int
    ):
        """Show detailed failure notification"""
        
        try:
            # Get target channel
            target_channel = await self.client.get_chat(int(self.client.me.id))
            
            failure_text = StatusFormats.FAILURE.format(
                msg_id=message_id,
                type=content_type,
                size=FormatHelper.format_file_size(file_size or 0),
                error_message=error_message,
                attempt_number=attempt_number,
                last_success_id=last_success_id
            )
            
            await self.client.send_message(target_channel.id, failure_text)
            
        except Exception as e:
            bot_logger.error(
                f"Failed to send failure notification: {e}",
                extra={"session_id": session_id, "error": str(e)}
            )
    
    def _get_completion_status(self, progress: float) -> str:
        """Get completion status based on progress"""
        
        if progress == 0:
            return "Starting..."
        elif progress < 25:
            return "Just started 🚀"
        elif progress < 50:
            return "Making progress 📈"
        elif progress < 75:
            return "Halfway there ⏳"
        elif progress < 90:
            return "Almost done 🎯"
        elif progress < 100:
            return "Final stretch 🏁"
        else:
            return "Completed! 🎉"
    
    async def start_periodic_updates(
        self,
        session_id: int,
        chat_id: int,
        update_interval: int = Config.STATUS_UPDATE_INTERVAL
    ):
        """Start periodic status updates"""
        
        async def update_loop():
            while session_id in self.status_messages:
                try:
                    # Get current session data
                    from database import db
                    session = await db.get_session(session_id)
                    if not session:
                        break
                    
                    # Update both status formats
                    await self.update_status(
                        session_id,
                        {
                            "successful": session.get("successful_count", 0),
                            "duplicate": session.get("duplicate_count", 0),
                            "deleted": session.get("deleted_count", 0),
                            "skipped": session.get("skipped_count", 0),
                            "filtered": session.get("filtered_count", 0)
                        },
                        session.get("last_message_id", 0),
                        session.get("total_messages", 1000),
                        session.get("status", BotState.FORWARDING)
                    )
                    
                except Exception as e:
                    bot_logger.warning(
                        f"Periodic update failed: {e}",
                        extra={"session_id": session_id, "error": str(e)}
                    )
                
                await asyncio.sleep(update_interval)
        
        # Start update task
        task = asyncio.create_task(update_loop())
        self.update_tasks[session_id] = task
    
    async def stop_updates(self, session_id: int):
        """Stop status updates for session"""
        
        # Cancel update task
        if session_id in self.update_tasks:
            self.update_tasks[session_id].cancel()
            del self.update_tasks[session_id]
        
        # Remove status message reference
        if session_id in self.status_messages:
            del self.status_messages[session_id]
    
    async def create_progress_bar(
        self,
        chat_id: int,
        current: int,
        total: int,
        length: int = 20
    ) -> Message:
        """Create a visual progress bar"""
        
        progress = current / total if total > 0 else 0
        filled = int(length * progress)
        bar = "█" * filled + "░" * (length - filled)
        
        progress_text = f"""
📊 **PROGRESS**
━━━━━━━━━━━━━━━━━━━━

[{bar}] {progress:.1%}

{current}/{total} messages processed
        """
        
        return await self.client.send_message(chat_id, progress_text)
    
    async def update_progress_bar(
        self,
        message: Message,
        current: int,
        total: int,
        length: int = 20
    ):
        """Update existing progress bar"""
        
        try:
            progress = current / total if total > 0 else 0
            filled = int(length * progress)
            bar = "█" * filled + "░" * (length - filled)
            
            progress_text = f"""
📊 **PROGRESS**
━━━━━━━━━━━━━━━━━━━━

[{bar}] {progress:.1%}

{current}/{total} messages processed
            """
            
            await message.edit_text(progress_text)
            
        except Exception as e:
            bot_logger.warning(
                f"Failed to update progress bar: {e}",
                extra={"error": str(e)}
            )
    
    async def show_eta(self, chat_id: int, remaining: int) -> Message:
        """Show estimated time of arrival"""
        
        eta = self.progress_tracker.get_eta(remaining)
        
        if eta:
            eta_text = f"""
⏱ **ESTIMATED TIME**
━━━━━━━━━━━━━━━━━━━━

📊 Remaining: {remaining:,} messages
⏰ ETA: {FormatHelper.format_duration(eta.total_seconds())}
⚡ Speed: {self.progress_tracker.get_formatted_speed()} msgs/min
            """
        else:
            eta_text = f"""
⏱ **ESTIMATED TIME**
━━━━━━━━━━━━━━━━━━━━

📊 Remaining: {remaining:,} messages
⏰ ETA: Calculating...
⚡ Speed: {self.progress_tracker.get_formatted_speed()} msgs/min
            """
        
        return await self.client.send_message(chat_id, eta_text)
    
    async def show_speed_stats(self, chat_id: int, session_id: int):
        """Show detailed speed statistics"""
        
        try:
            # Get session data
            from database import db
            session = await db.get_session(session_id)
            if not session:
                await self.client.send_message(chat_id, "❌ Session not found.")
                return
            
            # Calculate statistics
            total_processed = (
                session.get("successful_count", 0) +
                session.get("failed_count", 0) +
                session.get("duplicate_count", 0) +
                session.get("skipped_count", 0)
            )
            
            elapsed_time = self.progress_tracker.get_elapsed_time()
            avg_speed = total_processed / elapsed_time.total_seconds() * 60 if elapsed_time.total_seconds() > 0 else 0
            
            # Get speed history
            recent_speeds = self.progress_tracker.speed_history[-5:]
            
            speed_text = f"""
⚡ **SPEED STATISTICS**
━━━━━━━━━━━━━━━━━━━━

📊 **Current Session:**
🆔 Session ID: `{session_id}`
📈 Total processed: {total_processed:,}
⏱ Elapsed time: {FormatHelper.format_duration(elapsed_time.total_seconds())}

📈 **Speed Metrics:**
⚡ Current: {self.progress_tracker.get_formatted_speed()} msgs/min
📊 Average: {avg_speed:.1f} msgs/min

📊 **Recent Speeds:**
            """
            
            for i, speed in enumerate(recent_speeds[-5:], 1):
                speed_text += f"{i}. {speed:.1f} msgs/min\n"
            
            await self.client.send_message(chat_id, speed_text)
            
        except Exception as e:
            bot_logger.error(
                f"Failed to show speed stats: {e}",
                extra={"session_id": session_id, "error": str(e)}
            )
    
    async def show_completion_summary(
        self,
        chat_id: int,
        session_id: int,
        counters: Dict[str, int],
        start_time: datetime,
        end_time: datetime
    ):
        """Show completion summary"""
        
        try:
            duration = end_time - start_time
            total_messages = sum(counters.values())
            success_rate = (counters.get("successful", 0) / total_messages * 100) if total_messages > 0 else 0
            
            summary_text = f"""
🎉 **FORWARDING COMPLETED**
━━━━━━━━━━━━━━━━━━━━

🆔 **Session:** `{session_id}`
⏱ **Duration:** {FormatHelper.format_duration(duration.total_seconds())}
📊 **Success Rate:** {success_rate:.1f}%

📈 **Results:**
✅ Successful: {counters.get("successful", 0):,}
❌ Failed: {counters.get("failed", 0):,}
♻️ Duplicates: {counters.get("duplicate", 0):,}
🗑 Deleted: {counters.get("deleted", 0):,}
🪆 Skipped: {counters.get("skipped", 0):,}
🔁 Filtered: {counters.get("filtered", 0):,}

⚡ **Performance:**
Average speed: {total_messages / duration.total_seconds() * 60:.1f} msgs/min
Total processed: {total_messages:,}
            """
            
            await self.client.send_message(chat_id, summary_text)
            
        except Exception as e:
            bot_logger.error(
                f"Failed to show completion summary: {e}",
                extra={"session_id": session_id, "error": str(e)}
            )

# Global status handler instance
status_handler = None

def setup_status_handler(client: Client):
    """Setup status handler"""
    global status_handler
    status_handler = StatusHandler(client)