// ==========================================================================
// تنظیمات
// ==========================================================================
const API_BASE_URL = "http://localhost:8000";
const TOKEN_KEY = "access_token";
const USERNAME_KEY = "username";
const CHAT_DATA_KEY = "chat_data_"; // will append username

const SUGGESTED_QUESTIONS = [
    "شرایط ثبت‌نام در ترم جدید چیست؟",
    "آیین‌نامه‌ی آموزشی دانشگاه را خلاصه کن",
    "مراحل درخواست مرخصی تحصیلی چیست؟",
];

// DOM references
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

// Sidebar elements
const sidebar = document.getElementById("sidebar");
const convList = document.getElementById("convList");
const newChatBtn = document.getElementById("newChatBtn");
const closeSidebarBtn = document.getElementById("closeSidebar");
const toggleSidebarBtn = document.getElementById("toggleSidebar");

// State
let conversations = [];
let currentConvId = null;
let currentMessages = []; // reference to messages of current conversation
let currentUser = null;

// ========== STORAGE ==========
function getChatDataKey() {
    const username = localStorage.getItem(USERNAME_KEY);
    if (!username) return null;
    return `${CHAT_DATA_KEY}${username}`;
}

function loadUserData() {
    const key = getChatDataKey();
    if (!key) return null;
    try {
        const raw = localStorage.getItem(key);
        if (raw) {
            const data = JSON.parse(raw);
            if (
                data &&
                data.conversations &&
                Array.isArray(data.conversations)
            ) {
                return data;
            }
        }
    } catch (e) {
        console.warn("Failed to load chat data:", e);
    }
    return null;
}

function saveUserData() {
    const key = getChatDataKey();
    if (!key) return;
    const data = {
        conversations: conversations,
        currentId: currentConvId,
    };
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (e) {
        console.warn("Failed to save chat data:", e);
    }
}

function loadConversations() {
    const data = loadUserData();
    if (data) {
        conversations = data.conversations || [];
        currentConvId = data.currentId || null;
        // Ensure currentConvId is valid, otherwise fall back to the first conversation
        if (
            currentConvId &&
            !conversations.find((c) => c.id === currentConvId)
        ) {
            currentConvId = null;
        }
        if (!currentConvId && conversations.length > 0) {
            currentConvId = conversations[0].id;
        }
        // If there are no conversations at all, that's fine – the start
        // screen (empty state) will be shown instead of forcing a new one.
    } else {
        conversations = [];
        currentConvId = null;
        saveUserData();
    }
    // Set currentMessages to the messages of the active conversation
    const conv = conversations.find((c) => c.id === currentConvId);
    currentMessages = conv ? conv.messages : [];
    return conv;
}

function createNewConversation(save = true) {
    const id = `conv_${Date.now()}`;
    const title = `گفتگوی جدید (${conversations.length + 1})`;
    const newConv = {
        id,
        title,
        messages: [],
        createdAt: new Date().toISOString(),
    };
    conversations.push(newConv);
    currentConvId = id;
    currentMessages = newConv.messages;
    if (save) saveUserData();
    renderConversationList();
    renderChatMessages();
    return newConv;
}

function deleteConversation(id) {
    const target = conversations.find((c) => c.id === id);
    const title = target ? target.title : "این گفتگو";

    openConfirmModal(`آیا از حذف «${title}» مطمئن هستید؟ این عملیات قابل بازگشت نیست.`, () => {
        const idx = conversations.findIndex((c) => c.id === id);
        if (idx === -1) return;
        conversations.splice(idx, 1);
        if (currentConvId === id) {
            if (conversations.length > 0) {
                currentConvId = conversations[0].id;
                const conv = conversations.find((c) => c.id === currentConvId);
                currentMessages = conv ? conv.messages : [];
            } else {
                // No conversations left – show the start screen.
                currentConvId = null;
                currentMessages = [];
            }
        }
        saveUserData();
        renderConversationList();
        renderChatMessages();
    });
}

function switchConversation(id) {
    const conv = conversations.find((c) => c.id === id);
    if (!conv) return;
    currentConvId = id;
    currentMessages = conv.messages;
    saveUserData();
    renderChatMessages();
    renderConversationList();
    // Close sidebar on mobile if needed
    if (window.innerWidth < 768) {
        sidebar.classList.remove("open");
    }
}

function renameConversation(id, newTitle) {
    const conv = conversations.find((c) => c.id === id);
    if (!conv) return;
    conv.title = newTitle.trim() || "گفتگو";
    saveUserData();
    renderConversationList();
}

function getCurrentConv() {
    return conversations.find((c) => c.id === currentConvId);
}

