// ── DOM elements ──────────────────────────────────────────────────────
const detectorSelect = document.getElementById("detectorSelect");
const classifierSelect = document.getElementById("classifierSelect");
const classifierInputSelect = document.getElementById("classifierInputSelect");
const saveDefaultBtn = document.getElementById("saveDefaultBtn");
const resetDefaultBtn = document.getElementById("resetDefaultBtn");
const statusText = document.getElementById("statusText");

const activeDetector = document.getElementById("activeDetector");
const activeClassifier = document.getElementById("activeClassifier");
const activeInputMode = document.getElementById("activeInputMode");

const llmBackendSelect = document.getElementById("llmBackendSelect");
const saveLLMBtn = document.getElementById("saveLLMBtn");
const llmActiveBackend = document.getElementById("llmActiveBackend");
const llmOpenAIStatus = document.getElementById("llmOpenAIStatus");
const llmOpenAIModel = document.getElementById("llmOpenAIModel");
const llmOllamaStatus = document.getElementById("llmOllamaStatus");
const llmOllamaModel = document.getElementById("llmOllamaModel");
const llmNote = document.getElementById("llmNote");

const knowledgeFileInput = document.getElementById("knowledgeFileInput");
const uploadKnowledgeBtn = document.getElementById("uploadKnowledgeBtn");
const knowledgeUploadNote = document.getElementById("knowledgeUploadNote");

// ── Helpers ──────────────────────────────────────────────────────────

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.className = `status ${isError ? "error" : "success"}`;
  if (!isError) {
    setTimeout(() => {
      if (statusText.textContent === message) statusText.textContent = "";
    }, 4000);
  }
}

function fillSelect(select, items, current) {
  select.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = item;
    select.appendChild(option);
  });
  if (current && items.includes(current)) {
    select.value = current;
  }
}

// ── Pipeline (detector + classifier + input) ─────────────────────────

function renderPipeline(data) {
  // Active banner
  activeDetector.textContent = data.detector || "—";
  activeClassifier.textContent = data.classifier || "—";
  activeInputMode.textContent = data.classifier_input || "—";

  // Selects
  fillSelect(detectorSelect, data.available_detectors || [], data.detector);
  fillSelect(classifierSelect, data.available_classifiers || [], data.classifier);
  fillSelect(classifierInputSelect, data.available_inputs || ["full", "crop"], data.classifier_input);
}

async function loadPipeline() {
  try {
    const res = await fetch("/api/admin/default-pipeline");
    if (!res.ok) throw new Error("Không tải được pipeline");
    const data = await res.json();
    renderPipeline(data);
  } catch (err) {
    setStatus("Lỗi tải pipeline: " + err.message, true);
  }
}

saveDefaultBtn.addEventListener("click", async () => {
  const payload = {
    detector: detectorSelect.value,
    classifier: classifierSelect.value,
    classifier_input: classifierInputSelect.value,
  };

  saveDefaultBtn.disabled = true;
  try {
    const res = await fetch("/api/admin/default-pipeline", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lưu thất bại");
    renderPipeline(data);
    setStatus(`✓ Đã lưu pipeline: ${data.detector} → ${data.classifier} (${data.classifier_input})`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    saveDefaultBtn.disabled = false;
  }
});

resetDefaultBtn.addEventListener("click", async () => {
  if (!confirm("Khôi phục cấu hình mặc định từ file? DB sẽ được ghi đè bằng model_registry.json.")) return;
  resetDefaultBtn.disabled = true;
  try {
    const res = await fetch("/api/admin/default-pipeline/reset", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Reset thất bại");
    renderPipeline(data);
    setStatus("✓ Đã khôi phục cấu hình từ file.");
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    resetDefaultBtn.disabled = false;
  }
});

uploadKnowledgeBtn.addEventListener("click", async () => {
  const file = knowledgeFileInput.files && knowledgeFileInput.files[0];
  if (!file) {
    setStatus("Vui lòng chọn một tài liệu tri thức trước khi upload.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  uploadKnowledgeBtn.disabled = true;
  knowledgeUploadNote.textContent = "Đang upload và refresh vector database...";

  try {
    const res = await fetch("/api/admin/knowledge/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload thất bại");

    knowledgeFileInput.value = "";
    knowledgeUploadNote.textContent = `Đã lưu ${data.filename}. Vector database hiện có ${data.indexed_chunks} chunk được index.`;
    setStatus(`✓ Đã upload và index tài liệu tri thức: ${data.filename}`);
  } catch (err) {
    knowledgeUploadNote.textContent = "";
    setStatus(err.message, true);
  } finally {
    uploadKnowledgeBtn.disabled = false;
  }
});

// ── LLM backend ──────────────────────────────────────────────────────

function renderLLMStatus(data) {
  const backendLabels = {
    openai: "OpenAI GPT",
    ollama: "Ollama · Qwen",
    none: "Không có",
  };
  llmActiveBackend.textContent = backendLabels[data.active_backend] || data.active_backend;
  llmActiveBackend.className = "active-value " + (data.active_backend === "none" ? "status-error" : "status-ok");

  llmOpenAIStatus.textContent = data.openai_configured ? "✓ Đã cấu hình" : "✗ Chưa có API key";
  llmOpenAIStatus.className = "active-value " + (data.openai_configured ? "status-ok" : "status-warn");
  llmOpenAIModel.textContent = data.openai_model || "";

  if (!data.ollama_base_url) {
    llmOllamaStatus.textContent = "✗ Chưa cấu hình";
    llmOllamaStatus.className = "active-value status-warn";
    llmOllamaModel.textContent = "Cần đặt OLLAMA_BASE_URL trong .env";
  } else if (data.ollama_available) {
    llmOllamaStatus.textContent = "✓ Đang chạy";
    llmOllamaStatus.className = "active-value status-ok";
    llmOllamaModel.textContent = data.ollama_model || "";
  } else {
    llmOllamaStatus.textContent = "✗ Không kết nối được";
    llmOllamaStatus.className = "active-value status-error";
    llmOllamaModel.textContent = "Kiểm tra tunnel watchdog: run.bat hoặc start_ollama_tunnel_watchdog.bat";
  }

  llmBackendSelect.value = data.backend;

  const notes = {
    openai: "OpenAI GPT sẽ được dùng cho mọi câu trả lời RAG.",
    ollama: "Qwen 7B (Azure VM) sẽ được dùng. Cần SSH tunnel đang chạy.",
    auto: "Tự động: Ollama nếu tunnel đang chạy, không thì fallback OpenAI.",
  };
  llmNote.textContent = notes[data.backend] || "";
}

async function loadLLMSettings() {
  try {
    const res = await fetch("/api/admin/llm");
    if (!res.ok) throw new Error("Không tải được LLM settings");
    renderLLMStatus(await res.json());
  } catch (err) {
    llmNote.textContent = "Lỗi tải LLM settings: " + err.message;
  }
}

saveLLMBtn.addEventListener("click", async () => {
  const backend = llmBackendSelect.value;
  saveLLMBtn.disabled = true;
  try {
    const res = await fetch("/api/admin/llm", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ backend }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Lỗi lưu LLM settings");
    renderLLMStatus(data);
    setStatus(`✓ Đã chuyển LLM backend sang: ${backend}`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    saveLLMBtn.disabled = false;
  }
});

// ── Init ─────────────────────────────────────────────────────────────

loadPipeline();
loadLLMSettings();
