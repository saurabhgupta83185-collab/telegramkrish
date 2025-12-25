"""
Telegram Forward Bot - Forwarding Handler
Advanced message forwarding with error handling and recovery
"""

import asyncio
import os
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import (
    FloodWait,
    UserDeactivated,
    ChatWriteForbidden,
    MessageIdInvalid,
    MessageDeleteForbidden,
    SlowmodeWait,
    PeerIdInvalid,
    ChannelInvalid,
    ChatIdInvalid,
    MessageTooLong,
    MediaCaptionTooLong,
    ExternalUrlInvalid,
    WebpageCurlFailed,
    WebpageMediaEmpty,
    TimeoutError
)
from config import Config, BotState, ContentType, ErrorMessages, StatusFormats
from database import db
from utils.logger import bot_logger
from utils.helpers import (
    MessageContentExtractor,
    RetryHandler,
    FloodProtector,
    ProgressTracker,
    FormatHelper,
    progress_tracker
)
from utils.validators import channel_validator

class ForwardingHandler:
    """Handle message forwarding with advanced features"""
    
    def __init__(self, client: Client):
        self.client = client
        self.is_forwarding = False
        self.current_session: Optional[Dict[str, Any]] = None
        self.status_message: Optional[Message] = None
        self.status_update_task: Optional[asyncio.Task] = None
        self.flood_protector = FloodProtector()
        self.retry_handler = RetryHandler(max_retries=Config.MAX_RETRIES)
        self.counters: Dict[str, int] = {
            "successful": 0,
            "failed": 0,
            "duplicate": 0,
            "deleted": 0,
            "skipped": 0,
            "filtered": 0
        }
    
    async def start_forwarding(
        self,
        source_channel: str,
        target_channel: str,
        start_message_id: int = 1,
        end_message_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> bool:
        """Start forwarding messages from source to target channel"""
        
        try:
            self.is_forwarding = True
            
            # Create or resume session
            if session_id:
                self.current_session = await db.get_session(session_id)
                if not self.current_session:
                    bot_logger.error(f"Session {session_id} not found")
                    return False
            else:
                session_id = await db.create_forwarding_session(
                    source_channel,
                    target_channel,
                    start_message_id
                )
                self.current_session = await db.get_session(session_id)
            
            bot_logger.log_forwarding_start(
                session_id,
                source_channel,
                target_channel,
                start_message_id
            )
            
            # Get channel information
            source_chat = await self.client.get_chat(source_channel)
            target_chat = await self.client.get_chat(target_channel)
            
            # Initialize progress tracker
            progress_tracker.start_time = datetime.now()
            progress_tracker.messages_processed = 0
            
            # Initialize status message
            await self._initialize_status_message(source_chat.title, target_chat.title)
            
            # Start status update task
            self.status_update_task = asyncio.create_task(
                self._update_status_periodically(source_chat.title, target_chat.title)
            )
            
            # Get total message count estimate
            total_messages = await self._estimate_total_messages(source_channel, end_message_id)
            
            # Start forwarding
            current_message_id = start_message_id
            consecutive_failures = 0
            max_consecutive_failures = 5
            
            while self.is_forwarding and current_message_id <= (end_message_id or float('inf')):
                try:
                    # Get message
                    message = await self._get_message_with_retry(
                        source_channel,
                        current_message_id
                    )
                    
                    if not message:
                        # Message might be deleted or inaccessible
                        self.counters["deleted"] += 1
                        consecutive_failures += 1
                        
                        if consecutive_failures >= max_consecutive_failures:
                            bot_logger.warning(
                                f"Too many consecutive failures, stopping",
                                extra={"session_id": session_id, "message_id": current_message_id}
                            )
                            break
                        
                        current_message_id += 1
                        continue
                    
                    # Reset consecutive failures
                    consecutive_failures = 0
                    
                    # Forward message
                    success = await self._forward_message_with_strategies(
                        message,
                        target_channel
                    )
                    
                    if success:
                        self.counters["successful"] += 1
                        
                        # Track the message
                        await self._track_message(message, target_channel)
                        
                        # Update progress
                        progress_tracker.update(current_message_id)
                        
                        # Update session
                        await self._update_session_progress(current_message_id)
                        
                        # Apply delay
                        await self._apply_delay()
                    else:
                        self.counters["failed"] += 1
                        
                        # Log failure and continue
                        await self._handle_forwarding_failure(
                            message,
                            "All forwarding strategies failed"
                        )
                    
                    current_message_id += 1
                    
                except FloodWait as e:
                    # Handle flood wait
                    self.flood_protector.on_flood()
                    await asyncio.sleep(e.value)
                    
                except Exception as e:
                    bot_logger.error(
                        f"Unexpected error in forwarding loop: {e}",
                        extra={"session_id": session_id, "message_id": current_message_id, "error": str(e)}
                    )
                    self.counters["failed"] += 1
                    current_message_id += 1
            
            # Forwarding completed
            await self._finalize_forwarding()
            
            return True
            
        except Exception as e:
            bot_logger.error(
                f"Critical error in forwarding: {e}",
                extra={"error": str(e)}
            )
            await self._handle_critical_error(e)
            return False
    
    async def _get_message_with_retry(
        self,
        chat_id: Union[str, int],
        message_id: int
    ) -> Optional[Message]:
        """Get message with retry logic"""
        
        async def _get_message():
            return await self.client.get_messages(chat_id, message_id)
        
        try:
            return await self.retry_handler.execute_with_retry(_get_message)
        except Exception as e:
            bot_logger.log_forwarding_error(
                self.current_session["id"],
                message_id,
                e,
                content_type="unknown"
            )
            return None
    
    async def _forward_message_with_strategies(
        self,
        message: Message,
        target_channel: str
    ) -> bool:
        """Forward message using multiple strategies"""
        
        content_type = MessageContentExtractor.get_content_type(message)
        file_size = MessageContentExtractor.get_file_size(message)
        file_unique_id = MessageContentExtractor.get_file_unique_id(message)
        
        # Strategy 1: Direct forward (fastest)
        try:
            forwarded_msg = await message.forward(target_channel)
            if forwarded_msg:
                bot_logger.log_forwarding_progress(
                    self.current_session["id"],
                    message.id,
                    content_type,
                    file_size
                )
                return True
        except Exception as e:
            bot_logger.debug(
                f"Direct forward failed for message {message.id}: {e}",
                extra={"strategy": "direct", "message_id": message.id}
            )
        
        # Strategy 2: Download and re-upload
        try:
            forwarded_msg = await self._download_and_reupload(message, target_channel)
            if forwarded_msg:
                bot_logger.log_forwarding_progress(
                    self.current_session["id"],
                    message.id,
                    content_type,
                    file_size
                )
                return True
        except Exception as e:
            bot_logger.debug(
                f"Download-reupload failed for message {message.id}: {e}",
                extra={"strategy": "reupload", "message_id": message.id}
            )
        
        # Strategy 3: Chunk-based for large files
        if file_size and file_size > 50 * 1024 * 1024:  # > 50MB
            try:
                forwarded_msg = await self._forward_large_file(message, target_channel)
                if forwarded_msg:
                    bot_logger.log_forwarding_progress(
                        self.current_session["id"],
                        message.id,
                        content_type,
                        file_size
                    )
                    return True
            except Exception as e:
                bot_logger.debug(
                    f"Large file forwarding failed for message {message.id}: {e}",
                    extra={"strategy": "large_file", "message_id": message.id}
                )
        
        # All strategies failed
        await self._handle_forwarding_failure(message, "All forwarding strategies failed")
        return False
    
    async def _download_and_reupload(
        self,
        message: Message,
        target_channel: str
    ) -> Optional[Message]:
        """Download message content and re-upload"""
        
        try:
            # Download file to temporary location
            temp_file = f"/tmp/forward_{message.id}_{datetime.now().timestamp()}"
            
            if message.photo:
                file_path = await message.download(temp_file)
                return await self.client.send_photo(
                    target_channel,
                    file_path,
                    caption=message.caption,
                    parse_mode=message.parse_mode
                )
            elif message.video:
                file_path = await message.download(temp_file)
                return await self.client.send_video(
                    target_channel,
                    file_path,
                    caption=message.caption,
                    parse_mode=message.parse_mode,
                    duration=message.video.duration,
                    width=message.video.width,
                    height=message.video.height,
                    thumb=message.video.thumbs[0] if message.video.thumbs else None
                )
            elif message.document:
                file_path = await message.download(temp_file)
                return await self.client.send_document(
                    target_channel,
                    file_path,
                    caption=message.caption,
                    parse_mode=message.parse_mode,
                    thumb=message.document.thumbs[0] if message.document.thumbs else None
                )
            elif message.audio:
                file_path = await message.download(temp_file)
                return await self.client.send_audio(
                    target_channel,
                    file_path,
                    caption=message.caption,
                    parse_mode=message.parse_mode,
                    duration=message.audio.duration,
                    performer=message.audio.performer,
                    title=message.audio.title
                )
            elif message.voice:
                file_path = await message.download(temp_file)
                return await self.client.send_voice(
                    target_channel,
                    file_path,
                    caption=message.caption,
                    parse_mode=message.parse_mode,
                    duration=message.voice.duration
                )
            elif message.video_note:
                file_path = await message.download(temp_file)
                return await self.client.send_video_note(
                    target_channel,
                    file_path,
                    duration=message.video_note.duration,
                    length=message.video_note.length
                )
            elif message.sticker:
                file_path = await message.download(temp_file)
                return await self.client.send_sticker(target_channel, file_path)
            elif message.animation:
                file_path = await message.download(temp_file)
                return await self.client.send_animation(
                    target_channel,
                    file_path,
                    caption=message.caption,
                    parse_mode=message.parse_mode
                )
            elif message.text:
                return await self.client.send_message(
                    target_channel,
                    message.text,
                    parse_mode=message.parse_mode,
                    entities=message.entities,
                    disable_web_page_preview=not message.web_page
                )
            elif message.poll:
                return await self.client.send_poll(
                    target_channel,
                    question=message.poll.question,
                    options=[option.text for option in message.poll.options],
                    is_anonymous=message.poll.is_anonymous,
                    type=message.poll.type,
                    allows_multiple_answers=message.poll.allows_multiple_answers,
                    correct_option_id=message.poll.correct_option_id,
                    explanation=message.poll.explanation,
                    explanation_entities=message.poll.explanation_entities
                )
            elif message.contact:
                return await self.client.send_contact(
                    target_channel,
                    phone_number=message.contact.phone_number,
                    first_name=message.contact.first_name,
                    last_name=message.contact.last_name,
                    vcard=message.contact.vcard
                )
            elif message.location:
                return await self.client.send_location(
                    target_channel,
                    latitude=message.location.latitude,
                    longitude=message.location.longitude,
                    horizontal_accuracy=message.location.horizontal_accuracy,
                    live_period=message.location.live_period,
                    heading=message.location.heading,
                    proximity_alert_radius=message.location.proximity_alert_radius
                )
            elif message.venue:
                return await self.client.send_venue(
                    target_channel,
                    latitude=message.venue.location.latitude,
                    longitude=message.venue.location.longitude,
                    title=message.venue.title,
                    address=message.venue.address,
                    foursquare_id=message.venue.foursquare_id,
                    foursquare_type=message.venue.foursquare_type
                )
            elif message.dice:
                return await self.client.send_dice(
                    target_channel,
                    emoji=message.dice.emoji
                )
            
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            bot_logger.error(
                f"Download-reupload failed: {e}",
                extra={"message_id": message.id, "error": str(e)}
            )
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return None
    
    async def _forward_large_file(
        self,
        message: Message,
        target_channel: str
    ) -> Optional[Message]:
        """Forward large files with chunk-based streaming"""
        
        try:
            # For very large files, we need to handle them specially
            # This is a simplified implementation - in production, you'd want
            # more sophisticated chunking and progress tracking
            
            file_size = MessageContentExtractor.get_file_size(message)
            
            if file_size > 2 * 1024 * 1024 * 1024:  # > 2GB
                bot_logger.warning(
                    f"File too large for Telegram limits: {file_size} bytes",
                    extra={"message_id": message.id, "file_size": file_size}
                )
                return None
            
            # Use download and re-upload for large files
            # Pyrogram handles large files efficiently
            return await self._download_and_reupload(message, target_channel)
            
        except Exception as e:
            bot_logger.error(
                f"Large file forwarding failed: {e}",
                extra={"message_id": message.id, "error": str(e)}
            )
            return None
    
    async def _track_message(
        self,
        message: Message,
        target_channel: str
    ) -> None:
        """Track forwarded message for duplicate detection"""
        
        try:
            file_unique_id = MessageContentExtractor.get_file_unique_id(message)
            content_hash = MessageContentExtractor.generate_content_hash(message)
            
            await db.track_message(
                self.current_session["id"],
                message.id,
                message.id,  # We'll update this with actual forwarded message ID
                file_unique_id,
                content_hash
            )
        except Exception as e:
            bot_logger.warning(
                f"Failed to track message: {e}",
                extra={"message_id": message.id, "error": str(e)}
            )
    
    async def _apply_delay(self):
        """Apply configured delay between messages"""
        
        delay = float(await db.get_setting("delay", str(Config.DELAY_BETWEEN_MESSAGES)))
        await self.flood_protector.wait(delay)
    
    async def _update_session_progress(self, current_message_id: int):
        """Update session progress in database"""
        
        try:
            await db.update_progress(
                self.current_session["id"],
                current_message_id,
                self.counters,
                status=BotState.FORWARDING
            )
        except Exception as e:
            bot_logger.error(
                f"Failed to update session progress: {e}",
                extra={"session_id": self.current_session["id"], "error": str(e)}
            )
    
    async def _estimate_total_messages(
        self,
        source_channel: str,
        end_message_id: Optional[int]
    ) -> int:
        """Estimate total number of messages"""
        
        try:
            # Get the latest message ID in the channel
            messages = await self.client.get_chat_history(source_channel, limit=1)
            if messages:
                latest_id = messages[0].id
                return end_message_id or latest_id
        except Exception as e:
            bot_logger.warning(
                f"Could not estimate total messages: {e}",
                extra={"channel": source_channel, "error": str(e)}
            )
        
        return end_message_id or 1000  # Default estimate
    
    async def _initialize_status_message(self, source_name: str, target_name: str):
        """Initialize status message"""
        
        try:
            # Get target channel for status updates (could be a log channel)
            target_channel = await db.get_setting("target_channel")
            if target_channel:
                self.status_message = await self.client.send_message(
                    int(target_channel),
                    "Initializing forwarding status..."
                )
        except Exception as e:
            bot_logger.warning(
                f"Could not initialize status message: {e}",
                extra={"error": str(e)}
            )
    
    async def _update_status_periodically(self, source_name: str, target_name: str):
        """Update status message periodically"""
        
        while self.is_forwarding:
            try:
                if self.status_message:
                    # Calculate progress
                    total = self.current_session.get("total_messages", 1000)
                    current = self.current_session.get("last_message_id", 0)
                    progress = current / total if total > 0 else 0
                    
                    # Format status message
                    status_text = StatusFormats.TECHNICAL.format(
                        source_name=source_name,
                        target_name=target_name,
                        success=self.counters["successful"],
                        failed=self.counters["failed"],
                        duplicate=self.counters["duplicate"],
                        messages_per_minute=progress_tracker.get_formatted_speed(),
                        elapsed_time=progress_tracker.get_formatted_elapsed(),
                        current_msg_id=current,
                        status="RUNNING" if self.is_forwarding else "STOPPED"
                    )
                    
                    # Update status message
                    await self.status_message.edit_text(status_text)
                
                # Wait before next update
                await asyncio.sleep(Config.STATUS_UPDATE_INTERVAL)
                
            except Exception as e:
                bot_logger.warning(
                    f"Failed to update status: {e}",
                    extra={"error": str(e)}
                )
                await asyncio.sleep(Config.STATUS_UPDATE_INTERVAL)
    
    async def _handle_forwarding_failure(
        self,
        message: Message,
        error_message: str
    ) -> None:
        """Handle forwarding failure"""
        
        content_type = MessageContentExtractor.get_content_type(message)
        file_size = MessageContentExtractor.get_file_size(message)
        
        # Log to database
        await db.add_failed_message(
            self.current_session["id"],
            message.id,
            error_message,
            file_size,
            content_type
        )
        
        bot_logger.log_forwarding_error(
            self.current_session["id"],
            message.id,
            Exception(error_message),
            content_type,
            file_size
        )
    
    async def _handle_critical_error(self, error: Exception):
        """Handle critical errors"""
        
        # Update session status
        if self.current_session:
            await db.update_progress(
                self.current_session["id"],
                self.current_session.get("last_message_id", 0),
                self.counters,
                status=BotState.FAILED
            )
        
        # Send error notification
        try:
            target_channel = await db.get_setting("target_channel")
            if target_channel:
                error_text = f"""
⚠️ **CRITICAL ERROR**
━━━━━━━━━━━━━━━━━━━━

❌ Error: {str(error)}
🆔 Session: {self.current_session['id'] if self.current_session else 'None'}
⏱ Time: {datetime.now()}

💾 Progress has been saved.
Use /resume to continue after fixing the issue.
                """
                
                await self.client.send_message(int(target_channel), error_text)
        except Exception as e:
            bot_logger.error(
                f"Failed to send error notification: {e}",
                extra={"error": str(e)}
            )
    
    async def _finalize_forwarding(self):
        """Finalize forwarding session"""
        
        self.is_forwarding = False
        
        # Cancel status update task
        if self.status_update_task:
            self.status_update_task.cancel()
        
        # Update session status
        if self.current_session:
            await db.update_progress(
                self.current_session["id"],
                self.current_session.get("last_message_id", 0),
                self.counters,
                status="completed",
                end_time=datetime.now()
            )
        
        # Send completion notification
        try:
            target_channel = await db.get_setting("target_channel")
            if target_channel:
                completion_text = f"""
🎉 **FORWARDING COMPLETED**
━━━━━━━━━━━━━━━━━━━━

📊 **Summary:**
✅ Successful: {self.counters['successful']:,}
❌ Failed: {self.counters['failed']:,}
♻️ Duplicates: {self.counters['duplicate']:,}
🗑 Deleted: {self.counters['deleted']:,}
⏱ Duration: {progress_tracker.get_formatted_elapsed()}
⚡ Avg speed: {progress_tracker.get_formatted_speed()} msgs/min

💾 All progress has been saved.
                """
                
                await self.client.send_message(int(target_channel), completion_text)
        except Exception as e:
            bot_logger.error(
                f"Failed to send completion notification: {e}",
                extra={"error": str(e)}
            )
        
        bot_logger.info(
            "Forwarding session completed",
            extra={
                "session_id": self.current_session["id"] if self.current_session else None,
                "counters": self.counters,
                "duration": progress_tracker.get_elapsed_time().total_seconds()
            }
        )
    
    def stop_forwarding(self):
        """Stop current forwarding operation"""
        self.is_forwarding = False

# Global forwarding handler instance
forwarding_handler = None

def setup_forwarding_handler(client: Client):
    """Setup forwarding handler"""
    global forwarding_handler
    forwarding_handler = ForwardingHandler(client)