// ========== RENDER CHAT UI ==========
function renderChatMessages() {
    // Clear chatScroll but keep emptyState and suggestionRow? Actually we need to remove all children except emptyState
    // We'll rebuild the chat area based on currentMessages
    // Remove all child nodes from chatScroll except emptyState (which might be hidden)
    // Simpler: clear chatScroll, then append messages, then re-append emptyState if needed
    const chatScroll = document.getElementById("chatScroll");
    // Store emptyState reference
    const emptyState = document.getElementById("emptyState");
    const suggestionRow = document.getElementById("suggestionRow");

    // Clear all children
    while (chatScroll.firstChild) {
        chatScroll.removeChild(chatScroll.firstChild);
    }

    if (!currentMessages || currentMessages.length === 0) {
        // Show empty state
        chatScroll.appendChild(emptyState);
        emptyState.style.display = "block";

        const emptyTitle = document.getElementById("emptyTitle");
        const emptyDesc = document.getElementById("emptyDesc");

        if (conversations.length === 0) {
            // True start screen – no chats exist yet at all
            emptyState.classList.remove("compact");
            emptyTitle.textContent = "سوال خود را درباره‌ی اسناد دانشگاه بپرسید";
            emptyDesc.textContent =
                "پاسخ‌ها فقط بر اساس اسنادی است که در پایگاه دانش این دستیار بارگذاری شده‌اند.";
            suggestionRow.style.display = "flex";
            renderSuggestions();
        } else {
            // A fresh, empty conversation (e.g. just started via "New chat")
            emptyState.classList.add("compact");
            emptyTitle.textContent = "گفتگوی جدید";
            emptyDesc.textContent = "سوال خود را بنویسید تا گفتگو آغاز شود.";
            suggestionRow.style.display = "none";
            suggestionRow.innerHTML = "";
        }
        return;
    }

    emptyState.style.display = "none";
    // Re-render all messages from currentMessages
    currentMessages.forEach((msg) => {
        appendMessage(msg.role, msg.content, null, false);
    });
    chatScroll.scrollTop = chatScroll.scrollHeight;
}

// Override appendMessage to also save to currentMessages when save=true
function appendMessage(role, text, sources, save = true) {
    // Create DOM row
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

    if (save) {
        // Add to currentMessages if not already present (avoid duplicates)
        // We'll check if last message matches to prevent double-save
        const last = currentMessages.length
            ? currentMessages[currentMessages.length - 1]
            : null;
        if (last && last.role === role && last.content === text) {
            // already there, just update sources maybe
        } else {
            currentMessages.push({ role, content: text });
            // If this is the first user message, update conversation title
            if (role === "user" && currentMessages.length === 1) {
                const conv = getCurrentConv();
                if (conv) {
                    let title = text.slice(0, 30);
                    if (title.length < text.length) title += "...";
                    conv.title = title;
                }
            }
            saveUserData();
            renderConversationList(); // update title
        }
    }
}

// Helper to update messages after streaming (called from handleSubmit)
function addAssistantMessage(text) {
    currentMessages.push({ role: "assistant", content: text });
    saveUserData();
    renderConversationList(); // in case title changed
}

