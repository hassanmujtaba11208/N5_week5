# Full-Stack GenAI App: API + UI + Auth + Logging

A locally runnable full-stack GenAI-style application combining:
- A local RAG retrieval pipeline
- A bounded single-agent tool-use loop
- FastAPI backend
- Streamlit frontend that communicates with the backend over HTTP only
- API-key authentication for `POST /ask`
- Per-API-key sliding-window rate limiting
- Structured JSON request and tool logs

No paid API, cloud account, or external LLM key is required. The included retrieval engine uses TF-IDF for deterministic offline semantic-style retrieval. The agent routes between a safe calculator, local RAG, and a date/time tool.

## Assignment requirements checklist

| Requirement | Implementation |
|---|---|
| `POST /ask` routes to RAG or agent by mode | `mode="rag"` or `mode="agent"` |
| `GET /health` | Public health endpoint |
| API-key authentication on `/ask` | `X-API-Key` header |
| Per-key rate limiting | Sliding window, configurable |
| Structured JSON request logs | `logs/requests.jsonl` |
| Frontend calls backend over HTTP only | Streamlit uses `requests` and API URL |

## Architecture

```text
Browser
  |
  v
Streamlit UI (frontend/app.py)
  | HTTP requests only
  v
FastAPI (backend/app/main.py)
  |-- API-key authentication
  |-- per-key rate limiter
  |-- JSON request logging
  |
  +--> RAG service --> local knowledge base --> TF-IDF retrieval
  |
  +--> Agent service --> safe calculator / RAG / date-time tools
```

## Project structure

```text
Full_Stack_GenAI_App/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── rate_limiter.py
│   │   ├── logging_config.py
│   │   ├── schemas.py
│   │   ├── services/
│   │   │   ├── rag.py
│   │   │   └── agent.py
│   │   └── tools/
│   │       ├── calculator.py
│   │       └── datetime_tool.py
│   ├── data/knowledge_base.md
│   ├── logs/.gitkeep
│   └── requirements.txt
├── frontend/
│   ├── app.py
│   └── requirements.txt
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_auth_rate_limit.py
│   └── test_tools.py
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10+
- Windows 10/11 or macOS/Linux
- VS Code recommended

## Windows setup (VS Code PowerShell terminal)

### 1. Extract and open the project

Extract the ZIP, then open the `Full_Stack_GenAI_App` folder in VS Code.

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install backend and frontend dependencies

```powershell
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 4. Configure the API key

Copy `.env.example` to `.env` and set a private key. The app also accepts environment variables directly.

```powershell
Copy-Item .env.example .env
```

Default development key in `.env.example` is `dev-local-key-change-me`. Change it before sharing or deploying the project.

### 5. Start the FastAPI backend

Open **Terminal 1** in VS Code:

```powershell
.\venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend docs: http://127.0.0.1:8000/docs  
Health check: http://127.0.0.1:8000/health

### 6. Start the Streamlit frontend

Open **Terminal 2** in VS Code:

```powershell
.\venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

The frontend opens in your browser. It sends requests to FastAPI over HTTP and does not import backend services.

## API usage

### Health

```http
GET /health
```

No API key required. Example response:

```json
{
  "status": "ok",
  "service": "full-stack-genai-api",
  "version": "1.0.0"
}
```

### Ask

```http
POST /ask
X-API-Key: dev-local-key-change-me
Content-Type: application/json
```

RAG mode:

```json
{
  "query": "What does the knowledge base say about anomaly detection?",
  "mode": "rag",
  "top_k": 3
}
```

Agent mode:

```json
{
  "query": "What is 125 * (8 + 2)?",
  "mode": "agent",
  "top_k": 3
}
```

Example PowerShell request:

```powershell
$headers = @{ "X-API-Key" = "dev-local-key-change-me" }
$body = @{
  query = "What does the knowledge base say about anomaly detection?"
  mode = "rag"
  top_k = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/ask" -Method Post -Headers $headers -ContentType "application/json" -Body $body
```

## Authentication and rate limiting

- `/ask` requires `X-API-Key`.
- Missing or invalid keys receive HTTP `401`.
- Each API key has its own sliding-window request counter.
- Default limit: 10 requests per 60 seconds per key.
- Exceeding the limit returns HTTP `429` and a `Retry-After` header.
- Configure with `API_KEYS`, `RATE_LIMIT_REQUESTS`, and `RATE_LIMIT_WINDOW_SECONDS`.

`API_KEYS` accepts comma-separated keys. Example:

```powershell
$env:API_KEYS = "key-one,key-two"
```

For production, store secrets in a secret manager and use a shared rate-limit store such as Redis when running multiple workers. The included in-memory limiter is appropriate for a single-process assignment/demo.

## Structured logs

Every API request is written as one JSON object per line to:

`backend/logs/requests.jsonl`

Fields include timestamp, level, event, method, path, status code, duration, client IP, API-key fingerprint (not the raw key), and request ID.

Agent tool events are written to:

`backend/logs/tool_events.jsonl`

The raw API key is never written to logs.

## Tests

Run from the project root with the virtual environment active:

```powershell
pytest -v
```

Tests cover health, authentication, both modes, rate limiting, calculator safety, and RAG retrieval. The rate-limit test uses a test-specific app configuration to avoid changing your normal settings.

## Notes and limitations

- RAG uses TF-IDF cosine similarity over the included local knowledge base. It is a lightweight, reproducible retrieval implementation, not a hosted vector database or a generative LLM.
- `mode="agent"` uses a bounded, deterministic ReAct-style router and tools. It chooses a tool, executes it, observes the result, and returns a response.
- The included knowledge base is a sample infrastructure/AI operations corpus. If your Task 6 project has a required corpus, replace `backend/data/knowledge_base.md` with those source documents or extend `RAGService` to load your Task 6 ChromaDB index.
- The in-memory rate limiter resets when the backend restarts and is not shared between multiple worker processes.
