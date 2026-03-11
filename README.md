# LLM-Coached Kubernetes Fault Diagnosis System

A self-hosted learning platform that combines intentional Kubernetes fault injection with LLM-based real-time coaching, command-level session logging, and retrieval-augmented generation (RAG) over personal documentation.


## Quick Start (Full Stack)
```bash
# 1. Clone
git clone https://github.com/zhuxi17/llm-coach.git
cd llm-coach

# 2. Python env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# 4. Environment
export DB_PATH="$HOME/.llm-coach/db.sqlite"
export SCENARIOS_DIR="$(pwd)/scenarios"
mkdir -p ~/.llm-coach

# 5. Index docs
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
curl -s -X POST http://localhost:8000/scenario/rag/index

# 6. Install kk wrapper
mkdir -p ~/.local/bin
cp scripts/kk ~/.local/bin/kk && chmod +x ~/.local/bin/kk
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# 7. Start snapshotter (separate terminal)
python3 snapshotter.py &

# 8. Open Web UI
# → http://<your-server-ip>:8000
```

### Run a scenario
```bash
export SESSION_ID=$(curl -s -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "01_image_error"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

kk get pods -n llm-coach   # logged automatically
kk coach                    # get LLM hint
```

### (Optional) Run as a persistent service
```bash
sudo tee /etc/systemd/system/llm-coach.service << 'EOF'
[Unit]
Description=LLM Coach API
After=network.target ollama.service

[Service]
User=$USER
WorkingDirectory=/home/$USER/llm-coach
Environment="DB_PATH=/home/$USER/.llm-coach/db.sqlite"
Environment="SCENARIOS_DIR=/home/$USER/llm-coach/scenarios"
ExecStart=/home/$USER/llm-coach/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now llm-coach
```

## Motivation

Operational proficiency in Kubernetes is typically acquired through repeated exposure to production incidents. This system formalizes that process by providing a structured, reproducible environment for fault diagnosis practice, augmented by a locally-deployed LLM coach that delivers contextual hints and post-session performance reviews.

## System Architecture
```
User Terminal
  └─ kk (kubectl wrapper)
       ├─ kubectl execution  →  stdout to user
       └─ POST /command/log  →  Coach API (FastAPI)
                                    ├─ SQLite  (sessions / commands / snapshots)
                                    ├─ Chroma  (RAG document index)
                                    ├─ POST /coach/hint   →  Ollama (llama3.1:8b)
                                    └─ POST /coach/report →  Ollama (llama3.1:8b)

Snapshotter (background)
  └─ every 20s: kubectl get pods/events  →  snapshots table
```

## Components

| Component | Description |
|-----------|-------------|
| **Chaos & Scenario Controller** | Applies pre-defined broken K8s manifests via `kubectl apply` |
| **Session Logger** | Records every `kk` command, output, and exit code to SQLite |
| **Cluster Snapshotter** | Periodically collects abnormal pod/event state into DB |
| **RAG Backend** | Indexes local Markdown docs with `sentence-transformers` + Chroma |
| **LLM Coach API** | FastAPI service invoking Ollama for hints and reports |
| **kk wrapper** | Bash script intercepting kubectl calls for transparent logging |

## Fault Scenarios

| ID | Title | Difficulty | Root Cause |
|----|-------|------------|------------|
| `01_image_error` | ImagePullBackOff | Easy | Non-existent image tag (`nginx:99.99.99`) |
| `02_oomkilled` | OOMKilled | Medium | Memory limit set to 4Mi |
| `03_pvc_pending` | PVC Pending | Medium | Non-existent StorageClass (`fake-storage`) |

## LLM Coaching

### Real-time Hint (`kk coach`)
Triggered on demand. The LLM receives:
- Scenario metadata (title, learning points, root cause)
- Last 10 logged commands with outputs
- Current cluster state summary (from snapshotter)
- Top-3 relevant document snippets (from RAG)

Output:
```json
{
  "summary": "Diagnosis progress in 2-3 sentences",
  "next_commands": ["kubectl ...", "..."],
  "doc_suggestions": ["relevant doc title"]
}
```

### Post-session Report (`/coach/report`)
Generated after session finish. Evaluates the full command sequence against the known root cause and solution path.

Output fields: `diagnosis_flow`, `good_points`, `improve_points`, `recommended_approach`, `reference_docs`

## Stack

- **Runtime**: Python 3.10, FastAPI, Uvicorn
- **LLM**: Ollama (`llama3.1:8b`, CPU inference)
- **Vector DB**: ChromaDB + `all-MiniLM-L6-v2` embeddings
- **Storage**: SQLite (sessions, commands, snapshots)
- **Orchestration**: Kubernetes (kubeadm)

## Quick Start
```bash
# 1. Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# 3. Configure environment
export DB_PATH="$HOME/.llm-coach/db.sqlite"
export SCENARIOS_DIR="$(pwd)/scenarios"
mkdir -p ~/.llm-coach

# 4. Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start snapshotter (separate terminal)
python3 snapshotter.py

# 6. Install kk wrapper
cp scripts/kk ~/.local/bin/kk && chmod +x ~/.local/bin/kk

# 7. Run a scenario
export SESSION_ID=$(curl -s -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{"scenario_id": "01_image_error"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

kk get pods -n llm-coach
kk coach
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/session/start` | Deploy scenario, create session |
| POST | `/session/finish` | End session, trigger cleanup |
| POST | `/command/log` | Log a kubectl command (called by kk) |
| POST | `/coach/hint` | Generate real-time LLM hint |
| POST | `/coach/report` | Generate post-session review report |
| GET  | `/scenario/` | List all available scenarios |
| POST | `/scenario/rag/index` | Index local Markdown docs |
| GET  | `/scenario/rag/search` | Search indexed documents |

## Future Work

- Web UI for session timeline visualization
- Additional fault scenarios (network policy, node taint, config map error)
- Automated evaluation metrics (TTFR, command efficiency score)
- Integration with personal experiment logs (O-RAN, SDN)
