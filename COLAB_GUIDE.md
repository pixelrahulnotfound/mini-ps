# Running mini-ps on Google Colab

You can run mini-ps in Google Colab in two ways:
1. **Full Colab Mode**: Run both the model and the CLI directly inside Colab.
2. **Hybrid Mode**: Run the model on Colab GPU and connect to it from your local laptop CLI via a Cloudflare Tunnel.

---

## 1. Setup GPU in Colab

1. In the top menu, go to **Runtime** → **Change runtime type**.
2. Select **T4 GPU** and click **Save**.

---

## 2. Install Dependencies (Fast)

Install the pre-built CUDA package and tunnel utility:

```python
!pip install -q huggingface_hub "llama-cpp-python[server]" \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122

!wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb > /dev/null 2>&1
```

---

## 3. Download the Model

Download the single-file Qwen 2.5 7B GGUF:

```python
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="bartowski/Qwen2.5-7B-Instruct-GGUF",
    filename="Qwen2.5-7B-Instruct-Q4_K_M.gguf",
    local_dir="/content/models"
)
print("Downloaded model to:", model_path)
```

---

## 4. Start Model Server & Cloudflare Tunnel

```python
import time

# Start llama.cpp on GPU (port 5000)
!nohup python -m llama_cpp.server \
  --model /content/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf \
  --model_alias qwen2.5-7b-instruct \
  --host 0.0.0.0 \
  --port 5000 \
  --n_ctx 4096 \
  --n_gpu_layers -1 \
  --chat_format chatml > /tmp/llama.log 2>&1 &

# Start tunnel to port 5000
!nohup cloudflared tunnel --url http://localhost:5000 > /tmp/tunnel.log 2>&1 &

time.sleep(10)
!grep -o 'https://.*\.trycloudflare\.com' /tmp/tunnel.log
```

---

## 5. Connect from Your Laptop

1. Copy the `.trycloudflare.com` URL printed in Colab.
2. On your laptop, put it in `.env`:
   ```dotenv
   MINIPS_LLM_BASE_URL=https://your-url.trycloudflare.com/v1
   MINIPS_LLM_API_KEY=local
   MINIPS_LLM_MODEL=qwen2.5-7b-instruct
   MINIPS_MCP_URL=http://localhost:3000/sse
   ```
3. Start your local MCP server:
   ```bash
   python -m mcp_server.server
   ```
4. Run the CLI on your laptop:
   ```bash
   python -m cli.main
   ```

---

## 6. (Alternative) Run Everything inside Colab

If you want to run the travel planner entirely inside Colab without a local laptop:

1. Clone the repo and install project requirements:
   ```python
   !git clone https://github.com/pixelrahulnotfound/mini-ps.git
   %cd mini-ps
   !pip install -q -r requirements.txt
   ```
2. Start the MCP server:
   ```python
   !nohup python -m mcp_server.server > /tmp/mcp.log 2>&1 &
   ```
3. Run the CLI directly:
   ```python
   import os
   os.environ["MINIPS_LLM_BASE_URL"] = "http://localhost:5000/v1"
   os.environ["MINIPS_MCP_URL"] = "http://localhost:3000/sse"

   !python -m cli.main --query "Plan a 5-day trip to Goa for 3 people from Hyderabad in December with a budget of 75000 INR."
   ```
