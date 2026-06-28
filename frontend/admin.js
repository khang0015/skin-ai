const detectorSelect = document.getElementById("detectorSelect");
const classifierSelect = document.getElementById("classifierSelect");
const deployChangesBtn = document.getElementById("deployChangesBtn");
const saveDefaultBtn = document.getElementById("saveDefaultBtn");
const resetDefaultBtn = document.getElementById("resetDefaultBtn");
const statusText = document.getElementById("statusText");

const activeDetector = document.getElementById("activeDetector");
const activeClassifier = document.getElementById("activeClassifier");

const llmBackendSelect = document.getElementById("llmBackendSelect");
const saveLLMBtn = document.getElementById("saveLLMBtn");
const llmActiveBackend = document.getElementById("llmActiveBackend");
const llmOllamaRow = document.getElementById("llmOllamaRow");
const llmOpenAIRow = document.getElementById("llmOpenAIRow");
const llmOpenAIStatus = document.getElementById("llmOpenAIStatus");
const llmOpenAIModel = document.getElementById("llmOpenAIModel");
const llmOllamaStatus = document.getElementById("llmOllamaStatus");
const llmOllamaModel = document.getElementById("llmOllamaModel");
const llmNote = document.getElementById("llmNote");

const knowledgeFileInput = document.getElementById("knowledgeFileInput");
const knowledgeDropzone = document.getElementById("knowledgeDropzone");
const uploadKnowledgeBtn = document.getElementById("uploadKnowledgeBtn");
const knowledgeUploadNote = document.getElementById("knowledgeUploadNote");

const chatHistoryList = document.getElementById("chatHistoryList");
const chatHistoryTotal = document.getElementById("chatHistoryTotal");
const chatHistoryPageInfo = document.getElementById("chatHistoryPageInfo");
const chatHistoryPager = document.getElementById("chatHistoryPager");
const chatHistoryPrevBtn = document.getElementById("chatHistoryPrevBtn");
const chatHistoryNextBtn = document.getElementById("chatHistoryNextBtn");
const refreshChatHistoryBtn = document.getElementById("refreshChatHistoryBtn");
const chatHistoryModal = document.getElementById("chatHistoryModal");
const closeChatHistoryModalBtn = document.getElementById("closeChatHistoryModalBtn");
const chatHistoryModalTitle = document.getElementById("chatHistoryModalTitle");
const chatHistoryModalMeta = document.getElementById("chatHistoryModalMeta");
const chatHistoryMessages = document.getElementById("chatHistoryMessages");

let selectedKnowledgeFile = null;
let chatHistoryPage = 1;
let chatHistoryTotalPages = 1;
const CHAT_HISTORY_PER_PAGE = 20;

const API_ORIGINS = [
  "",
  "http://localhost:8000",
  "http://127.0.0.1:8000",
];

window.addEventListener("error", (event) => {
  if (statusText) {
    setStatus(`Loi JavaScript: ${event.message}`, true);
  }
});

async function apiFetch(path, options) {
  let lastError = null;
  const tried = [];

  for (const origin of API_ORIGINS) {
    const url = `${origin}${path}`;
    tried.push(url || path);
    try {
      const response = await fetch(url, options);
      if (response.ok) {
        return response;
      }
      lastError = new Error(`${url || path} -> HTTP ${response.status}`);
    } catch (err) {
      lastError = err;
    }
  }

  throw new Error(`${lastError?.message || "API request failed"}; tried: ${tried.join(", ")}`);
}

