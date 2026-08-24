// ==========================================================================
// تنظیمات: آدرس API بک‌اند. اگر بک‌اند را روی پورت یا دامنه‌ی دیگری اجرا
// می‌کنید، فقط همین یک خط را تغییر دهید.
// ==========================================================================
const API_BASE_URL = "http://localhost:8000";

const TOKEN_KEY = "access_token";

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

const logoutBtn = document.getElementById("logoutBtn");

let conversationHistory = [];
let currentUser = null;

// ========== AUTH HELPERS ==========
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

function isLoggedIn() {
    return !!getToken();
}

function authHeader() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

function authHeaders() {
    const token = getToken();
    return {
        Authorization: token ? `Bearer ${token}` : "",
        "Content-Type": "application/json",
    };
}

// ========== AUTH UI ==========
function checkAuth() {
    const modal = document.getElementById("authModal");
    if (isLoggedIn()) {
        modal.classList.remove("active");
        logoutBtn.style.display = "block";
        // Optionally fetch user info here
    } else {
        modal.classList.add("active");
        logoutBtn.style.display = "none";
        // Clear chat UI maybe
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value.trim();
    const errorEl = document.getElementById("loginError");
    errorEl.textContent = "";

    if (!username || !password) {
        errorEl.textContent = "لطفاً نام کاربری و رمز عبور را وارد کنید.";
        return;
    }

    try {
        const formData = new FormData();
        formData.append("username", username);
        formData.append("password", password);

        const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: "POST",
            body: formData,
        });

        console.log("Login response status:", res.status);

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "نام کاربری یا رمز عبور اشتباه است.");
        }

        const data = await res.json();
        console.log("Login response data:", data); // <-- see if access_token exists

        if (data.access_token) {
            setToken(data.access_token);
            console.log("Token stored:", getToken()); // <-- verify
            checkAuth();
            refreshDocuments();
        } else {
            console.error("No access_token in response");
        }
    } catch (err) {
        errorEl.textContent = err.message;
        console.error("Login error:", err);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById("registerUsername").value.trim();
    const password = document.getElementById("registerPassword").value.trim();
    const errorEl = document.getElementById("registerError");
    errorEl.textContent = "";

    if (!username || !password) {
        errorEl.textContent = "لطفاً نام کاربری و رمز عبور را وارد کنید.";
        return;
    }

    try {
        const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "ثبت‌نام ناموفق بود.");
        }

        const data = await res.json();
        setToken(data.access_token);
        checkAuth();
        refreshDocuments();
    } catch (err) {
        errorEl.textContent = err.message;
    }
}

function logout() {
    clearToken();
    checkAuth();
    // Reset conversation UI
    document.getElementById("chatScroll").innerHTML = `
    <div class="empty-state" id="emptyState">
      <div class="empty-glyph" aria-hidden="true">؟</div>
      <h2>سوال خود را درباره‌ی اسناد دانشگاه بپرسید</h2>
      <p>پاسخ‌ها فقط بر اساس اسنادی است که در پایگاه دانش این دستیار بارگذاری شده‌اند.</p>
      <div class="suggestion-row" id="suggestionRow"></div>
    </div>
  `;
    conversationHistory = [];
    renderSuggestions();
}

// ========== INIT ==========
function init() {
    renderSuggestions();
    checkAuth();
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
        }),
    );
    ["dragleave", "drop"].forEach((evt) =>
        uploadDrop.addEventListener(evt, (e) => {
            e.preventDefault();
            uploadDrop.classList.remove("dragover");
        }),
    );
    uploadDrop.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files);
    });

    // Auth events
    document
        .getElementById("loginForm")
        .addEventListener("submit", handleLogin);
    document
        .getElementById("registerForm")
        .addEventListener("submit", handleRegister);
    document.getElementById("logoutBtn").addEventListener("click", logout);

    // Tab switching
    document.getElementById("tabLogin").addEventListener("click", function () {
        document
            .querySelectorAll(".auth-tab")
            .forEach((t) => t.classList.remove("active"));
        this.classList.add("active");
        document.getElementById("loginForm").classList.add("active");
        document.getElementById("registerForm").classList.remove("active");
    });
    document
        .getElementById("tabRegister")
        .addEventListener("click", function () {
            document
                .querySelectorAll(".auth-tab")
                .forEach((t) => t.classList.remove("active"));
            this.classList.add("active");
            document.getElementById("registerForm").classList.add("active");
            document.getElementById("loginForm").classList.remove("active");
        });
}

