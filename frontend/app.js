const ACCESS_KEY_RE = /^[A-Za-z0-9_-]{8,255}$/;
const TOKEN_KEY = "chat_token";
const THEME_KEY = "chat_theme";

function qs(id) {
  return document.getElementById(id);
}

function show(el) {
  el.classList.remove("hidden");
}

function hide(el) {
  el.classList.add("hidden");
}

function setError(el, msg) {
  if (!msg) {
    el.textContent = "";
    hide(el);
    return;
  }
  el.textContent = msg;
  show(el);
}

function formatDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
}

async function api(path, { method = "GET", body = undefined } = {}) {
  const token = sessionStorage.getItem(TOKEN_KEY);
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try {
    data = await res.json();
  } catch (_) {}
  if (!res.ok) {
    const detail = data && data.detail ? String(data.detail) : `http_${res.status}`;
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return data;
}

function renderMessages(container, items) {
  container.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "messages-empty";
    empty.textContent = "История пока пуста — начните диалог.";
    container.appendChild(empty);
    return;
  }

  for (const m of items) {
    const row = document.createElement("div");
    row.className = `msg ${m.role === "user" ? "msg--user" : "msg--assistant"}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = m.text;

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = formatDate(m.created_at);

    bubble.appendChild(meta);
    row.appendChild(bubble);
    container.appendChild(row);
  }
  container.scrollTop = container.scrollHeight;
}

async function initModelInfo() {
  const el = document.getElementById("modelInfo");
  if (!el) return;
  try {
    const res = await fetch("/api/model");
    if (!res.ok) return;
    const data = await res.json();
    if (!data || !data.url || !data.model_id) return;
    el.innerHTML = `<a href="${data.url}" target="_blank" rel="noreferrer">${data.model_id}</a>`;
  } catch (_) {
    // тихо игнорируем ошибку, это только декоративная информация
  }
}

async function bootstrap() {
  const loginView = qs("loginView");
  const chatView = qs("chatView");
  const logoutBtn = qs("logoutBtn");
  const themeToggle = qs("themeToggle");

  const accessKeyInput = qs("accessKeyInput");
  const loginBtn = qs("loginBtn");
  const loginError = qs("loginError");

  const messagesEl = qs("messages");
  const sendForm = qs("sendForm");
  const messageInput = qs("messageInput");
  const sendBtn = qs("sendBtn");
  const chatError = qs("chatError");
  const chatStatus = qs("chatStatus");

  function setChatStatus(msg) {
    if (!chatStatus) return;
    chatStatus.textContent = msg || "";
  }

  function applyTheme(theme) {
    const t = theme === "light" ? "light" : "dark";
    if (t === "light") {
      document.body.classList.add("theme-light");
    } else {
      document.body.classList.remove("theme-light");
    }
    localStorage.setItem(THEME_KEY, t);
    if (themeToggle) {
      themeToggle.textContent = t === "light" ? "Ночная тема" : "Дневная тема";
    }
  }

  function setAuthed(isAuthed) {
    if (isAuthed) {
      hide(loginView);
      show(chatView);
      show(logoutBtn);
    } else {
      show(loginView);
      hide(chatView);
      hide(logoutBtn);
    }
  }

  function validateKey() {
    const v = accessKeyInput.value || "";
    const ok = ACCESS_KEY_RE.test(v);
    loginBtn.disabled = !ok;
    if (v.length === 0) setError(loginError, "");
    return ok;
  }

  function validateMessage() {
    const v = (messageInput.value || "").trim();
    sendBtn.disabled = v.length < 1 || v.length > 500;
    return v;
  }

  accessKeyInput.addEventListener("input", () => {
    validateKey();
  });

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = localStorage.getItem(THEME_KEY) || "dark";
      const next = current === "light" ? "dark" : "light";
      applyTheme(next);
    });
  }

  loginBtn.addEventListener("click", async () => {
    setError(loginError, "");
    const key = accessKeyInput.value || "";
    if (!ACCESS_KEY_RE.test(key)) return;
    loginBtn.disabled = true;
    try {
      const data = await api("/auth/login", { method: "POST", body: { access_key: key } });
      sessionStorage.setItem(TOKEN_KEY, data.token);
      accessKeyInput.value = "";
      setAuthed(true);
      await loadHistory();
    } catch (e) {
      sessionStorage.removeItem(TOKEN_KEY);
      const msg = e && e.status === 401 ? "Неверный ключ доступа." : "Ошибка входа. Попробуйте ещё раз.";
      setError(loginError, msg);
    } finally {
      validateKey();
    }
  });

  logoutBtn.addEventListener("click", () => {
    sessionStorage.removeItem(TOKEN_KEY);
    setAuthed(false);
    messagesEl.innerHTML = "";
    setError(chatError, "");
    messageInput.value = "";
    validateKey();
  });

  messageInput.addEventListener("input", () => validateMessage());

  async function loadHistory() {
    setError(chatError, "");
    try {
      setChatStatus("Загружаем историю…");
      const items = await api("/messages");
      renderMessages(messagesEl, items);
    } catch (e) {
      if (e && e.status === 401) {
        sessionStorage.removeItem(TOKEN_KEY);
        setAuthed(false);
        setError(loginError, "Сессия истекла. Введите ключ доступа снова.");
        return;
      }
      setError(chatError, "Не удалось загрузить историю.");
    } finally {
      setChatStatus("");
    }
  }

  let sending = false;
  sendForm.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (sending) return;
    const text = validateMessage();
    if (!text) return;

    setError(chatError, "");
    sending = true;
    sendBtn.disabled = true;
    messageInput.disabled = true;
    setChatStatus("Модель думает…");
    try {
      const out = await api("/messages", { method: "POST", body: { text } });
      messageInput.value = "";
      const items = await api("/messages");
      renderMessages(messagesEl, items);
    } catch (e) {
      const msg =
        e && e.status === 502
          ? "Ошибка запроса к модели. Попробуйте ещё раз."
          : e && e.status === 401
            ? "Сессия истекла. Введите ключ доступа снова."
            : "Ошибка отправки сообщения.";
      setError(chatError, msg);
      if (e && e.status === 401) {
        sessionStorage.removeItem(TOKEN_KEY);
        setAuthed(false);
      }
    } finally {
      sending = false;
      messageInput.disabled = false;
      validateMessage();
      messageInput.focus();
      setChatStatus("");
    }
  });

  // initial
  setAuthed(false);
  validateKey();
  validateMessage();
  applyTheme(localStorage.getItem(THEME_KEY) || "dark");
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (token) {
    try {
      await api("/auth/validate");
      setAuthed(true);
      await loadHistory();
    } catch (_) {
      sessionStorage.removeItem(TOKEN_KEY);
      setAuthed(false);
    }
  }

  initModelInfo();
}

bootstrap();