function setStatus(message, isError = false) {
  if (!statusText) {
    return;
  }
  statusText.textContent = message;
  statusText.className = `status ${isError ? "error" : "success"}`;
  if (!isError) {
    setTimeout(() => {
      if (statusText.textContent === message) {
        statusText.textContent = "";
      }
    }, 4000);
  }
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function summarizeText(value, maxLength = 150) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1)}...`;
}

function fillSelect(select, items, current) {
  select.innerHTML = "";
  if (!items.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Khong co du lieu";
    select.appendChild(option);
    return;
  }
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = item === current ? `${item} (Current)` : item;
    select.appendChild(option);
  });
  if (current && items.includes(current)) {
    select.value = current;
  }
}

function renderPipeline(data) {
  activeDetector.textContent = data.detector || "-";
  activeClassifier.textContent = data.classifier || "-";

  fillSelect(detectorSelect, data.available_detectors || [], data.detector);
  fillSelect(classifierSelect, data.available_classifiers || [], data.classifier);
  setStatus(`Da tai pipeline: ${data.detector || "-"} -> ${data.classifier || "-"}`);
}

function renderPipelineFromRegistry(config) {
  const pipelines = config?.pipelines || {};
  const defaultPipeline = pipelines.default || {};
  const detectors = config?.detectors ? Object.keys(config.detectors).sort() : [];
  const classifiers = config?.classifiers ? Object.keys(config.classifiers).sort() : [];

  renderPipeline({
    detector: defaultPipeline.detector || detectors[0] || "",
    classifier: defaultPipeline.classifier || classifiers[0] || "",
    available_detectors: detectors,
    available_classifiers: classifiers,
  });
}

async function loadPipeline() {
  try {
    const res = await apiFetch("/api/admin/default-pipeline");
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Khong tai duoc pipeline (${res.status}): ${detail.slice(0, 160)}`);
    }
    renderPipeline(await res.json());
  } catch (err) {
    try {
      const fallback = await apiFetch("/api/admin/config");
      if (!fallback.ok) {
        throw err;
      }
      renderPipelineFromRegistry(await fallback.json());
      setStatus("Da tai pipeline tu registry fallback.", false);
    } catch {
      activeDetector.textContent = "Khong tai duoc";
      activeClassifier.textContent = "Khong tai duoc";
      setStatus(`Loi tai pipeline: ${err.message}`, true);
    }
  }
}

async function savePipeline() {
  const payload = {
    detector: detectorSelect.value,
    classifier: classifierSelect.value,
    classifier_input: "full",
  };

  saveDefaultBtn.disabled = true;
  if (deployChangesBtn) {
    deployChangesBtn.disabled = true;
  }
  try {
    const res = await apiFetch("/api/admin/default-pipeline", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Luu that bai");
    }
    renderPipeline(data);
    setStatus(`Da luu pipeline: ${data.detector} -> ${data.classifier}`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    saveDefaultBtn.disabled = false;
    if (deployChangesBtn) {
      deployChangesBtn.disabled = false;
    }
  }
}

saveDefaultBtn.addEventListener("click", savePipeline);
deployChangesBtn?.addEventListener("click", savePipeline);

resetDefaultBtn?.addEventListener("click", async () => {
  if (!confirm("Khoi phuc cau hinh mac dinh tu file? DB se duoc ghi de bang model_registry.json.")) {
    return;
  }

  resetDefaultBtn.disabled = true;
  try {
    const res = await apiFetch("/api/admin/default-pipeline/reset", { method: "POST" });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Reset that bai");
    }
    renderPipeline(data);
    setStatus("Da khoi phuc cau hinh tu file.");
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    resetDefaultBtn.disabled = false;
  }
});

function setKnowledgeFile(file) {
  selectedKnowledgeFile = file || null;
  knowledgeUploadNote.textContent = file
    ? `Da chon: ${file.name}`
    : "Dung luong toi da moi tep: 50MB";
}

knowledgeFileInput?.addEventListener("change", () => {
  setKnowledgeFile(knowledgeFileInput.files?.[0]);
});

