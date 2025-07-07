"""FastAPI gateway for poly-agents system."""

import asyncio
import uuid
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel

from .orchestrator import Orchestrator
from .config import settings


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str


app = FastAPI(
    title="Poly-Agents System",
    description="Multi-agent Gemini system with consensus",
    version="1.0.0"
)

orchestrator = Orchestrator()


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    await orchestrator.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    await orchestrator.cleanup()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint - runs multi-agent conversation with consensus."""
    try:
        conversation_id = str(uuid.uuid4())
        answer = await orchestrator.run_conversation(
            prompt=request.prompt,
            conversation_id=conversation_id,
            n_turns=settings.default_turns
        )
        
        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket streaming endpoint for real-time conversation updates."""
    # TODO: Implement WebSocket streaming for real-time agent debates
    await websocket.accept()
    await websocket.send_text("WebSocket streaming not yet implemented")
    await websocket.close()


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 