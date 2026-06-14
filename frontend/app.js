const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const imageInput = document.getElementById("imageInput");
const attachBtn = document.getElementById("attachBtn");
const sendBtn = document.getElementById("sendBtn");
const pipelineInput = document.getElementById("pipelineInput");
const attachmentPreview = document.getElementById("attachmentPreview");
const newChatBtn = document.getElementById("newChatBtn");
const newChatSidebarBtn = document.getElementById("newChatSidebarBtn");
const conversationList = document.getElementById("conversationList");
const refreshConversationsBtn = document.getElementById("refreshConversationsBtn");
const searchInput = document.getElementById("searchInput");
const mobileSidebarToggle = document.getElementById("mobileSidebarToggle");
const sidebarOverlay = document.getElementById("sidebarOverlay");

let selectedImageFile = null;
let selectedImageUrl = "";
let selectedImageBase64 = "";
let latestSummary = "";
let isSending = false;

const NOT_SKIN_MESSAGE = "Ảnh không được nhận dạng là ảnh da.";
const NOT_SKIN_TIP = "Tip: Để hệ thống phát hiện chính xác hơn, hãy chụp cận cảnh vùng da nghi ngờ tổn thương, đặt vùng cần khám ở giữa ảnh, đủ sáng và hạn chế nền xung quanh.";
const NO_DETECTION_MESSAGE = "Ảnh là vùng da nhưng chưa phát hiện vùng tổn thương đủ rõ để phân loại.";
const NO_DETECTION_TIP = "Tip: Hãy chụp cận cảnh hơn vùng nghi ngờ bệnh, đặt tổn thương ở giữa ảnh, đủ sáng và hạn chế rung/mờ để mô hình phát hiện chính xác hơn.";

// Mỗi lần load trang luôn bắt đầu với welcome screen (không tự khôi phục
// conversation cũ). User phải click vào item sidebar để mở lại chat cũ.
// Điều này đảm bảo: refresh = chat mới, click sidebar = chat cũ.
let currentConversationId = "";
localStorage.removeItem("skin_ai_conversation_id");

let clientId = localStorage.getItem("skin_ai_client_id");

// AbortController cho phép dừng request đang chạy (Ollama có thể mất 40-90s)
let currentAbortController = null;

const DISPLAY_TIME_ZONE = "Asia/Ho_Chi_Minh";

function zonedTimestamp(date, timeZone = DISPLAY_TIME_ZONE) {
  // Convert a Date instant into a timestamp that represents the same wall-clock
  // time in the provided IANA time zone, expressed as UTC milliseconds.
  // This lets us do day/hour/minute diffs consistently in that time zone.
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);

  const map = {};
  parts.forEach((p) => {
    if (p.type !== "literal") {
      map[p.type] = p.value;
    }
  });

  return Date.UTC(
    Number(map.year),
    Number(map.month) - 1,
    Number(map.day),
    Number(map.hour),
    Number(map.minute),
    Number(map.second),
  );
}

function formatDateInZone(date, options, timeZone = DISPLAY_TIME_ZONE) {
  return new Intl.DateTimeFormat("vi-VN", { timeZone, ...options }).format(date);
}

function parseApiDate(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Date) {
    return value;
  }
  if (typeof value === "number") {
    return new Date(value);
  }
  if (typeof value !== "string") {
    return null;
  }

  const raw = value.trim();
  if (!raw) {
    return null;
  }

  // Normalize common server formats:
  // - "YYYY-MM-DD HH:mm:ss" -> "YYYY-MM-DDTHH:mm:ss"
  // - ISO without timezone -> treat as UTC by appending "Z" to prevent UTC+7 skew.
  const normalized = raw.includes(" ") && !raw.includes("T") ? raw.replace(" ", "T") : raw;

  const hasTimeZone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(normalized);
  // Accept any fractional second length to match common DB serializers.
  const looksLikeDateTime = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(normalized);

  const candidate = looksLikeDateTime && !hasTimeZone ? `${normalized}Z` : normalized;
  const date = new Date(candidate);
  return Number.isNaN(date.getTime()) ? null : date;
}

if (!clientId) {
  clientId = crypto.randomUUID();
  localStorage.setItem("skin_ai_client_id", clientId);
}