function autoResizeTextarea() {
    questionInput.style.height = "auto";
    questionInput.style.height =
        Math.min(questionInput.scrollHeight, 160) + "px";
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

// ========== HEALTH CHECK ==========
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

// ========== CHAT ==========
async function handleSubmit(e) {
    e.preventDefault();
    if (!isLoggedIn()) {
        checkAuth();
        return;
    }

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
            headers: authHeaders(),
            body: JSON.stringify({
                question,
                history: conversationHistory.slice(-8),
            }),
        });

        if (!res.ok) {
            if (res.status === 401) {
                clearToken();
                checkAuth();
                throw new Error(
                    "نشست شما منقضی شده است. لطفاً مجدداً وارد شوید.",
                );
            }
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
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const parsed = JSON.parse(line);
                    if (parsed.type === "status") {
                        assistantMsg.statusEl.textContent = parsed.data;
                        assistantMsg.statusEl.style.display = "block";
                    } else if (parsed.type === "sources") {
                        renderSourcesBlock(assistantMsg.row, parsed.data);
                    } else if (parsed.type === "text") {
                        assistantMsg.statusEl.style.display = "none";
                        fullAnswer += parsed.data;
                        assistantMsg.bubble.innerHTML =
                            formatCitations(fullAnswer);
                        chatScroll.scrollTop = chatScroll.scrollHeight;
                    }
                } catch (e) {
                    console.error("Error parsing NDJSON frame:", e, line);
                }
            }
        }

        conversationHistory.push({ role: "assistant", content: fullAnswer });
        kbDot.className = "kb-dot online";
        kbStatusText.textContent = "متصل به سرور";
    } catch (err) {
        loadingEl.remove();
        appendMessage(
            "assistant",
            `متاسفانه در دریافت پاسخ خطایی رخ داد.\nجزئیات: ${err.message}\n\nمطمئن شوید بک‌اند روی ${API_BASE_URL} در حال اجراست.`,
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

function formatCitations(text) {
    const escaped = escapeHtml(text);
    return escaped.replace(/\[منبع\s*([۰-۹0-9]+)\]/g, (match, p1) => {
        return `<a href="javascript:void(0)" class="inline-citation" onclick="highlightSource('${p1}')">${match}</a>`;
    });
}

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
    bubble.innerHTML =
        role === "assistant" ? formatCitations(text) : escapeHtml(text);
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
    const map = {
        0: "۰",
        1: "۱",
        2: "۲",
        3: "۳",
        4: "۴",
        5: "۵",
        6: "۶",
        7: "۷",
        8: "۸",
        9: "۹",
    };
    return String(input).replace(/[0-9]/g, (d) => map[d]);
}

// ========== ADMIN PANEL ==========
function setDrawer(open) {
    adminDrawer.classList.toggle("open", open);
    drawerBackdrop.classList.toggle("open", open);
}

async function refreshDocuments() {
    if (!isLoggedIn()) return;
    try {
        const res = await fetch(`${API_BASE_URL}/api/documents`, {
            headers: authHeaders(),
        });
        if (!res.ok) {
            if (res.status === 401) {
                clearToken();
                checkAuth();
                return;
            }
            throw new Error();
        }
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
    if (!isLoggedIn()) {
        checkAuth();
        return;
    }
    try {
        const res = await fetch(
            `${API_BASE_URL}/api/documents/${encodeURIComponent(name)}`,
            {
                method: "DELETE",
                headers: authHeaders(),
            },
        );
        if (!res.ok) {
            if (res.status === 401) {
                clearToken();
                checkAuth();
                return;
            }
            throw new Error();
        }
        refreshDocuments();
    } catch (err) {
        uploadStatus.innerHTML = `<span class="status-err">حذف سند «${escapeHtml(
            name,
        )}» ناموفق بود.</span>`;
    }
}

async function handleUpload(fileList) {
    if (!fileList || !fileList.length || !isLoggedIn()) {
        if (!isLoggedIn()) checkAuth();
        return;
    }

    const formData = new FormData();
    Array.from(fileList).forEach((file) => formData.append("files", file));

    uploadStatus.innerHTML = `در حال پردازش ${toPersianDigits(
        fileList.length,
    )} فایل…`;

    try {
        const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
            method: "POST",
            headers: authHeader(), // only Authorization, no Content-Type
            body: formData,
        });

        if (!res.ok) {
            if (res.status === 401) {
                clearToken();
                checkAuth();
                throw new Error("نشست منقضی شد.");
            }
            const errBody = await res.json().catch(() => ({}));
            throw new Error(errBody.detail || `خطای سرور (${res.status})`);
        }

        const data = await res.json();
        uploadStatus.innerHTML = `<span class="status-ok">${escapeHtml(
            data.message,
        )}</span>`;
        refreshDocuments();
    } catch (err) {
        uploadStatus.innerHTML = `<span class="status-err">خطا در بارگذاری: ${escapeHtml(
            err.message,
        )}</span>`;
    } finally {
        fileInput.value = "";
    }
}

// Start the app
init();
