// ==========================================================================
// تنظیمات: آدرس API بک‌اند. اگر بک‌اند را روی پورت یا دامنه‌ی دیگری اجرا
// می‌کنید، فقط همین یک خط را تغییر دهید.
// ==========================================================================
const API_BASE_URL = "http://localhost:8000";

const SUGGESTED_QUESTIONS = [
  "شرایط ثبت‌نام در ترم جدید چیست؟",
  "آیین‌نامه‌ی آموزشی دانشگاه را خلاصه کن",
  "مراحل درخواست مرخصی تحصیلی چیست؟",
];

const chatScroll = document.getElementById("chatScroll");
const emptyState = document.getElementById("emptyState");
const suggestionRow = document.getElementById("suggestionRow");
const composerForm = document.getElementById("composerForm");
const questionInput = document.getElementById("questionInput");
const sendBtn = document.getElementById("sendBtn");

const kbDot = document.getElementById("kbDot");
const kbStatusText = document.getElementById("kbStatusText");

const toggleAdminBtn = document.getElementById("toggleAdmin");
const closeAdminBtn = document.getElementById("closeAdmin");
const adminDrawer = document.getElementById("adminDrawer");
const drawerBackdrop = document.getElementById("drawerBackdrop");

const uploadDrop = document.getElementById("uploadDrop");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const docList = document.getElementById("docList");
const docCount = document.getElementById("docCount");

let conversationHistory = [];

// ---------------------------------------------------------------------
// راه‌اندازی اولیه
// ---------------------------------------------------------------------
function init() {
  renderSuggestions();
  checkHealth();
  refreshDocuments();
  autoResizeTextarea();

  composerForm.addEventListener("submit", handleSubmit);
  questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      composerForm.requestSubmit();
    }
  });
  questionInput.addEventListener("input", autoResizeTextarea);

  toggleAdminBtn.addEventListener("click", () => setDrawer(true));
  closeAdminBtn.addEventListener("click", () => setDrawer(false));
  drawerBackdrop.addEventListener("click", () => setDrawer(false));

  uploadDrop.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => handleUpload(fileInput.files));

  ["dragover", "dragenter"].forEach((evt) =>
    uploadDrop.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadDrop.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    uploadDrop.addEventListener(evt, (e) => {
      e.preventDefault();
      uploadDrop.classList.remove("dragover");
    })
  );
  uploadDrop.addEventListener("drop", (e) => {
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files);
  });
}

function autoResizeTextarea() {
  questionInput.style.height = "auto";
  questionInput.style.height = Math.min(questionInput.scrollHeight, 160) + "px";
}

function renderSuggestions() {
  suggestionRow.innerHTML = "";
  SUGGESTED_QUESTIONS.forEach((q) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "suggestion-chip";
    chip.textContent = q;
    chip.addEventListener("click", () => {
      questionInput.value = q;
      autoResizeTextarea();
      composerForm.requestSubmit();
    });
    suggestionRow.appendChild(chip);
  });
}

// ---------------------------------------------------------------------
// وضعیت سلامت بک‌اند
// ---------------------------------------------------------------------
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (!res.ok) throw new Error("bad status");
    kbDot.className = "kb-dot online";
    kbStatusText.textContent = "متصل به سرور";
  } catch (err) {
    kbDot.className = "kb-dot offline";
    kbStatusText.textContent = "عدم اتصال به بک‌اند";
  }
}