// ========== RENDER SIDEBAR ==========
function renderConversationList() {
    convList.innerHTML = "";
    if (!conversations || conversations.length === 0) {
        convList.innerHTML =
            '<li class="conv-empty">هیچ گفتگویی وجود ندارد.</li>';
        return;
    }
    conversations.forEach((conv) => {
        const li = document.createElement("li");
        li.className = "conv-item";
        if (conv.id === currentConvId) {
            li.classList.add("active");
        }
        const titleSpan = document.createElement("span");
        titleSpan.textContent = conv.title || "گفتگو";
        li.appendChild(titleSpan);

        const actions = document.createElement("div");
        actions.className = "conv-actions";

        const renameBtn = document.createElement("button");
        renameBtn.className = "conv-btn";
        renameBtn.type = "button";
        renameBtn.title = "تغییر نام";
        renameBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M16.5 4.5l3 3L7 20H4v-3L16.5 4.5Z" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
        renameBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            startRenameConversation(li, conv);
        });
        actions.appendChild(renameBtn);

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "conv-btn conv-btn-delete";
        deleteBtn.type = "button";
        deleteBtn.title = "حذف";
        deleteBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-9 0v12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V7" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 11v6M14 11v6" stroke-linecap="round"/></svg>`;
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        });
        actions.appendChild(deleteBtn);

        li.appendChild(actions);
        li.addEventListener("click", () => switchConversation(conv.id));
        convList.appendChild(li);
    });
}

// ========== INLINE RENAME ==========
function startRenameConversation(li, conv) {
    if (li.classList.contains("renaming")) return;
    li.classList.add("renaming");
    li.innerHTML = "";

    const input = document.createElement("input");
    input.type = "text";
    input.className = "conv-rename-input";
    input.value = conv.title || "";
    li.appendChild(input);

    let settled = false;
    const finish = (shouldSave) => {
        if (settled) return;
        settled = true;
        if (shouldSave) {
            renameConversation(conv.id, input.value);
        } else {
            renderConversationList();
        }
    };

    input.addEventListener("click", (e) => e.stopPropagation());
    input.addEventListener("keydown", (e) => {
        e.stopPropagation();
        if (e.key === "Enter") {
            e.preventDefault();
            finish(true);
        } else if (e.key === "Escape") {
            e.preventDefault();
            finish(false);
        }
    });
    input.addEventListener("blur", () => finish(true));

    input.focus();
    input.select();
}

// ========== CONFIRM MODAL ==========
const confirmModal = document.getElementById("confirmModal");
const confirmModalMessage = document.getElementById("confirmModalMessage");
const confirmModalCancelBtn = document.getElementById("confirmModalCancel");
const confirmModalConfirmBtn = document.getElementById("confirmModalConfirm");
let confirmModalCallback = null;

function openConfirmModal(message, onConfirm) {
    confirmModalMessage.textContent = message;
    confirmModalCallback = onConfirm;
    confirmModal.classList.add("active");
}

function closeConfirmModal() {
    confirmModal.classList.remove("active");
    confirmModalCallback = null;
}

confirmModalCancelBtn.addEventListener("click", closeConfirmModal);
confirmModalConfirmBtn.addEventListener("click", () => {
    const cb = confirmModalCallback;
    closeConfirmModal();
    if (cb) cb();
});
confirmModal.addEventListener("click", (e) => {
    if (e.target === confirmModal) closeConfirmModal();
});

// ========== AUTH HELPERS ==========
function getToken() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token || token === "null" || token === "undefined") return null;
    return token.trim();
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token.trim());
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

function getUsername() {
    return localStorage.getItem(USERNAME_KEY);
}

function setUsername(username) {
    localStorage.setItem(USERNAME_KEY, username);
}

function clearUsername() {
    localStorage.removeItem(USERNAME_KEY);
}

function isLoggedIn() {
    return !!getToken();
}

function authHeaders() {
    const token = getToken();
    const headers = { "Content-Type": "application/json" };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
}

function authHeader() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

// ========== AUTH UI ==========
function checkAuth() {
    const modal = document.getElementById("authModal");
    if (isLoggedIn()) {
        modal.classList.remove("active");
        logoutBtn.style.display = "block";
        // Load user conversations
        loadConversations();
        renderChatMessages();
        renderConversationList();
    } else {
        modal.classList.add("active");
        logoutBtn.style.display = "none";
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

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "نام کاربری یا رمز عبور اشتباه است.");
        }

        const data = await res.json();
        if (data.access_token) {
            setToken(data.access_token);
            setUsername(username);
            checkAuth();
            refreshDocuments();
            // Load conversations is called inside checkAuth
        }
    } catch (err) {
        errorEl.textContent = err.message;
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
        if (data.access_token) {
            setToken(data.access_token);
            setUsername(username);
            checkAuth();
            refreshDocuments();
        }
    } catch (err) {
        errorEl.textContent = err.message;
    }
}

function logout() {
    clearToken();
    clearUsername();
    // DO NOT clear chat data – it stays per user
    // Reset UI
    location.reload();
}

// ========== CHAT SUBMISSION ==========
async function handleSubmit(e) {
    e.preventDefault();
    if (!isLoggedIn()) {
        checkAuth();
        return;
    }

    const question = questionInput.value.trim();
    if (!question) return;

    // Ensure we have a current conversation
    if (!getCurrentConv()) {
        createNewConversation();
    }

    // Add user message
    appendMessage("user", question); // this pushes to currentMessages and saves

    questionInput.value = "";
    autoResizeTextarea();
    sendBtn.disabled = true;

    const loadingEl = appendLoadingMessage();

    try {
        const token = getToken();
        if (!token) {
            throw new Error("توکن وجود ندارد. لطفاً مجدداً وارد شوید.");
        }

        // Get last few messages from current conversation
        const history = currentMessages.slice(-8);

        const res = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
                question,
                history: history,
            }),
        });

        if (!res.ok) {
            if (res.status === 401) {
                clearToken();
                clearUsername();
                checkAuth();
                throw new Error("نشست شما منقضی شد.");
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

        // Add assistant message to currentMessages
        currentMessages.push({ role: "assistant", content: fullAnswer });
        saveUserData();
        renderConversationList(); // update title if needed
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

// ========== UI HELPERS ==========
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

// ========== HEALTH ==========
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

// ========== ADMIN ==========
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
                clearUsername();
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
                clearUsername();
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
            headers: authHeader(),
            body: formData,
        });

        if (!res.ok) {
            if (res.status === 401) {
                clearToken();
                clearUsername();
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

// ========== SIDEBAR TOGGLE ==========
function toggleSidebar() {
    sidebar.classList.toggle("open");
    drawerBackdrop.classList.toggle("open");
}

// ========== INIT ==========
function init() {
    // Sidebar events
    toggleSidebarBtn.addEventListener("click", toggleSidebar);
    closeSidebarBtn.addEventListener("click", toggleSidebar);
    drawerBackdrop.addEventListener("click", toggleSidebar);
    newChatBtn.addEventListener("click", () => {
        createNewConversation();
        renderChatMessages();
        renderConversationList();
        if (window.innerWidth < 768) toggleSidebar();
    });

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

// Start the app
init();
