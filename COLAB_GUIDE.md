# Running mini-ps on Google Colab

mini-ps uses two local processes in the Colab runtime:

1. **llama.cpp** serves a quantized Qwen model through an OpenAI-compatible API.
2. **mini-ps MCP server** serves the travel-planning tools over SSE.

The CLI connects to both. No paid API keys are required.

## Requirements

- A copy of this repository on GitHub, or a ZIP upload.
- Google Colab notebook environment.
- Sufficient Colab RAM for the model (e.g. Qwen 2.5 7B Q4 or smaller 3B Q4).

## GPU Option

To run on GPU in Colab, change the runtime:

```text
Runtime → Change runtime type → T4 GPU
```

Check GPU availability:

```python
!nvidia-smi
```

Install llama.cpp with CUDA support:

```python
!pip uninstall -y llama-cpp-python
!CMAKE_ARGS="-DGGML_CUDA=on" pip install -q --no-cache-dir --force-reinstall "llama-cpp-python[server]"
```

Start llama.cpp on GPU:

```python
!nohup python -m llama_cpp.server \
  --model "$MODEL_PATH" \
  --model_alias qwen2.5-7b-instruct \
  --host 127.0.0.1 \
  --port 8080 \
  --n_ctx 4096 \
  --n_gpu_layers -1 \
  --chat_format chatml \
  > /tmp/llama.log 2>&1 &
```

## 1. Create a Colab Notebook

Open [colab.research.google.com](https://colab.research.google.com/) and create a new notebook, or use `colab/demo.ipynb`.

## 2. Clone the Repository

```python
!git clone https://github.com/pixelrahulnotfound/mini-ps.git
%cd mini-ps
```

For a private repository, upload a ZIP instead of putting a GitHub token in a
notebook cell:

```python
from google.colab import files
uploaded = files.upload()  # choose mini-ps.zip
```

```python
!unzip -q mini-ps.zip -d /content/
%cd /content/mini-ps
```

If the ZIP extracts into a different folder name, run `!ls /content` and change
the `%cd` path.

## 3. Install the Python dependencies

## 3. Install Dependencies

```python
!pip install -q -r requirements.txt
!CMAKE_ARGS="-DGGML_CUDA=OFF" pip install -q "llama-cpp-python[server]"
```

## 4. Download Model

```python
from huggingface_hub import hf_hub_download

MODEL_DIR = "/content/mini-ps/models"
MODEL_FILE = "qwen2.5-7b-instruct-q4_k_m.gguf"

hf_hub_download(
    repo_id="Qwen/Qwen2.5-7B-Instruct-GGUF",
    filename=MODEL_FILE,
    local_dir=MODEL_DIR,
)
```

## 5. Configure Environment

```python
import os

os.environ["MINIPS_LLM_BASE_URL"] = "http://127.0.0.1:8080/v1"
os.environ["MINIPS_LLM_API_KEY"] = "local"
os.environ["MINIPS_LLM_MODEL"] = "qwen2.5-7b-instruct"
os.environ["MINIPS_MCP_URL"] = "http://127.0.0.1:3000/sse"
os.environ["MINIPS_MAX_STEPS"] = "10"
os.environ["MINIPS_ENABLE_LIVE_DATA"] = "false"
```

## 6. Start llama.cpp Server

```python
MODEL_PATH = "/content/mini-ps/models/qwen2.5-7b-instruct-q4_k_m.gguf"

!nohup python -m llama_cpp.server \
  --model "$MODEL_PATH" \
  --host 127.0.0.1 \
  --port 8080 \
  --model_alias qwen2.5-7b-instruct \
  --n_ctx 4096 \
  --n_gpu_layers 0 \
  --chat_format chatml \
  > /tmp/llama.log 2>&1 &
```

Wait and verify server health:

```python
import time, requests

for attempt in range(30):
    try:
        response = requests.get("http://127.0.0.1:8080/v1/models", timeout=3)
        if response.ok:
            print("llama.cpp is ready")
            break
    except requests.RequestException:
        time.sleep(5)
```

## 7. Start the MCP Server

```python
!nohup python -m mcp_server.server > /tmp/mcp.log 2>&1 &
```

Verify MCP tools:

```python
import asyncio
from agent.mcp_client import MCPClient

async def check_mcp():
    async with MCPClient("http://127.0.0.1:3000/sse") as client:
        tools = await client.list_tools()
        print([tool.name for tool in tools])

asyncio.run(check_mcp())
```

## 8. Run Travel Planner

```python
!python -m cli.main --query "Plan a 5-day trip to Goa for 3 people from Hyderabad in December. Total budget: 75,000 INR. Interests: beaches, seafood, nightlife."
```

## 9. Stopping Processes

```python
!pkill -f "llama_cpp.server" || true
!pkill -f "mcp_server.server" || true
```
