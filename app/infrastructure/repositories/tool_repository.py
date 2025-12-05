from datetime import datetime
from typing import List, Optional

import aiosqlite

from app.core.models import Tool, ToolStatus


class ToolRepository:
    """Repository for managing tools with SQLite persistence"""

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
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                openapi_url TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)

        await self._connection.commit()

    async def close(self) -> None:
        """Close the database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def create(self, tool: Tool) -> Tool:
        """Create a new tool"""
        assert self._connection is not None

        await self._connection.execute(
            """INSERT INTO tools (id, name, openapi_url, description, status, error_message, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                tool.id,
                tool.name,
                tool.openapi_url,
                tool.description,
                tool.status.value,
                tool.error_message,
                tool.created_at.isoformat()
            )
        )
        await self._connection.commit()
        return tool

    async def get(self, tool_id: str) -> Optional[Tool]:
        """Get a tool by ID"""
        assert self._connection is not None

        async with self._connection.execute(
            """SELECT id, name, openapi_url, description, status, error_message, created_at
               FROM tools WHERE id = ?""",
            (tool_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            return Tool(
                id=row[0],
                name=row[1],
                openapi_url=row[2],
                description=row[3],
                status=ToolStatus(row[4]),
                error_message=row[5],
                created_at=datetime.fromisoformat(row[6])
            )

    async def get_all(self) -> List[Tool]:
        """Get all tools"""
        assert self._connection is not None

        tools = []
        async with self._connection.execute(
            """SELECT id, name, openapi_url, description, status, error_message, created_at
               FROM tools ORDER BY created_at DESC"""
        ) as cursor:
            async for row in cursor:
                tools.append(Tool(
                    id=row[0],
                    name=row[1],
                    openapi_url=row[2],
                    description=row[3],
                    status=ToolStatus(row[4]),
                    error_message=row[5],
                    created_at=datetime.fromisoformat(row[6])
                ))
        return tools

    async def get_active(self) -> List[Tool]:
        """Get all active tools"""
        assert self._connection is not None

        tools = []
        async with self._connection.execute(
            """SELECT id, name, openapi_url, description, status, error_message, created_at
               FROM tools WHERE status = ? ORDER BY created_at DESC""",
            (ToolStatus.ACTIVE.value,)
        ) as cursor:
            async for row in cursor:
                tools.append(Tool(
                    id=row[0],
                    name=row[1],
                    openapi_url=row[2],
                    description=row[3],
                    status=ToolStatus(row[4]),
                    error_message=row[5],
                    created_at=datetime.fromisoformat(row[6])
                ))
        return tools

    async def update_status(
        self,
        tool_id: str,
        status: ToolStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update a tool's status"""
        assert self._connection is not None

        await self._connection.execute(
            "UPDATE tools SET status = ?, error_message = ? WHERE id = ?",
            (status.value, error_message, tool_id)
        )
        await self._connection.commit()

    async def delete(self, tool_id: str) -> bool:
        """Delete a tool"""
        assert self._connection is not None

        # Check if tool exists
        async with self._connection.execute(
            "SELECT id FROM tools WHERE id = ?",
            (tool_id,)
        ) as cursor:
            if not await cursor.fetchone():
                return False

        await self._connection.execute(
            "DELETE FROM tools WHERE id = ?",
            (tool_id,)
        )
        await self._connection.commit()
        return True
