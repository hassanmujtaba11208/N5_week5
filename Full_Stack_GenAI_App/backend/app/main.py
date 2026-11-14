from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.app.config import (
    DEFAULT_TOP_K, KNOWLEDGE_BASE_PATH, LOG_DIR,
    RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS,
)
from backend.app.auth import require_api_key, key_fingerprint
from backend.app.rate_limiter import RateLimiter
from backend.app.logging_config import get_loggers
from backend.app.schemas import AskRequest, AskResponse
from backend.app.services.rag import RAGService
from backend.app.services.agent import AgentService

request_logger, tool_logger = get_loggers(LOG_DIR)
rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
rag_service = RAGService(KNOWLEDGE_BASE_PATH)
agent_service = AgentService(rag_service, tool_logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Full-Stack GenAI API",
    description="Authenticated RAG and bounded-agent API with structured logging and rate limiting.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def structured_request_logging(request: Request, call_next):
    request_id = str(uuid4())
    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        request_logger.write(
            level="ERROR", event="http_request", request_id=request_id,
            method=request.method, path=request.url.path, status_code=500,
            duration_ms=round((perf_counter() - started) * 1000, 2),
            client_ip=request.client.host if request.client else None,
            error=str(exc),
        )
        raise
    finally:
        # API key is intentionally not logged. A fingerprint is added in the route log.
        if status_code != 500:
            request_logger.write(
                level="INFO", event="http_request", request_id=request_id,
                method=request.method, path=request.url.path, status_code=status_code,
                duration_ms=round((perf_counter() - started) * 1000, 2),
                client_ip=request.client.host if request.client else None,
            )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "full-stack-genai-api", "version": "1.0.0"}


@app.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, request: Request, api_key: str = Depends(require_api_key)):
    fingerprint = key_fingerprint(api_key)
    allowed, retry_after, current_count = rate_limiter.check(fingerprint)
    if not allowed:
        request_logger.write(
            level="WARNING", event="rate_limit_exceeded",
            request_id=request.headers.get("X-Request-ID"),
            api_key_fingerprint=fingerprint, path="/ask",
            limit=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW_SECONDS,
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started = perf_counter()
    if payload.mode == "rag":
        results = rag_service.search(payload.query, payload.top_k)
        if results:
            answer = "Retrieved knowledge-base passages:\n\n" + "\n\n".join(
                f"{r['rank']}. {r['section']} (similarity {r['similarity']})\n{r['text']}"
                for r in results
            )
        else:
            answer = "No sufficiently relevant passage was found in the local knowledge base."
        tool_used, iterations = "rag", 1
    else:
        agent_result = agent_service.ask(payload.query, payload.top_k)
        answer = agent_result["answer"]
        results = agent_result["results"]
        tool_used, iterations = agent_result["tool_used"], agent_result["iterations"]

    duration_ms = round((perf_counter() - started) * 1000, 2)
    request_logger.write(
        level="INFO", event="ask_request", request_id=request_id,
        method="POST", path="/ask", mode=payload.mode, status_code=200,
        api_key_fingerprint=fingerprint, query_length=len(payload.query),
        top_k=payload.top_k, tool_used=tool_used, iterations=iterations,
        rate_limit_count=current_count, duration_ms=duration_ms,
    )
    return AskResponse(
        mode=payload.mode, answer=answer, results=results,
        tool_used=tool_used, iterations=iterations, request_id=request_id,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # FastAPI's standard response shape is preserved; middleware logs status and duration.
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )
