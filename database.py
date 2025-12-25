"""
Telegram Forward Bot - Database Module
Industrial-strength database operations with SQLite
"""

import aiosqlite
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from config import Config

logger = logging.getLogger(__name__)

class Database:
    """Database manager for bot operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """Establish database connection"""
        try:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self._connection.execute("PRAGMA journal_mode = WAL")
            await self._connection.execute("PRAGMA synchronous = NORMAL")
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def initialize(self) -> None:
        """Initialize database tables"""
        await self._create_tables()
        await self._create_indexes()
        logger.info("Database initialized successfully")
    
    async def _create_tables(self) -> None:
        """Create all required tables"""
        
        # Progress tracking table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS forwarding_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_channel_id TEXT NOT NULL,
                target_channel_id TEXT NOT NULL,
                last_message_id INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                successful_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                duplicate_count INTEGER DEFAULT 0,
                deleted_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0,
                filtered_count INTEGER DEFAULT 0,
                start_time DATETIME,
                end_time DATETIME,
                status TEXT DEFAULT 'idle',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Failed messages table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS failed_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                message_id INTEGER NOT NULL,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                file_size INTEGER,
                content_type TEXT,
                file_unique_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES forwarding_progress (id)
            )
        """)
        
        # Bot settings table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Session management table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                session_string TEXT,
                source_channel TEXT,
                target_channel TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Message tracking table (for duplicates)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS message_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                source_message_id INTEGER,
                target_message_id INTEGER,
                file_unique_id TEXT,
                content_hash TEXT,
                forwarded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES forwarding_progress (id)
            )
        """)
        
        # Bot statistics table
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS bot_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_messages_forwarded INTEGER DEFAULT 0,
                total_sessions INTEGER DEFAULT 0,
                total_errors INTEGER DEFAULT 0,
                uptime_seconds INTEGER DEFAULT 0,
                last_reset DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._connection.commit()
    
    async def _create_indexes(self) -> None:
        """Create database indexes for performance"""
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_progress_status ON forwarding_progress (status)",
            "CREATE INDEX IF NOT EXISTS idx_progress_channels ON forwarding_progress (source_channel_id, target_channel_id)",
            "CREATE INDEX IF NOT EXISTS idx_failed_messages_session ON failed_messages (session_id)",
            "CREATE INDEX IF NOT EXISTS idx_failed_messages_msg ON failed_messages (message_id)",
            "CREATE INDEX IF NOT EXISTS idx_message_tracker_session ON message_tracker (session_id)",
            "CREATE INDEX IF NOT EXISTS idx_message_tracker_unique ON message_tracker (file_unique_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id)",
        ]
        
        for index in indexes:
            try:
                await self._connection.execute(index)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")
        
        await self._connection.commit()
    
    async def create_forwarding_session(
        self,
        source_channel_id: str,
        target_channel_id: str,
        start_message_id: int = 0
    ) -> int:
        """Create a new forwarding session"""
        
        cursor = await self._connection.execute("""
            INSERT INTO forwarding_progress 
            (source_channel_id, target_channel_id, last_message_id, start_time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (source_channel_id, target_channel_id, start_message_id, datetime.now(), BotState.FORWARDING))
        
        await self._connection.commit()
        return cursor.lastrowid
    
    async def update_progress(
        self,
        session_id: int,
        last_message_id: int,
        counters: Dict[str, int],
        status: Optional[str] = None
    ) -> None:
        """Update forwarding progress"""
        
        update_fields = [
            "last_message_id = ?",
            "successful_count = ?",
            "failed_count = ?",
            "duplicate_count = ?",
            "deleted_count = ?",
            "skipped_count = ?",
            "filtered_count = ?",
            "updated_at = ?"
        ]
        
        params = [
            last_message_id,
            counters.get("successful", 0),
            counters.get("failed", 0),
            counters.get("duplicate", 0),
            counters.get("deleted", 0),
            counters.get("skipped", 0),
            counters.get("filtered", 0),
            datetime.now()
        ]
        
        if status:
            update_fields.append("status = ?")
            params.append(status)
        
        params.append(session_id)
        
        await self._connection.execute(f"""
            UPDATE forwarding_progress 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """, params)
        
        await self._connection.commit()
    
    async def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get session details"""
        
        cursor = await self._connection.execute("""
            SELECT * FROM forwarding_progress WHERE id = ?
        """, (session_id,))
        
        row = await cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    async def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Get currently active session"""
        
        cursor = await self._connection.execute("""
            SELECT * FROM forwarding_progress 
            WHERE status IN (?, ?)
            ORDER BY created_at DESC LIMIT 1
        """, (BotState.FORWARDING, BotState.PAUSED))
        
        row = await cursor.fetchone()
        if row:
            return dict(zip([d[0] for d in cursor.description], row))
        return None
    
    async def add_failed_message(
        self,
        session_id: int,
        message_id: int,
        error_message: str,
        file_size: Optional[int] = None,
        content_type: Optional[str] = None,
        file_unique_id: Optional[str] = None
    ) -> None:
        """Add a failed message to tracking"""
        
        await self._connection.execute("""
            INSERT INTO failed_messages 
            (session_id, message_id, error_message, file_size, content_type, file_unique_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, message_id, error_message, file_size, content_type, file_unique_id))
        
        await self._connection.commit()
    
    async def get_failed_messages(
        self,
        session_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get failed messages for a session"""
        
        cursor = await self._connection.execute("""
            SELECT * FROM failed_messages 
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, limit))
        
        rows = await cursor.fetchall()
        return [dict(zip([d[0] for d in cursor.description], row)) for row in rows]
    
    async def is_duplicate_message(
        self,
        session_id: int,
        file_unique_id: Optional[str] = None,
        content_hash: Optional[str] = None
    ) -> bool:
        """Check if message is duplicate"""
        
        if not file_unique_id and not content_hash:
            return False
        
        query = "SELECT COUNT(*) FROM message_tracker WHERE session_id = ? AND ("
        params = [session_id]
        
        conditions = []
        if file_unique_id:
            conditions.append("file_unique_id = ?")
            params.append(file_unique_id)
        if content_hash:
            conditions.append("content_hash = ?")
            params.append(content_hash)
        
        query += " OR ".join(conditions) + ")"
        
        cursor = await self._connection.execute(query, params)
        count = await cursor.fetchone()
        
        return count[0] > 0
    
    async def track_message(
        self,
        session_id: int,
        source_message_id: int,
        target_message_id: int,
        file_unique_id: Optional[str] = None,
        content_hash: Optional[str] = None
    ) -> None:
        """Track forwarded message"""
        
        await self._connection.execute("""
            INSERT INTO message_tracker 
            (session_id, source_message_id, target_message_id, file_unique_id, content_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, source_message_id, target_message_id, file_unique_id, content_hash))
        
        await self._connection.commit()
    
    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get bot setting"""
        
        cursor = await self._connection.execute("""
            SELECT value FROM bot_settings WHERE key = ?
        """, (key,))
        
        row = await cursor.fetchone()
        return row[0] if row else default
    
    async def set_setting(self, key: str, value: str) -> None:
        """Set bot setting"""
        
        await self._connection.execute("""
            INSERT OR REPLACE INTO bot_settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now()))
        
        await self._connection.commit()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get bot statistics"""
        
        # Get total statistics
        cursor = await self._connection.execute("""
            SELECT 
                SUM(successful_count) as total_forwarded,
                SUM(failed_count) as total_failed,
                COUNT(*) as total_sessions,
                AVG(successful_count) as avg_success_per_session
            FROM forwarding_progress
        """)
        
        stats = await cursor.fetchone()
        
        # Get recent activity (last 24 hours)
        cursor = await self._connection.execute("""
            SELECT COUNT(*) as recent_sessions
            FROM forwarding_progress
            WHERE created_at > datetime('now', '-1 day')
        """)
        
        recent = await cursor.fetchone()
        
        return {
            "total_messages_forwarded": stats[0] or 0,
            "total_errors": stats[1] or 0,
            "total_sessions": stats[2] or 0,
            "average_success_rate": stats[3] or 0,
            "recent_sessions": recent[0] or 0
        }
    
    async def reset_all(self) -> None:
        """Reset all data (use with caution)"""
        
        tables = [
            "forwarding_progress",
            "failed_messages",
            "message_tracker",
            "bot_settings",
            "sessions"
        ]
        
        for table in tables:
            await self._connection.execute(f"DELETE FROM {table}")
        
        await self._connection.commit()
        logger.warning("All database tables have been reset")
    
    async def close(self) -> None:
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            logger.info("Database connection closed")

# Global database instance
db = Database()