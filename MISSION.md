# Mission: Headless ChatGPT Clone with Semantic Kernel Agent

## Overview

Build a headless chat application with an LLM agent powered by Semantic Kernel. The UI is Swagger UI (already provided by FastAPI).

## Core Requirements

1. **Chat with LLM Agent** - Conversational interface using Semantic Kernel agent
2. **Dynamic Tool Extension** - Extend agent capabilities by providing OpenAPI spec URLs
3. **Session Management** - Server-side session handling (client provides session_id)
4. **Persistence** - SQLite initially, following hexagonal architecture for easy backend swap
5. **Configuration** - OpenAI credentials via `.env` file

## Architecture

Following hexagonal/clean architecture:

```
app/
├── api/
│   └── routers/
│       ├── chat.py          # Chat endpoints
│       └── tools.py         # OpenAPI tool registration
├── core/
│   ├── models/
│   │   ├── chat.py          # Message, Session, Conversation models
│   │   └── tool.py          # Tool/OpenAPI spec models
│   └── services/
│       ├── chat_service.py  # Chat orchestration
│       ├── agent_service.py # Semantic Kernel agent management
│       └── tool_service.py  # OpenAPI tool registration
└── infrastructure/
    └── repositories/
        ├── session_repository.py  # Session persistence (SQLite)
        └── tool_repository.py     # Registered tools persistence
```

## API Endpoints

- `POST /chat/{session_id}` - Send message, get response
- `GET /chat/{session_id}/history` - Get conversation history
- `DELETE /chat/{session_id}` - Delete session
- `POST /tools` - Register OpenAPI spec URL
- `GET /tools` - List registered tools
- `DELETE /tools/{tool_id}` - Remove tool

## Development Approach

**Test-Driven Development (TDD)**
1. Write failing tests first
2. Implement code to make tests pass
3. Refactor as needed

## Dependencies

- `semantic-kernel` - Agent framework
- `python-dotenv` - Environment variable loading
- `aiosqlite` - Async SQLite support
- `httpx` - Async HTTP client for fetching OpenAPI specs
