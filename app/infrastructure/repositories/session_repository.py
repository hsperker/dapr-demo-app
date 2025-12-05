import json
from datetime import datetime
from typing import Optional

import aiosqlite

from app.core.models import Message, MessageRole, Session


class SessionRepository:
    """Repository for managing chat sessions with SQLite persistence"""

    def __init__(self, db_path: str = "chat.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initialize the database connection and create tables"""
        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()

    async def _create_tables(self) -> None:
        """Create the necessary database tables"""
        assert self._connection is not None

        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                message_order INTEGER NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id
            ON messages(session_id)
        """)

        await self._connection.commit()

    async def close(self) -> None:
        """Close the database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def create(self, session_id: str) -> Session:
        """Create a new session"""
        assert self._connection is not None

        now = datetime.utcnow().isoformat()
        await self._connection.execute(
            "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
            (session_id, now, now)
        )
        await self._connection.commit()

        return Session(
            id=session_id,
            messages=(),
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )

    async def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        assert self._connection is not None

        async with self._connection.execute(
            "SELECT id, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            session_data = {
                "id": row[0],
                "created_at": datetime.fromisoformat(row[1]),
                "updated_at": datetime.fromisoformat(row[2])
            }

        # Fetch messages
        messages = []
        async with self._connection.execute(
            """SELECT id, role, content, created_at
               FROM messages
               WHERE session_id = ?
               ORDER BY message_order ASC""",
            (session_id,)
        ) as cursor:
            async for row in cursor:
                messages.append(Message(
                    id=row[0],
                    role=MessageRole(row[1]),
                    content=row[2],
                    created_at=datetime.fromisoformat(row[3])
                ))

        return Session(
            id=session_data["id"],
            messages=tuple(messages),
            created_at=session_data["created_at"],
            updated_at=session_data["updated_at"]
        )

    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to a session"""
        assert self._connection is not None

        # Get the next message order
        async with self._connection.execute(
            "SELECT COALESCE(MAX(message_order), -1) + 1 FROM messages WHERE session_id = ?",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            next_order = row[0] if row else 0

        # Insert the message
        await self._connection.execute(
            """INSERT INTO messages (id, session_id, role, content, created_at, message_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                message.id,
                session_id,
                message.role.value,
                message.content,
                message.created_at.isoformat(),
                next_order
            )
        )

        # Update session's updated_at
        now = datetime.utcnow().isoformat()
        await self._connection.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id)
        )

        await self._connection.commit()

    async def delete(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        assert self._connection is not None

        # Check if session exists
        async with self._connection.execute(
            "SELECT id FROM sessions WHERE id = ?",
            (session_id,)
        ) as cursor:
            if not await cursor.fetchone():
                return False

        # Delete messages first (foreign key constraint)
        await self._connection.execute(
            "DELETE FROM messages WHERE session_id = ?",
            (session_id,)
        )

        # Delete session
        await self._connection.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )

        await self._connection.commit()
        return True

    async def get_or_create(self, session_id: str) -> Session:
        """Get an existing session or create a new one"""
        session = await self.get(session_id)
        if session is None:
            session = await self.create(session_id)
        return session
