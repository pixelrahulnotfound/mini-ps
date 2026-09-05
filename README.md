# mini-ps

A travel planning CLI that uses an LLM and a local Model Context Protocol (MCP) server to generate itineraries and budgets.

## Features

- **MCP Tools**: Tools for destination overviews, logistics/transport, weather/seasons, activities, day-by-day itineraries, budgets, and accommodations.
- **Model Agnostic**: Works with local models (via `llama.cpp`) or any OpenAI-compatible API endpoint.
- **Offline First**: Uses local dataset files by default for deterministic behavior, with optional live enrichment (Wikipedia, Nominatim).
- **Interactive CLI**: Terminal interface built with Rich for interactive input or single-query mode.

## Architecture

```text
CLI ──> Agent Loop ──> LLM (OpenAI-compatible)
              │
              └── calls tools via MCP SSE
                       │
                       ▼
              MCP Server (:3000)
              ├── destination
              ├── logistics
              ├── timing
              ├── activities
              ├── itinerary
              ├── budget
              └── accommodation
```

## Quick Start

### 1. Setup Environment

```bash
git clone https://github.com/pixelrahulnotfound/mini-ps.git
cd mini-ps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Start MCP Server

In one terminal:

```bash
python -m mcp_server.server
```

### 3. Start LLM Server

In a second terminal, start an OpenAI-compatible endpoint (e.g. `llama.cpp`):

```bash
python -m llama_cpp.server \
  --model models/qwen2.5-7b-instruct-q4_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --n_ctx 4096 \
  --n_gpu_layers 0 \
  --chat_format chatml
```

### 4. Run CLI

In a third terminal:

```bash
# Interactive mode
python -m cli.main

# Or direct query mode
python -m cli.main --query "Plan a 5-day trip to Goa for 3 people from Hyderabad in December with a budget of 75000 INR."
```

## Configuration

Settings are configured via `.env` (or environment variables):

| Variable | Default | Description |
|---|---|---|
| `MINIPS_LLM_BASE_URL` | `http://localhost:8080/v1` | LLM API base URL |
| `MINIPS_LLM_API_KEY` | `local` | API key (if required) |
| `MINIPS_LLM_MODEL` | `qwen2.5-7b-instruct` | Model name |
| `MINIPS_MCP_URL` | `http://localhost:3000/sse` | MCP server SSE endpoint |
| `MINIPS_MAX_STEPS` | `10` | Maximum planning tool-call iterations |
| `MINIPS_ENABLE_LIVE_DATA` | `false` | Enable live API lookups (Wikipedia, etc.) |

## Testing

Run unit tests with pytest:

```bash
pytest
```

## Google Colab

To run on Google Colab without local setup, open `colab/demo.ipynb` or refer to [COLAB_GUIDE.md](file:///home/pixelnotfound/Downloads/wandermind/COLAB_GUIDE.md).
