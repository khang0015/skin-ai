# Skin Lesion AI Platform (Multi-Model + RAG)

This project is organized for extensibility:
- Detector/classifier are plugin-like adapters.
- Pipelines are configured in JSON, not hard-coded in API.
- You can run multiple model combinations (YOLO + different classifiers).

Current flow:
- YOLO crop -> classify each crop -> summarize findings -> RAG answer from local medical vector context.

## Project structure

```text
DA/
  backend/
    app/
      main.py
      config.py
      schemas.py
      ml/
        base.py
        types.py
        pipeline.py
        registry.py
        adapters/
          ultralytics_yolo.py
          keras_classifier.py
          pytorch_classifier.py
      models/
        vgg_vit.py
      data/
        knowledge_base.md
        model_registry.json
      services/
        rag_service.py
    models/
      yolov8s.pt
      VGG_ViT.pth
  frontend/
    index.html
    style.css
    app.js
  requirements.txt
  .env.example
```

## 1) Setup

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```env
MODEL_REGISTRY_PATH=backend/app/data/model_registry.json
APP_HOST=0.0.0.0
APP_PORT=8000
MAX_UPLOAD_SIZE_MB=10
```

## 2) Put model files

Place your files:
- `backend/models/yolov8s.pt` for YOLOv8
- `backend/models/VGG_ViT.pth` for classifier

Update paths in `backend/app/data/model_registry.json` if needed.

## 3) Configure pipelines

`backend/app/data/model_registry.json` contains 3 sections:

1. `detectors`
2. `classifiers`
3. `pipelines` (detector + classifier pairing)

Example pipeline:

```json
"default": {
  "detector": "yolo8s_best",
  "classifier": "vgg_vit"
}
```

## 4) VGG_ViT checkpoint loading

For `.pth` checkpoints, the architecture is required. Implement:
- `backend/app/models/vgg_vit.py:create_model`

Then registry points to:

```json
"model_factory": "backend.app.models.vgg_vit:create_model"
```

This allows loading `state_dict` checkpoints cleanly.

## 5) Run app

Start PostgreSQL for chat history and admin pipeline config:

```bash
docker compose up -d postgres
python scripts/init_db.py
```

Chạy backend — **phải chạy từ thư mục gốc `DA/`**, không phải từ `backend/`:

```bash
# Windows (từ D:\Code\DA)
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Hoặc dùng script có sẵn:
run.bat          # Windows CMD
.\run.ps1        # PowerShell
```

> ⚠️ **Lỗi thường gặp**: Nếu chạy `uvicorn app.main:app` từ thư mục `backend/`
> sẽ báo `ModuleNotFoundError: No module named 'app'`.
> Lý do: `.venv` và `backend/` đều nằm trong `DA/`, phải chạy từ `DA/`.

Open:
- `http://localhost:8000` for frontend
- `http://localhost:8000/admin` for pipeline admin
- `http://localhost:8000/docs` for Swagger

## 6) API usage

- `POST /api/analyze`
  - multipart fields:
    - `file`: image file
    - `pipeline`: pipeline name, example `default`
  - response includes:
    - selected `pipeline`, `detector`, `classifier`
    - detections, summary, warnings

- `POST /api/ask`
  - Semantic RAG query over local medical notes and uploaded knowledge documents.

## Chat History and Admin Config

The app uses PostgreSQL for conversation history and pipeline administration.
User login is intentionally not required. The browser creates an anonymous
`client_id` with `crypto.randomUUID()` and stores it in `localStorage`.

Database responsibilities:

```text
anonymous_clients     browser identity without auth
conversations         chat sessions per anonymous client
messages              user/assistant turns
image_analyses        stored image-analysis metadata
pipeline_presets      admin-editable pipeline presets
model_registry_configs versioned registry JSON snapshots
```

Frontend responsibilities:

```text
localStorage.skin_ai_client_id
localStorage.skin_ai_conversation_id
localStorage.skin_ai_admin_token
```

Admin route:

```text
http://localhost:8000/admin
```

Set `ADMIN_TOKEN` in `.env`, paste the same token into the admin page, then load
and edit the active registry. Saving the registry reloads the in-memory pipeline
without restarting the server.

Chat API with memory:

```text
POST /api/chat
```

The backend loads recent messages from PostgreSQL and passes them into the RAG
generator together with the current question, image-analysis summary, and
retrieved knowledge-base chunks.

## Semantic RAG knowledge base

The RAG module supports local knowledge files in these formats:

- Markdown: `.md`
- Plain text: `.txt`
- PDF: `.pdf`
- Word document: `.docx`

Place source files in:

```text
backend/app/data/docs/raw/
```

The original files stay in `docs/raw`. The application extracts text, splits it into
chunks, embeds the chunks with a local multilingual SentenceTransformer model, and
stores the vectors in a persistent Chroma collection at:

```text
backend/app/data/vector_store/
```

Recommended default embedding model:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

It is lightweight, CPU-friendly, and works for Vietnamese-English dermatology notes.
For stronger retrieval on a larger machine, use:

```text
intfloat/multilingual-e5-base
```

Download the embedding model locally:

```bash
python scripts/download_rag_model.py
```

Build or rebuild the RAG vector index:

```bash
python scripts/build_rag_index.py --reset
```

RAG flow for reporting:

```text
PDF/TXT/MD/DOCX
  -> text extraction
  -> chunking with source metadata
  -> local multilingual embedding
  -> Chroma vector store
  -> top-k semantic retrieval
  -> OpenAI answer generation
```

LangChain is intentionally not required in this version. The pipeline is explicit and
easy to explain in a graduation thesis: document loader, chunker, embedder, vector
database, retriever, prompt augmentation, and generator.

## 8) RAG LLM backend — OpenAI vs Ollama (Qwen)

Hệ thống hỗ trợ 2 LLM để sinh câu trả lời RAG, chọn qua `RAG_LLM_BACKEND` trong `.env`:

| Backend | Giá trị | Yêu cầu | Tốc độ |
|---|---|---|---|
| OpenAI GPT | `openai` | `OPENAI_API_KEY` | ~1–3s |
| Qwen 7B (Ollama) | `ollama` | SSH tunnel + `OLLAMA_BASE_URL` | ~40–90s (CPU) |
| Tự động | `auto` | — | Ollama nếu có, không thì OpenAI |

**Dùng Ollama (Qwen):**

Bước 1 — Chạy app bằng `run.bat` để tự bật tunnel watchdog, hoặc bật riêng watchdog:
```bash
start_ollama_tunnel_watchdog.bat
```

Bước 2 — Thêm vào `.env`:
```env
RAG_LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

**Lưu ý**: `RAG_LLM_BACKEND` chỉ ảnh hưởng đến phần **sinh câu trả lời RAG**.
Phần **phân tích ảnh** (detector + classifier) được chọn riêng qua trường `pipeline`
trong API request (xem mục 3 và 7).

## 9) Add new models later

1. Add model file into `backend/models/`
2. Add or implement adapter in `backend/app/ml/adapters/`
3. Register model in `backend/app/data/model_registry.json`
4. Add new pipeline mapping in the same JSON
5. Select new pipeline from frontend dropdown or API `pipeline` field

## Medical disclaimer

This tool is for research/prototyping only and does not provide diagnosis. Clinical decisions must be made by qualified healthcare professionals.
