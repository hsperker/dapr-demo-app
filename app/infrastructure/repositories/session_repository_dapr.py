import pprint
from datetime import datetime
from typing import Optional

from dapr.clients import DaprClient

from app.core.models import Message, Session


class SessionRepositoryDapr:
    """Repository for managing chat sessions with SQLite persistence"""

    DAPR_STORE_NAME = "statestore"

    async def initialize(self) -> None:
        """Initialize the repository (create tables, etc.)"""
        pass

    async def close(self) -> None:
        """Close any connections"""
        pass

    async def create(self, session_id: str) -> Session:
        """Create a new session"""
        now = datetime.utcnow().isoformat()

        session = Session(
            id=session_id,
            messages=(),
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

        with DaprClient() as client:
            client.save_state(
                self.DAPR_STORE_NAME, session_id, session.model_dump_json()
            )

        return session

    async def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        with DaprClient() as client:
            result = client.get_state(self.DAPR_STORE_NAME, session_id)
            if result and result.data:
                print("Result: " + str(result.data))
                return Session.model_validate_json(result.data)
            return None

    async def get_or_create(self, session_id: str) -> Session:
        """Get an existing session or create a new one"""
        session = await self.get(session_id)
        if session is None:
            session = await self.create(session_id)
        return session

    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to a session"""
        session = await self.get_or_create(session_id)
        updated_session = session.with_message(message)

        with DaprClient() as client:
            client.save_state(self.DAPR_STORE_NAME, session_id, updated_session.model_dump_json())

    async def delete(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        with DaprClient() as client:
            client.delete_state(self.DAPR_STORE_NAME, session_id)
            return True
