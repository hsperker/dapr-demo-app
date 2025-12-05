"""
FastAPI application entry point.

Semantic Kernel Chat API - A headless ChatGPT clone.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.routers import chat, tools
from app.config import settings
from app.core.services import (
    AgentPluginManager,
    ChatService,
    SemanticKernelAgent,
    ToolService,
)
from app.infrastructure.repositories import (
    SessionRepository,
    SessionRepositoryDapr,
    ToolRepository,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown"""

    # Initialize repositories
    # session_repository = SessionRepository(settings.database_path)
    session_repository = SessionRepositoryDapr()
    tool_repository = ToolRepository(settings.database_path)

    await session_repository.initialize()
    await tool_repository.initialize()

    # Initialize agent
    agent = SemanticKernelAgent(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        instructions=settings.agent_instructions,
    )

    # Initialize services
    chat_service = ChatService(session_repository, agent)
    tool_service = ToolService(tool_repository)
    plugin_manager = AgentPluginManager(agent)

    # Store in app.state for dependency injection
    app.state.chat_service = chat_service
    app.state.tool_service = tool_service
    app.state.plugin_manager = plugin_manager
    app.state.agent = agent

    # Keep references for cleanup
    app.state.session_repository = session_repository
    app.state.tool_repository = tool_repository

    yield

    # Cleanup
    await app.state.session_repository.close()
    await app.state.tool_repository.close()


app = FastAPI(
    title="Semantic Kernel Chat API",
    description="A headless ChatGPT clone using Semantic Kernel agents with dynamic OpenAPI tool support",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(chat.router)
app.include_router(tools.router)


@app.get("/", include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    """Redirect root to API docs"""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