// ---------------------------------------------------------------------
// ارسال سوال و دریافت پاسخ RAG به‌صورت استریمینگ
// ---------------------------------------------------------------------
async function handleSubmit(e) {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  emptyState.style.display = "none";
  appendMessage("user", question);
  conversationHistory.push({ role: "user", content: question });

  questionInput.value = "";
  autoResizeTextarea();
  sendBtn.disabled = true;

  const loadingEl = appendLoadingMessage();

  try {
    const res = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        history: conversationHistory.slice(-8),
      }),
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `خطای سرور (${res.status})`);
    }

    loadingEl.remove();
    const assistantMsg = createAssistantMessagePlaceholder();
    let fullAnswer = "";

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // نگه‌داشتن آخرین خط در صورت کامل‌نشدن

      for (const line of lines) {
        if (!line.trim()) continue;

        try {
          const parsed = JSON.parse(line);

          if (parsed.type === "status") {
            // نمایش گام جاری به کاربر
            assistantMsg.statusEl.textContent = parsed.data;
            assistantMsg.statusEl.style.display = "block";
          } else if (parsed.type === "sources") {
            // رندر کردن بلاک منابع در پایین حباب پاسخ
            renderSourcesBlock(assistantMsg.row, parsed.data);
          } else if (parsed.type === "text") {
            // مخفی کردن وضعیت زنده موقع شروع استریم متن
            assistantMsg.statusEl.style.display = "none";

            fullAnswer += parsed.data;
            // تبدیل عبارات [منبع X] به لینک‌های قابل کلیک
            assistantMsg.bubble.innerHTML = formatCitations(fullAnswer);
            chatScroll.scrollTop = chatScroll.scrollHeight;
          }
        } catch (e) {
          console.error("Error parsing NDJSON frame:", e, line);
        }
      }
    }

    // ذخیره پاسخ کامل در تاریخچه گفتگو
    conversationHistory.push({ role: "assistant", content: fullAnswer });
    kbDot.className = "kb-dot online";
    kbStatusText.textContent = "متصل به سرور";
  } catch (err) {
    loadingEl.remove();
    appendMessage(
      "assistant",
      `متاسفانه در دریافت پاسخ خطایی رخ داد.\nجزئیات: ${err.message}\n\nمطمئن شوید بک‌اند روی ${API_BASE_URL} در حال اجراست.`
    );
    kbDot.className = "kb-dot offline";
    kbStatusText.textContent = "عدم اتصال به بک‌اند";
  } finally {
    sendBtn.disabled = false;
    questionInput.focus();
  }
}

function appendLoadingMessage() {
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="assistant-label">دستیار دانشگاه</div>
    <div class="msg-bubble loading">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </div>`;
  chatScroll.appendChild(row);
  chatScroll.scrollTop = chatScroll.scrollHeight;
  return row;
}

// ساخت المان پیام دستیار شامل بخش وضعیت زنده
function createAssistantMessagePlaceholder() {
  const row = document.createElement("div");
  row.className = "msg-row assistant";

  const label = document.createElement("div");
  label.className = "assistant-label";
  label.textContent = "دستیار دانشگاه";
  row.appendChild(label);

  const statusEl = document.createElement("div");
  statusEl.className = "status-badge";
  statusEl.style.cssText =
    "font-size: 0.8rem; color: #888; margin-bottom: 6px; font-style: italic;";
  row.appendChild(statusEl);

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  row.appendChild(bubble);

  chatScroll.appendChild(row);
  chatScroll.scrollTop = chatScroll.scrollHeight;

  return { row, bubble, statusEl };
}

// تبدیل ارجاعات [منبع ۱] به لینک‌های کلیک‌پذیر
function formatCitations(text) {
  const escaped = escapeHtml(text);
  // جایگزینی عبارت [منبع X] یا [منبع x] با دکمه لینک
  return escaped.replace(/\[منبع\s*([۰-۹0-9]+)\]/g, (match, p1) => {
    return `<a href="javascript:void(0)" class="inline-citation" onclick="highlightSource('${p1}')">${match}</a>`;
  });
}

// اکشن کلیک روی ارجاع درون‌متنی
window.highlightSource = function (sourceNum) {
  const normalizedNum = toPersianDigits(sourceNum);
  const chips = document.querySelectorAll(".source-chip");

  chips.forEach((chip) => {
    if (chip.textContent.includes(`منبع ${normalizedNum}`)) {
      const detail = chip.nextElementSibling;
      if (detail && !detail.classList.contains("open")) {
        detail.classList.add("open");
        chip.classList.add("active");
      }
      chip.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
};

function renderSourcesBlock(rowEl, sources) {
  if (!sources || !sources.length) return;

  const sourcesBlock = document.createElement("div");
  sourcesBlock.className = "sources-block";

  sources.forEach((src, idx) => {
    const sourceWrapper = document.createElement("div");
    sourceWrapper.className = "source-item-wrapper";

    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "source-chip";
    chip.textContent = `منبع ${toPersianDigits(idx + 1)} · ${src.document_name}`;

    const detail = document.createElement("div");
    detail.className = "source-detail";

    const scorePercentage = (src.score * 100).toFixed(0);
    detail.innerHTML = `
      <div class="src-meta">
        <strong>سند:</strong> ${escapeHtml(src.document_name)} | 
        <strong>بخش:</strong> ${toPersianDigits(src.chunk_index + 1)} | 
        <strong>ارتباط:</strong> ${toPersianDigits(scorePercentage)}٪
      </div>
      <div class="src-content">${escapeHtml(src.content)}</div>
    `;

    chip.addEventListener("click", () => {
      detail.classList.toggle("open");
      chip.classList.toggle("active");
    });

    sourceWrapper.appendChild(chip);
    sourceWrapper.appendChild(detail);
    sourcesBlock.appendChild(sourceWrapper);
  });

  rowEl.appendChild(sourcesBlock);
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function appendMessage(role, text, sources) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  if (role === "assistant") {
    const label = document.createElement("div");
    label.className = "assistant-label";
    label.textContent = "دستیار دانشگاه";
    row.appendChild(label);
  }

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = role === "assistant" ? formatCitations(text) : escapeHtml(text);
  row.appendChild(bubble);

  if (sources && sources.length) {
    renderSourcesBlock(row, sources);
  }

  chatScroll.appendChild(row);
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function toPersianDigits(input) {
  if (input === undefined || input === null) return "";
  const map = { 0: "۰", 1: "۱", 2: "۲", 3: "۳", 4: "۴", 5: "۵", 6: "۶", 7: "۷", 8: "۸", 9: "۹" };
  return String(input).replace(/[0-9]/g, (d) => map[d]);
}

// ---------------------------------------------------------------------
// پنل مدیریت اسناد
// ---------------------------------------------------------------------
function setDrawer(open) {
  adminDrawer.classList.toggle("open", open);
  drawerBackdrop.classList.toggle("open", open);
}

async function refreshDocuments() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/documents`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    renderDocList(data.documents || []);
  } catch (err) {
    docList.innerHTML = `<li class="doc-empty">امکان دریافت لیست اسناد نبود.</li>`;
  }
}

