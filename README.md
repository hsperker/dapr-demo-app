# Semantic Kernel Chat API

A headless ChatGPT clone using Semantic Kernel agents with dynamic OpenAPI tool support.

## Overview

This project provides a chat API powered by Semantic Kernel's ChatCompletionAgent. It supports:

- **Session-based Chat**: Server-side session management - just provide a session ID
- **Conversation Persistence**: Pluggable storage backends (SQLite, Dapr state stores)
- **Dynamic Tool Extension**: Register OpenAPI specs to extend agent capabilities
- **Clean Architecture**: Hexagonal architecture for maintainability and testability

## Features

- **Semantic Kernel Agent** - Chat powered by OpenAI via Semantic Kernel
- **Session Management** - Server-side conversation history
- **OpenAPI Tool Registration** - Extend agent with external APIs
- **Pluggable Persistence** - SQLite or Dapr state stores (Redis, CosmosDB, etc.)
- **Swagger UI** - Built-in API documentation at `/docs`

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- OpenAI API key
- [Dapr CLI](https://docs.dapr.io/getting-started/install-dapr-cli/) (optional, for Dapr state store)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd semantic-kernel-chat
   ```

2. Create `.env` file with your OpenAI key:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. Run tests to verify setup:
   ```bash
   uv run pytest
   ```

4. Start the development server:
   ```bash
   uv run fastapi dev
   ```

5. Open http://localhost:8000/docs for the Swagger UI

### Running with Dapr

To use Dapr for state management (enables Redis, CosmosDB, and other backends):

1. Install and initialize Dapr:
   ```bash
   dapr init
   ```

2. Run with Dapr multi-app:
   ```bash
   dapr run -f dapr.yaml
   ```

The Dapr state store is configured in `resources/statestore.yaml`. By default it uses SQLite, but you can swap to Redis or other backends by changing the component configuration.

## API Endpoints

### Chat

- `POST /chat/{session_id}` - Send a message, get a response
- `GET /chat/{session_id}/history` - Get conversation history
- `DELETE /chat/{session_id}` - Delete a session

### Tools

- `POST /tools` - Register a new OpenAPI tool
- `GET /tools` - List all registered tools
- `GET /tools/{tool_id}` - Get a specific tool
- `POST /tools/{tool_id}/activate` - Activate a tool
- `DELETE /tools/{tool_id}` - Remove a tool

## Project Structure

```
app/
├── api/routers/        # HTTP endpoints
├── core/
│   ├── models/         # Domain models (Pydantic)
│   └── services/       # Business logic & agent
├── infrastructure/
│   └── repositories/   # Data persistence
│       ├── session_repository_sqlite.py  # SQLite backend
│       └── session_repository_dapr.py    # Dapr state store backend
├── config.py           # Settings from .env
└── main.py             # FastAPI application

resources/
└── statestore.yaml     # Dapr state store component

tests/
├── core/               # Unit tests
├── infrastructure/     # Repository tests
└── integration/        # API tests
```

## Switching Persistence Backends

The application uses a repository pattern, making it easy to swap storage backends.

### Using SQLite (default for tests)

```python
from app.infrastructure.repositories import SessionRepositorySqLite

session_repository = SessionRepositorySqLite(settings.database_path)
```

### Using Dapr State Store

```python
from app.infrastructure.repositories import SessionRepositoryDapr

session_repository = SessionRepositoryDapr()
```

With Dapr, you can switch from SQLite to Redis by simply changing `resources/statestore.yaml`:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
    - name: redisHost
      value: "localhost:6379"
```

No code changes required - just update the Dapr component configuration.

## Configuration

Environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `DATABASE_URL` | SQLite database path | `chat.db` |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `AGENT_INSTRUCTIONS` | System prompt for agent | `You are a helpful AI assistant.` |
