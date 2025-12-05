# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

```bash
# Start development server (auto-creates venv and installs deps)
uv run fastapi dev

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/core/services/test_chat_service.py

# Run a specific test
uv run pytest tests/core/services/test_chat_service.py::TestChatService::test_send_message_adds_user_message

# Type checking
uv run mypy app tests
```

## Architecture

This is a FastAPI application following hexagonal (clean) architecture with three layers:

- **app/api/** - HTTP layer with routers. Routers use FastAPI's dependency injection to get services.
- **app/core/** - Business logic layer with models (Pydantic) and services. Services contain business rules and are independent of infrastructure. The `agent.py` wraps Semantic Kernel's ChatCompletionAgent.
- **app/infrastructure/** - Data access layer with repositories using SQLite (aiosqlite).

Data flows: Router → Service → Repository. Services receive repositories via constructor injection, enabling easy mocking in tests.

## Key Components

- **ChatService**: Orchestrates chat sessions with the Semantic Kernel agent
- **ToolService**: Manages OpenAPI tool registration and activation
- **SemanticKernelAgent**: Wrapper around Semantic Kernel's ChatCompletionAgent with OpenAI backend
- **SessionRepository/ToolRepository**: Async SQLite persistence

## Testing

Unit tests mock the repository and agent layers. Integration tests mock services at the API level using FastAPI's dependency override mechanism.

## API

Root path (`/`) redirects to `/docs` (Swagger UI). Endpoints:
- `/chat/{session_id}` - Chat operations (POST message, GET history, DELETE session)
- `/tools` - Tool management (POST register, GET list, DELETE remove)
- `/tools/{tool_id}/activate` - Activate a registered tool

## Configuration

Settings loaded from `.env` file:
- `OPENAI_API_KEY` - Required for chat functionality
- `DATABASE_URL` - SQLite database path (default: `chat.db`)
- `OPENAI_MODEL` - Model to use (default: `gpt-4o-mini`)
