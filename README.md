# PolyAgents - Multi-Agent System (Gemini + Qwen3)

## Overview
A multi-agent system with orchestration, intelligent consensus, and persistent memory. Supports cloud agents (Gemini) and a local model (Qwen3-0.6B) for summarization and fusion of responses.

### Key Features
- Orchestration of Gemini (cloud) agents with local consensus and synthesis
- Local model Qwen3-0.6B for summaries and fusion ("thinking" mode)
- Real-time streaming via WebSocket
- Memory: Redis, PostgreSQL, Qdrant (optional)
- Advanced security: API Key, JWT, rate-limit
- Robust healthcheck (waits for local model to load)

### Requirements
- Python >=3.11
- Docker & Docker Compose
- Redis, PostgreSQL
- Qdrant (optional)
- Local model: Qwen/Qwen3-0.6B (HuggingFace)

### Quickstart
```bash
git clone <repository-url>
cd PolyAgents-main
cp env.example .env  # configure variables
pip install -r requirements.txt
# or
# docker-compose -f docker-compose.dev.yml up -d --build
```

### Environment (.env) excerpt
```env
LOCAL_LLM_MODEL=Qwen/Qwen3-0.6B
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_HOST=0.0.0.0
API_PORT=8000
NUM_AGENTS=3
CONSENSUS_ALGORITHM=synthesis
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
REDIS_HOST=redis
POSTGRES_HOST=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=polyagents
JWT_SECRET_KEY=your_very_secure_secret_key_here
API_KEY_ENABLED=true
RATE_LIMITING_ENABLED=true
# (see env.example for more)
```

### Notable changes
- **Local model Qwen3-0.6B**: used for summarizing and fusing cloud agent (Gemini) responses in "thinking" mode.
- **Parametric loading**: local model is downloaded from HuggingFace using LOCAL_LLM_MODEL and, if needed, HUGGINGFACE_TOKEN.
- **Robust healthcheck**: container is healthy only after the local model is fully loaded.
- **Healthcheck timeout increased**: see docker-compose.dev.yml (start_period=240s).
- **requirements.txt updated**: transformers>=4.41.0, torch>=2.1, accelerate, safetensors.

### Run
```bash
# Development (hot reload, robust healthcheck)
docker-compose -f docker-compose.dev.yml up -d --build
# Or backend only
python -m app.main
```

### Troubleshooting
- If the container is unhealthy, check logs: local model loading may take 1-3 minutes.
- If you get HuggingFace/tokenizer errors, update transformers and torch as per requirements.
- For private models, set HUGGINGFACE_TOKEN.

---

# PolyAgents - Sistema Multi-Agente (Gemini + Qwen3)

## Descrizione
Sistema multi-agente con orchestrazione, consenso intelligente e memoria persistente. Supporta agenti cloud (Gemini) e un modello locale (Qwen3-0.6B) per riassunti e fusione delle risposte.

### Caratteristiche principali
- Orchestrazione di agenti Gemini (cloud) con consenso e sintesi locale
- Modello locale Qwen3-0.6B per riassunti e fusione (modalità thinking)
- Streaming risposte via WebSocket
- Memoria: Redis, PostgreSQL, Qdrant (opzionale)
- Sicurezza avanzata: API Key, JWT, rate-limit
- Healthcheck robusto (attende caricamento modello locale)

### Requisiti
- Python >=3.11
- Docker & Docker Compose
- Redis, PostgreSQL
- Qdrant (opzionale)
- Modello locale: Qwen/Qwen3-0.6B (HuggingFace)

### Installazione rapida
```bash
git clone <repository-url>
cd PolyAgents-main
cp env.example .env  # configura le variabili
pip install -r requirements.txt
# oppure
# docker-compose -f docker-compose.dev.yml up -d --build
```

### Estratto configurazione (.env)
```env
LOCAL_LLM_MODEL=Qwen/Qwen3-0.6B
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_HOST=0.0.0.0
API_PORT=8000
NUM_AGENTS=3
CONSENSUS_ALGORITHM=synthesis
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
REDIS_HOST=redis
POSTGRES_HOST=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=polyagents
JWT_SECRET_KEY=your_very_secure_secret_key_here
API_KEY_ENABLED=true
RATE_LIMITING_ENABLED=true
# (vedi env.example per altre variabili)
```

### Novità e modifiche principali
- **Modello locale Qwen3-0.6B**: usato per riassumere e fondere le risposte degli agenti cloud (Gemini) in modalità thinking.
- **Caricamento parametrico**: il modello locale viene scaricato da HuggingFace usando LOCAL_LLM_MODEL e, se necessario, HUGGINGFACE_TOKEN.
- **Healthcheck robusto**: il container è healthy solo dopo il caricamento completo del modello locale.
- **Timeout healthcheck aumentato**: vedi docker-compose.dev.yml (start_period=240s).
- **requirements.txt aggiornato**: transformers>=4.41.0, torch>=2.1, accelerate, safetensors.

### Avvio
```bash
# Sviluppo (hot reload, healthcheck robusto)
docker-compose -f docker-compose.dev.yml up -d --build
# Oppure solo backend
python -m app.main
```

### Troubleshooting
- Se il container va in unhealthy, controlla i log: il caricamento del modello locale può richiedere 1-3 minuti.
- Se hai errori di HuggingFace/tokenizer, aggiorna transformers e torch come da requirements.
- Per modelli privati, imposta HUGGINGFACE_TOKEN.

---

Per supporto o richieste, apri una issue o contatta il maintainer. 