function scrollToBottom() {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: "smooth" });
}

function openSidebar() {
  document.body.classList.add("sidebar-open");
}

function closeSidebar() {
  document.body.classList.remove("sidebar-open");
}

function autoresizeInput() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 160)}px`;
}

function createMessage(role) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "Bạn" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  article.append(avatar, bubble);
  messagesEl.appendChild(article);
  scrollToBottom();
  return bubble;
}

function addUserMessage(text, imageUrl) {
  const bubble = createMessage("user");
  if (text) {
    const pre = document.createElement("pre");
    pre.textContent = text;
    bubble.appendChild(pre);
  }
  if (imageUrl) {
    const img = document.createElement("img");
    img.className = "thumb";
    img.src = imageUrl;
    img.alt = "Ảnh người dùng đã gửi";
    bubble.appendChild(img);
  }
}

function addAssistantTyping() {
  const bubble = createMessage("assistant");
  bubble.innerHTML = `<div class="typing" aria-label="AI đang trả lời"><span></span><span></span><span></span></div>`;
  return bubble;
}

function addAssistantMessage(text, contexts = []) {
  const bubble = createMessage("assistant");
  renderTextSection(bubble, "Trả lời", text);
  renderContexts(bubble, contexts);
}

function renderTextSection(parent, title, text) {
  if (!text) {
    return;
  }
  const section = document.createElement("section");
  const heading = document.createElement("h3");
  const pre = document.createElement("pre");
  heading.textContent = title;
  pre.textContent = text;
  section.append(heading, pre);
  parent.appendChild(section);
}

function renderAnalysisImage(parent, imageUrl, detections) {
  if (!imageUrl) {
    return;
  }

  const wrap = document.createElement("div");
  wrap.className = "analysis-image";
  const img = document.createElement("img");
  const canvas = document.createElement("canvas");
  img.src = imageUrl;
  img.alt = "Ảnh phân tích với vùng phát hiện";
  wrap.append(img, canvas);
  parent.appendChild(wrap);

  img.addEventListener("load", () => {
    const rect = img.getBoundingClientRect();
    const scaleX = rect.width / img.naturalWidth;
    const scaleY = rect.height / img.naturalHeight;
    canvas.width = Math.round(rect.width);
    canvas.height = Math.round(rect.height);

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 2;
    ctx.font = "12px Be Vietnam Pro";

    (detections || []).forEach((det, idx) => {
      const [x1, y1, x2, y2] = det.bbox || [0, 0, 0, 0];
      const color = idx % 2 === 0 ? "#e11d48" : "#0f766e";
      const rx = x1 * scaleX;
      const ry = y1 * scaleY;
      const rw = Math.max(0, (x2 - x1) * scaleX);
      const rh = Math.max(0, (y2 - y1) * scaleY);
      const label = `${det.lesion_type || "unknown"} ${(det.confidence ?? 0).toFixed(2)}`;

      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.strokeRect(rx, ry, rw, rh);
      const labelWidth = Math.min(ctx.measureText(label).width + 10, canvas.width - rx);
      const labelY = Math.max(0, ry - 22);
      ctx.fillRect(rx, labelY, labelWidth, 20);
      ctx.fillStyle = "#fff";
      ctx.fillText(label, rx + 5, labelY + 14);
    });
  });
}

function renderAnalysisResult(parent, analysis, imageUrl) {
  renderAnalysisImage(parent, imageUrl, analysis.detections || []);

  if (analysis.is_skin === false) {
    renderTextSection(parent, "Kết quả phân tích ảnh", `${NOT_SKIN_MESSAGE}\n\n${NOT_SKIN_TIP}`);
    return;
  }

  if (!Array.isArray(analysis.detections) || !analysis.detections.length) {
    renderTextSection(parent, "Kết quả phân tích ảnh", `${analysis.summary || NO_DETECTION_MESSAGE}\n\n${NO_DETECTION_TIP}`);
    return;
  }

  const lines = [`Tóm tắt: ${analysis.summary || "Không có tóm tắt."}`];

  renderTextSection(parent, "Kết quả phân tích ảnh", lines.join("\n"));

  if (Array.isArray(analysis.detections) && analysis.detections.length) {
    const list = document.createElement("div");
    list.className = "result-list";
    analysis.detections.forEach((item, idx) => {
      const row = document.createElement("div");
      row.className = "result-item";
      row.textContent = `${idx + 1}. ${item.lesion_type} - độ tin cậy ${(item.confidence ?? 0).toFixed(3)}.`;
      list.appendChild(row);
    });
    parent.appendChild(list);
  }

  if (Array.isArray(analysis.warnings) && analysis.warnings.length) {
    renderTextSection(parent, "Cảnh báo", analysis.warnings.map((warn) => `- ${warn}`).join("\n"));
  }
}

function renderContexts(parent, contexts) {
  if (!Array.isArray(contexts) || !contexts.length) {
    return;
  }

  const details = document.createElement("details");
  const summary = document.createElement("summary");
  const pre = document.createElement("pre");
  summary.textContent = "Ngữ cảnh đã truy xuất";
  pre.textContent = contexts.map((ctx, idx) => `${idx + 1}. ${ctx}`).join("\n\n");
  details.append(summary, pre);
  parent.appendChild(details);
}

function setAttachment(file) {
  selectedImageFile = file;
  if (selectedImageUrl) {
    URL.revokeObjectURL(selectedImageUrl);
  }
  selectedImageUrl = URL.createObjectURL(file);

  // Convert to base64 for server persistence
  const reader = new FileReader();
  reader.onload = () => {
    selectedImageBase64 = reader.result; // data URI string
  };
  reader.readAsDataURL(file);

  attachmentPreview.hidden = false;
  attachmentPreview.innerHTML = "";

  const chip = document.createElement("div");
  chip.className = "attachment-chip";
  chip.innerHTML = `
    <img src="${selectedImageUrl}" alt="Ảnh đã chọn" />
    <span>${file.name}</span>
    <button class="remove-attachment" type="button" aria-label="Bỏ ảnh">×</button>
  `;
  attachmentPreview.appendChild(chip);
  chip.querySelector(".remove-attachment").addEventListener("click", clearAttachment);
}

function clearAttachment() {
  selectedImageFile = null;
  if (selectedImageUrl) {
    URL.revokeObjectURL(selectedImageUrl);
  }
  selectedImageUrl = "";
  selectedImageBase64 = "";
  imageInput.value = "";
  attachmentPreview.hidden = true;
  attachmentPreview.innerHTML = "";
}

async function analyzeImage(file, signal) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("pipeline", pipelineInput?.value || "default");

  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData,
    signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Phân tích ảnh thất bại");
  }
  return data;
}

async function askRag(question, analysisSummary, signal) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      analysis_summary: analysisSummary || null,
    }),
    signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Yêu cầu RAG thất bại");
  }
  return data;
}

async function chatWithMemory(message, analysisSummary, analysis, imageBase64, signal) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: clientId,
      conversation_id: currentConversationId || null,
      message,
      analysis_summary: analysisSummary || null,
      analysis: analysis || null,
      image_base64: imageBase64 || null,
    }),
    signal,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Không thể lưu và trả lời cuộc trò chuyện");
  }
  currentConversationId = data.conversation_id;
  localStorage.setItem("skin_ai_conversation_id", currentConversationId);
  return data;
}

function getDateGroup(dateStr) {
  const date = parseApiDate(dateStr);
  if (!date) {
    return "Trước đó";
  }
  const now = new Date();
  const MS_PER_DAY = 1000 * 60 * 60 * 24;
  const diffDays = Math.floor(zonedTimestamp(now) / MS_PER_DAY) - Math.floor(zonedTimestamp(date) / MS_PER_DAY);

  if (diffDays === 0) {
    return "Hôm nay";
  } else if (diffDays === 1) {
    return "Hôm qua";
  } else if (diffDays < 7) {
    return "Tuần này";
  } else if (diffDays < 30) {
    return "Tháng này";
  } else {
    return "Trước đó";
  }
}

function formatTime(dateStr) {
  const date = parseApiDate(dateStr);
  if (!date) {
    return "";
  }
  const now = new Date();
  const diffMs = zonedTimestamp(now) - zonedTimestamp(date);
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return "Vừa xong";
  if (diffMins < 60) return `${diffMins} phút trước`;
  if (diffHours < 24) return `${diffHours} giờ trước`;
  if (diffDays < 7) return `${diffDays} ngày trước`;
  return formatDateInZone(date, { day: "numeric", month: "short" });
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

async function loadConversations(searchQuery = "") {
  if (!conversationList) {
    return;
  }
  try {
    let url;
    if (searchQuery.trim()) {
      url = `/api/conversations/search?client_id=${encodeURIComponent(clientId)}&q=${encodeURIComponent(searchQuery.trim())}`;
    } else {
      url = `/api/conversations?client_id=${encodeURIComponent(clientId)}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Không thể tải lịch sử");
    }
    const conversations = await response.json();
    conversationList.innerHTML = "";

    if (!conversations.length) {
      const emptyMsg = searchQuery
        ? `Không tìm thấy kết quả cho "${escapeHtml(searchQuery)}"`
        : "Chưa có cuộc trò chuyện nào.<br>Bắt đầu bằng cách gửi tin nhắn!";
      conversationList.innerHTML = `<div class="conversation-empty">
        <div style="font-size:1.5rem;margin-bottom:8px;">💬</div>
        ${emptyMsg}
      </div>`;
      return;
    }

    // Group by date
    const groups = {};
    conversations.forEach((item) => {
      const group = getDateGroup(item.updated_at || item.created_at);
      if (!groups[group]) groups[group] = [];
      groups[group].push(item);
    });

    Object.entries(groups).forEach(([groupName, items]) => {
      const groupEl = document.createElement("div");
      groupEl.className = "conversation-date-group";
      groupEl.textContent = groupName;
      conversationList.appendChild(groupEl);

      items.forEach((item) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `conversation-item ${item.id === currentConversationId ? "active" : ""}`;

        const title = item.title || "Cuộc trò chuyện";
        const summary = item.summary || "";
        const time = formatTime(item.updated_at || item.created_at);

        button.innerHTML = `
          <div class="conversation-item-content">
            <span class="conversation-title">${escapeHtml(title)}</span>
            ${summary ? `<span class="conversation-summary">${escapeHtml(summary)}</span>` : ""}
            <span class="conversation-time">${time}</span>
          </div>
          <div class="conversation-actions">
            <button class="conv-action-btn conv-rename-btn" type="button" title="Đổi tên" aria-label="Đổi tên">✏️</button>
            <button class="conv-action-btn conv-delete-btn" type="button" title="Xóa" aria-label="Xóa">🗑️</button>
          </div>
        `;
        button.title = title;

        // Click on item content -> open conversation
        button.addEventListener("click", (e) => {
          if (e.target.closest(".conversation-actions")) return;
          openConversation(item.id);
        });

        // Rename button
        button.querySelector(".conv-rename-btn").addEventListener("click", (e) => {
          e.stopPropagation();
          renameConversation(item.id, item.title);
        });

        // Delete button
        button.querySelector(".conv-delete-btn").addEventListener("click", (e) => {
          e.stopPropagation();
          deleteConversation(item.id);
        });

        conversationList.appendChild(button);
      });
    });
  } catch {
    conversationList.innerHTML = `<div class="conversation-empty">Chưa kết nối database</div>`;
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ── Custom Modal helpers ───────────────────────────────────

const modalOverlay = document.getElementById("modalOverlay");
const modalTitle = document.getElementById("modalTitle");
const modalBody = document.getElementById("modalBody");
const modalInputEl = document.getElementById("modalInput");
const modalCancel = document.getElementById("modalCancel");
const modalConfirmBtn = document.getElementById("modalConfirm");

function showModal({ title, body, inputValue, confirmText, isDanger }) {
  return new Promise((resolve) => {
    modalTitle.textContent = title;
    modalBody.textContent = body;
    modalConfirmBtn.textContent = confirmText || "Xác nhận";
    modalConfirmBtn.className = `modal-btn ${isDanger ? "modal-btn-danger" : "modal-btn-confirm"}`;

    if (inputValue !== undefined) {
      modalInputEl.hidden = false;
      modalInputEl.value = inputValue;
    } else {
      modalInputEl.hidden = true;
    }

    modalOverlay.hidden = false;
    if (!modalInputEl.hidden) modalInputEl.focus();

    function cleanup(result) {
      modalOverlay.hidden = true;
      modalCancel.removeEventListener("click", onCancel);
      modalConfirmBtn.removeEventListener("click", onConfirm);
      modalOverlay.removeEventListener("click", onOverlay);
      resolve(result);
    }

    function onCancel() { cleanup(null); }
    function onConfirm() {
      cleanup(modalInputEl.hidden ? true : modalInputEl.value);
    }
    function onOverlay(e) { if (e.target === modalOverlay) cleanup(null); }

    modalCancel.addEventListener("click", onCancel);
    modalConfirmBtn.addEventListener("click", onConfirm);
    modalOverlay.addEventListener("click", onOverlay);
  });
}

async function renameConversation(conversationId, currentTitle) {
  const newTitle = await showModal({
    title: "Đổi tên cuộc trò chuyện",
    body: "Nhập tên mới cho cuộc trò chuyện:",
    inputValue: currentTitle || "",
    confirmText: "Lưu",
  });
  if (!newTitle || newTitle.trim() === currentTitle) return;

  try {
    await fetch(`/api/conversations/${encodeURIComponent(conversationId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: clientId, title: newTitle.trim() }),
    });
    await loadConversations(searchInput?.value || "");
  } catch {
    // silently fail
  }
}

async function deleteConversation(conversationId) {
  const confirmed = await showModal({
    title: "Xóa cuộc trò chuyện",
    body: "Bạn có chắc muốn xóa cuộc trò chuyện này? Hành động này không thể hoàn tác.",
    confirmText: "Xóa",
    isDanger: true,
  });
  if (!confirmed) return;

  try {
    await fetch(
      `/api/conversations/${encodeURIComponent(conversationId)}?client_id=${encodeURIComponent(clientId)}`,
      { method: "DELETE" },
    );
    if (currentConversationId === conversationId) {
      startNewChat();
    }
    await loadConversations(searchInput?.value || "");
  } catch {
    // silently fail
  }
}

async function openConversation(conversationId) {
  const response = await fetch(
    `/api/conversations/${encodeURIComponent(conversationId)}/messages?client_id=${encodeURIComponent(clientId)}`,
  );
  if (!response.ok) {
    return;
  }
  const messages = await response.json();
  currentConversationId = conversationId;
  localStorage.setItem("skin_ai_conversation_id", currentConversationId);
  messagesEl.innerHTML = "";
  messages.forEach((message) => {
    if (message.role === "user") {
      // Show user text + user image if saved
      addUserMessage(message.content, message.image_path || "");
    } else if (message.role === "assistant") {
      const ia = message.metadata?.image_analysis;
      if (ia) {
        // This assistant message has image analysis — render full analysis view
        const bubble = createMessage("assistant");
        // Show bounding-box image if available (saved by backend)
        if (message.image_path) {
          const analysisWrap = document.createElement("div");
          analysisWrap.className = "analysis-image";
          const img = document.createElement("img");
          img.src = message.image_path;
          img.alt = "Ảnh phân tích với vùng phát hiện";
          analysisWrap.appendChild(img);
          bubble.appendChild(analysisWrap);
        }
        renderAnalysisResult(bubble, ia, "");
        if (ia.is_skin === false) {
          return;
        }
        // Render AI text answer
        renderTextSection(bubble, "Trao đổi thêm", message.content);
        renderContexts(bubble, message.metadata?.contexts || []);
      } else {
        addAssistantMessage(message.content, message.metadata?.contexts || []);
      }
    }
  });
  await loadConversations(searchInput?.value || "");
  scrollToBottom();
  closeSidebar();
}

async function handleSend(event) {
  event.preventDefault();
  if (isSending) {
    return;
  }

  const text = messageInput.value.trim();
  const file = selectedImageFile;
  const imageUrlForMessage = file ? URL.createObjectURL(file) : "";
  // Capture base64 BEFORE clearAttachment() resets it
  const imageBase64ForChat = selectedImageBase64 || "";
  if (!text && !file) {
    return;
  }

  const userText = text || "Hãy phân tích ảnh này giúp tôi.";
  addUserMessage(userText, imageUrlForMessage);
  messageInput.value = "";
  autoresizeInput();
  clearAttachment();

  // ── Hiện loading ba chấm ngay lập tức ──────────────────
  // Capture the message count BEFORE addUserMessage to know if this is a fresh chat.
  // The static welcome message has data-welcome="true" so we can ignore it.
  const hasRealMessagesBeforeSend = Array.from(
    messagesEl.querySelectorAll(".message")
  ).some((el) => el.dataset.welcome !== "true");

  const assistantBubble = addAssistantTyping();
  isSending = true;
  sendBtn.disabled = true;

  // ── Sidebar logic ───────────────────────────────────────
  // Add temp item to sidebar ONLY when this is genuinely a new chat:
  //   - currentConversationId is empty (no chat selected) AND
  //   - no real messages yet (only the welcome screen)
  // This prevents the temp item from appearing when user is in an old chat
  // but currentConversationId got cleared by some edge case.
  const isNewChat = !currentConversationId && !hasRealMessagesBeforeSend;
  if (isNewChat) {
    const tempTitle = userText.slice(0, 60) || "Cuộc trò chuyện mới";
    _upsertSidebarItem({
      id: PENDING_ID,
      title: tempTitle,
      isPending: true,
    });
  }

  try {
    assistantBubble.innerHTML = `<div class="typing" aria-label="AI đang trả lời"><span></span><span></span><span></span></div>`;
    let analysis = null;
    let summaryForRag = latestSummary;

    if (file) {
      assistantBubble.innerHTML = `
        <div class="typing-label">
          <div class="typing" aria-label="Đang phân tích ảnh"><span></span><span></span><span></span></div>
          <span class="typing-text">Đang phân tích ảnh...</span>
        </div>`;
      analysis = await analyzeImage(file);
      latestSummary = analysis.summary || "";
      summaryForRag = latestSummary;
      assistantBubble.innerHTML = "";
      renderAnalysisResult(assistantBubble, analysis, imageUrlForMessage);
      if (analysis.is_skin === false) {
        latestSummary = "";
        summaryForRag = "";
        document.querySelector(`.conversation-item[data-id="${PENDING_ID}"]`)?.remove();
        return;
      }
      if (!Array.isArray(analysis.detections) || !analysis.detections.length) {
        latestSummary = "";
        summaryForRag = "";
        document.querySelector(`.conversation-item[data-id="${PENDING_ID}"]`)?.remove();
        return;
      }
      // Cập nhật loading cho bước RAG
      const ragLoader = document.createElement("div");
      ragLoader.className = "typing-label";
      ragLoader.innerHTML = `<div class="typing"><span></span><span></span><span></span></div><span class="typing-text">Đang tìm kiếm thông tin...</span>`;
      assistantBubble.appendChild(ragLoader);
    }

    let rag;
    try {
      rag = await chatWithMemory(userText, summaryForRag, analysis, imageBase64ForChat);
    } catch {
      rag = await askRag(userText, summaryForRag);
    }

    // Xóa MỌI loading indicator (cả .typing và .typing-label) trước khi render answer
    assistantBubble.querySelectorAll(".typing, .typing-label").forEach((el) => el.remove());

    renderTextSection(assistantBubble, file ? "Trao đổi thêm" : "Trả lời", rag.answer || "Chưa có câu trả lời phù hợp.");
    renderContexts(assistantBubble, rag.contexts);

    // Cập nhật sidebar với dữ liệu thật từ server
    await loadConversations(searchInput?.value || "");
  } catch (error) {
    assistantBubble.innerHTML = "";
    renderTextSection(assistantBubble, "Lỗi", error.message || "Không thể xử lý yêu cầu.");
    // Xóa item tạm chỉ khi là chat mới và lỗi (chưa nhận được conversation_id thật)
    if (isNewChat && !currentConversationId) {
      document.querySelector(`.conversation-item[data-id="${PENDING_ID}"]`)?.remove();
    }
  } finally {
    isSending = false;
    sendBtn.disabled = false;
    scrollToBottom();
  }
}

const PENDING_ID = "__pending__";

/**
 * Thêm hoặc cập nhật một item trong sidebar ngay lập tức (optimistic UI).
 * Nếu id đã tồn tại → cập nhật title/time.
 * Nếu chưa tồn tại → thêm vào đầu danh sách dưới nhóm "Hôm nay".
 */
function _upsertSidebarItem({ id, title, updated_at, isPending }) {
  if (!conversationList) return;

  // Nếu đã có item này → chỉ đánh dấu active
  const existing = conversationList.querySelector(`.conversation-item[data-id="${id}"]`);
  if (existing) {
    conversationList.querySelectorAll(".conversation-item").forEach((el) => el.classList.remove("active"));
    existing.classList.add("active");
    return;
  }

  // Xóa trạng thái empty nếu có
  conversationList.querySelector(".conversation-empty")?.remove();

  // Tìm hoặc tạo nhóm "Hôm nay"
  let todayGroup = Array.from(conversationList.querySelectorAll(".conversation-date-group"))
    .find((el) => el.textContent.trim() === "Hôm nay");

  if (!todayGroup) {
    todayGroup = document.createElement("div");
    todayGroup.className = "conversation-date-group";
    todayGroup.textContent = "Hôm nay";
    conversationList.prepend(todayGroup);
  }

  // Tạo button item
  const button = document.createElement("button");
  button.type = "button";
  button.className = "conversation-item active";
  button.dataset.id = id;
  button.innerHTML = `
    <div class="conversation-item-content">
      <span class="conversation-title">${escapeHtml(title || "Cuộc trò chuyện mới")}</span>
      ${isPending ? '<span class="conversation-summary typing-inline"><span></span><span></span><span></span></span>' : ""}
      <span class="conversation-time">Vừa xong</span>
    </div>
    <div class="conversation-actions">
      <button class="conv-action-btn conv-rename-btn" type="button" title="Đổi tên" aria-label="Đổi tên">✏️</button>
      <button class="conv-action-btn conv-delete-btn" type="button" title="Xóa" aria-label="Xóa">🗑️</button>
    </div>
  `;

  // Bỏ active các item khác
  conversationList.querySelectorAll(".conversation-item").forEach((el) => el.classList.remove("active"));

  // Chèn ngay sau nhóm "Hôm nay"
  todayGroup.insertAdjacentElement("afterend", button);

  // Wire up click events
  button.addEventListener("click", (e) => {
    if (e.target.closest(".conversation-actions")) return;
    if (id !== PENDING_ID) openConversation(id);
  });
  button.querySelector(".conv-rename-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    if (id !== PENDING_ID) renameConversation(id, title);
  });
  button.querySelector(".conv-delete-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    if (id !== PENDING_ID) deleteConversation(id);
  });
}

attachBtn.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", () => {
  const file = imageInput.files?.[0];
  if (file) {
    setAttachment(file);
  }
});

chatForm.addEventListener("submit", handleSend);

messageInput.addEventListener("input", autoresizeInput);

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

// Search conversations
if (searchInput) {
  searchInput.addEventListener(
    "input",
    debounce(() => {
      loadConversations(searchInput.value);
    }, 300),
  );
}

function startNewChat() {
  latestSummary = "";
  currentConversationId = "";
  localStorage.removeItem("skin_ai_conversation_id");
  clearAttachment();
  closeSidebar();
  messagesEl.innerHTML = `
    <article class="message assistant" data-welcome="true">
      <div class="avatar" aria-hidden="true">AI</div>
      <div class="bubble">
        <p>Chào bạn. Bạn có thể mô tả triệu chứng hoặc gửi ảnh vùng da cần phân tích.</p>
      </div>
    </article>
  `;
  messageInput.focus();
  loadConversations();
}

newChatBtn.addEventListener("click", startNewChat);
newChatSidebarBtn?.addEventListener("click", startNewChat);
mobileSidebarToggle?.addEventListener("click", openSidebar);
sidebarOverlay?.addEventListener("click", closeSidebar);

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeSidebar();
  }
});

refreshConversationsBtn?.addEventListener("click", () => loadConversations(searchInput?.value || ""));

autoresizeInput();
loadConversations();