["dragenter", "dragover"].forEach((eventName) => {
  knowledgeDropzone?.addEventListener(eventName, (event) => {
    event.preventDefault();
    knowledgeDropzone.classList.add("is-dragover");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  knowledgeDropzone?.addEventListener(eventName, (event) => {
    event.preventDefault();
    knowledgeDropzone.classList.remove("is-dragover");
  });
});

knowledgeDropzone?.addEventListener("drop", (event) => {
  const file = event.dataTransfer?.files?.[0];
  if (file) {
    setKnowledgeFile(file);
  }
});

uploadKnowledgeBtn.addEventListener("click", async () => {
  const file = selectedKnowledgeFile || knowledgeFileInput.files?.[0];
  if (!file) {
    setStatus("Vui long chon mot tai lieu tri thuc truoc khi upload.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  uploadKnowledgeBtn.disabled = true;
  knowledgeUploadNote.textContent = "Dang upload va refresh vector database...";

  try {
    const res = await apiFetch("/api/admin/knowledge/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Upload that bai");
    }

    selectedKnowledgeFile = null;
    knowledgeFileInput.value = "";
    knowledgeUploadNote.textContent = `Da luu ${data.filename}. Vector database hien co ${data.indexed_chunks} chunk duoc index.`;
    setStatus(`Da upload va index tai lieu tri thuc: ${data.filename}`);
  } catch (err) {
    knowledgeUploadNote.textContent = "";
    setStatus(err.message, true);
  } finally {
    uploadKnowledgeBtn.disabled = false;
  }
});

function renderChatHistory(data) {
  chatHistoryPage = data.page || 1;
  chatHistoryTotalPages = data.total_pages || 1;

  chatHistoryTotal.textContent = `${data.total || 0} đoạn chat`;
  chatHistoryPageInfo.textContent = `Trang ${chatHistoryPage}/${chatHistoryTotalPages}`;
  chatHistoryPager.textContent = `Trang ${chatHistoryPage}`;
  chatHistoryPrevBtn.disabled = chatHistoryPage <= 1;
  chatHistoryNextBtn.disabled = chatHistoryPage >= chatHistoryTotalPages;

  const items = data.items || [];
  if (!items.length) {
    chatHistoryList.innerHTML = `<p class="chat-history-empty">Chưa có đoạn chat nào.</p>`;
    return;
  }

  chatHistoryList.innerHTML = "";
  items.forEach((item) => {
    const button = document.createElement("button");
    button.className = "chat-history-item";
    button.type = "button";
    button.dataset.id = item.id;
    button.innerHTML = `
      <span class="chat-history-main">
        <strong>${escapeHtml(item.title || "Cuộc trò chuyện mới")}</strong>
        <em>${escapeHtml(summarizeText(item.summary || "Chưa có tóm tắt"))}</em>
      </span>
      <span class="chat-history-meta">
        <span>${item.message_count || 0} tin nhắn</span>
        <span>${escapeHtml(item.client_id || "-")}</span>
        <span>${formatDateTime(item.updated_at)}</span>
      </span>
    `;
    button.addEventListener("click", () => openChatHistoryModal(item.id));
    chatHistoryList.appendChild(button);
  });
}

async function loadChatHistory(page = chatHistoryPage) {
  if (!chatHistoryList) {
    return;
  }

  chatHistoryList.innerHTML = `<p class="chat-history-empty">Đang tải lịch sử chat...</p>`;
  chatHistoryPrevBtn.disabled = true;
  chatHistoryNextBtn.disabled = true;

  try {
    const res = await apiFetch(
      `/api/admin/chat-history?page=${encodeURIComponent(page)}&per_page=${CHAT_HISTORY_PER_PAGE}`,
    );
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Không tải được lịch sử chat");
    }
    renderChatHistory(data);
  } catch (err) {
    chatHistoryList.innerHTML = `<p class="chat-history-empty error">Lỗi tải lịch sử chat: ${escapeHtml(err.message)}</p>`;
  }
}

function renderChatHistoryMessages(messages) {
  if (!messages.length) {
    chatHistoryMessages.innerHTML = `<p class="chat-history-empty">Cuộc hội thoại này chưa có tin nhắn.</p>`;
    return;
  }

  chatHistoryMessages.innerHTML = "";
  messages.forEach((message) => {
    const article = document.createElement("article");
    article.className = `chat-transcript-message ${message.role === "user" ? "user" : "assistant"}`;

    const imageHtml = message.image_path
      ? `<a href="${escapeHtml(message.image_path)}" target="_blank" rel="noreferrer">
          <img src="${escapeHtml(message.image_path)}" alt="Hình ảnh" />
        </a>`
      : "";
    const analysisHtml = message.analysis_summary
      ? `<div class="chat-analysis">${escapeHtml(message.analysis_summary)}</div>`
      : "";

    article.innerHTML = `
      <div class="chat-message-head">
        <strong>${message.role === "user" ? "Người dùng" : "Chatbox"}</strong>
        <span>${formatDateTime(message.created_at)}</span>
      </div>
      ${imageHtml}
      <p>${escapeHtml(message.content)}</p>
      ${analysisHtml}
    `;
    chatHistoryMessages.appendChild(article);
  });
}

async function openChatHistoryModal(conversationId) {
  chatHistoryModal.hidden = false;
  chatHistoryModalTitle.textContent = "Đang tải lịch sử chat...";
  chatHistoryModalMeta.textContent = "";
  chatHistoryMessages.innerHTML = `<p class="chat-history-empty">Đang tải nội dung chat...</p>`;

  try {
    const res = await apiFetch(`/api/admin/chat-history/${encodeURIComponent(conversationId)}`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Không tải được nội dung chat");
    }

    const conversation = data.conversation || {};
    chatHistoryModalTitle.textContent = conversation.title || "Cuộc trò chuyện mới";
    chatHistoryModalMeta.textContent = [
      `Client: ${conversation.client_id || "-"}`,
      `${conversation.message_count || 0} tin nhắn`,
      `ập nhật: ${formatDateTime(conversation.updated_at)}`,
    ].join(" - ");
    renderChatHistoryMessages(data.messages || []);
  } catch (err) {
    chatHistoryModalTitle.textContent = "Lỗi tải nội dung chat";
    chatHistoryMessages.innerHTML = `<p class="chat-history-empty error">${escapeHtml(err.message)}</p>`;
  }
}

function closeChatHistoryModal() {
  chatHistoryModal.hidden = true;
}

refreshChatHistoryBtn?.addEventListener("click", () => loadChatHistory(chatHistoryPage));
chatHistoryPrevBtn?.addEventListener("click", () => loadChatHistory(Math.max(1, chatHistoryPage - 1)));
chatHistoryNextBtn?.addEventListener("click", () => loadChatHistory(Math.min(chatHistoryTotalPages, chatHistoryPage + 1)));
closeChatHistoryModalBtn?.addEventListener("click", closeChatHistoryModal);
chatHistoryModal?.addEventListener("click", (event) => {
  if (event.target === chatHistoryModal) {
    closeChatHistoryModal();
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && chatHistoryModal && !chatHistoryModal.hidden) {
    closeChatHistoryModal();
  }
});

function renderLLMStatus(data) {
  const backendLabels = {
    openai: "OpenAI GPT",
    ollama: "Ollama Qwen",
    none: "None",
  };

  llmActiveBackend.textContent = backendLabels[data.active_backend] || data.active_backend;
  llmActiveBackend.className = data.active_backend === "none" ? "status-error" : "status-ok";

  const selectedBackend = data.backend === "auto" ? data.active_backend : data.backend;
  const openAISelected = selectedBackend === "openai";
  const ollamaSelected = selectedBackend === "ollama";

  llmOpenAIRow?.classList.toggle("selected", openAISelected);
  llmOpenAIRow?.classList.toggle("muted", !openAISelected);
  llmOllamaRow?.classList.toggle("selected", ollamaSelected);
  llmOllamaRow?.classList.toggle("muted", !ollamaSelected);

  llmOpenAIStatus.textContent = openAISelected
    ? "SELECTED"
    : data.openai_configured
      ? "READY"
      : "INACTIVE";
  llmOpenAIStatus.className = openAISelected
    ? "status-selected"
    : data.openai_configured
      ? "status-ready"
      : "status-warn";
  llmOpenAIModel.textContent = data.openai_model || "";

  if (!data.ollama_base_url) {
    llmOllamaStatus.textContent = "INACTIVE";
    llmOllamaStatus.className = "status-warn";
    llmOllamaModel.textContent = "Can dat OLLAMA_BASE_URL trong .env";
  } else if (data.ollama_available) {
    llmOllamaStatus.textContent = ollamaSelected ? "SELECTED" : "READY";
    llmOllamaStatus.className = ollamaSelected ? "status-selected" : "status-ready";
    llmOllamaModel.textContent = data.ollama_model || "";
  } else {
    llmOllamaStatus.textContent = "INACTIVE";
    llmOllamaStatus.className = "status-error";
    llmOllamaModel.textContent = "Kiem tra tunnel watchdog.";
  }

  llmBackendSelect.value = data.backend;

  const notes = {
    openai: "OpenAI GPT se duoc dung cho moi cau tra loi RAG.",
    ollama: "Qwen 7B se duoc dung. Can SSH tunnel dang chay.",
    auto: "Tu dong: Ollama neu tunnel dang chay, khong thi fallback OpenAI.",
  };
  llmNote.textContent = notes[data.backend] || "";
}

async function loadLLMSettings() {
  try {
    const res = await apiFetch("/api/admin/llm");
    if (!res.ok) {
      throw new Error("Khong tai duoc LLM settings");
    }
    renderLLMStatus(await res.json());
  } catch (err) {
    llmNote.textContent = `Loi tai LLM settings: ${err.message}`;
  }
}

saveLLMBtn.addEventListener("click", async () => {
  const backend = llmBackendSelect.value;
  saveLLMBtn.disabled = true;
  try {
    const res = await apiFetch("/api/admin/llm", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ backend }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Loi luu LLM settings");
    }
    renderLLMStatus(data);
    setStatus(`Da chuyen LLM backend sang: ${backend}`);
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    saveLLMBtn.disabled = false;
  }
});

setStatus("Starting admin.js...");
loadPipeline();
loadLLMSettings();
loadChatHistory(1);