function renderDocList(documents) {
  docCount.textContent = toPersianDigits(documents.length);
  docList.innerHTML = "";

  if (!documents.length) {
    docList.innerHTML = `<li class="doc-empty">هنوز سندی بارگذاری نشده است.</li>`;
    return;
  }

  documents.forEach((name) => {
    const li = document.createElement("li");
    li.className = "doc-item";
    li.innerHTML = `<span>${escapeHtml(name)}</span>`;

    const removeBtn = document.createElement("button");
    removeBtn.className = "doc-remove";
    removeBtn.type = "button";
    removeBtn.textContent = "✕";
    removeBtn.addEventListener("click", () => deleteDocument(name));

    li.appendChild(removeBtn);
    docList.appendChild(li);
  });
}

async function deleteDocument(name) {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/documents/${encodeURIComponent(name)}`,
      {
        method: "DELETE",
      }
    );
    if (!res.ok) throw new Error();
    refreshDocuments();
  } catch (err) {
    uploadStatus.innerHTML = `<span class="status-err">حذف سند «${escapeHtml(
      name
    )}» ناموفق بود.</span>`;
  }
}

async function handleUpload(fileList) {
  if (!fileList || !fileList.length) return;

  const formData = new FormData();
  Array.from(fileList).forEach((file) => formData.append("files", file));

  uploadStatus.innerHTML = `در حال پردازش ${toPersianDigits(
    fileList.length
  )} فایل…`;

  try {
    const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `خطای سرور (${res.status})`);
    }

    const data = await res.json();
    uploadStatus.innerHTML = `<span class="status-ok">${escapeHtml(
      data.message
    )}</span>`;
    refreshDocuments();
  } catch (err) {
    uploadStatus.innerHTML = `<span class="status-err">خطا در بارگذاری: ${escapeHtml(
      err.message
    )}</span>`;
  } finally {
    fileInput.value = "";
  }
}

init();