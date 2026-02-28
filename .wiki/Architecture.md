## Введение (контекст)

Нужно одностраничное веб‑приложение “тематический чат”:
- **Экран 1**: вход по ключу доступа (валидация на фронте + проверка на бэке).
- **Экран 2**: чат с LLM в рамках заданной темы (**system prompt** на сервере).
- **История**: сохраняется между перезагрузками и перезапусками (постоянное хранилище).
- **Стек**: Python backend, фронт только HTML/CSS/JS без фреймворков, LLM — Google Gemini API.

Критично оценится: архитектура, UX/UI, подход к авторизации (как ключ передаётся/хранится).

## Архитектура (широко → узко)

### 1) Границы модулей

- **Frontend (SPA)**:
  - отвечает за UX, валидации, рендер истории/диалога
  - хранит только **токен сессии** (не сам ключ)
  - общается с API по `/api/*`

- **Backend (API)**:
  - проверяет ключ доступа и выдаёт токен
  - принимает сообщения, вызывает LLM, сохраняет историю
  - инкапсулирует работу с Gemini и с хранилищем

- **Nginx (edge)**:
  - раздаёт статический фронт
  - проксирует `/api/*` на backend
  - даёт **same-origin**: фронт и API на одном хосте → CORS не нужен

### 2) Потоки (user journeys)

#### Логин
1) Пользователь вводит ключ → фронт валидирует regex и длину.
2) `POST /api/auth/login` с ключом.
3) Backend:
   - валидирует формат ключа
   - сравнивает с `ACCESS_KEY` (env)
   - выдаёт **подписанный токен** (TTL) → возвращает фронту.
4) Фронт кладёт токен в `sessionStorage` и открывает чат.

#### Отправка сообщения
1) Фронт валидирует сообщение: trim, 1..500, блокирует кнопку на время запроса.
2) `POST /api/messages` с Bearer-токеном.
3) Backend:
   - проверяет токен
   - пишет user message в БД
   - вызывает Gemini (system prompt + текущее сообщение)
   - пишет assistant message в БД
   - возвращает пару сообщений (или фронт запрашивает историю заново).

#### История
- `GET /api/messages` возвращает список сообщений в порядке `id ASC`.
- Хранилище: SQLite файл, путь `DB_PATH`, монтируется volume → персистентность.

### 3) Подход к авторизации (почему так)

- **Ключ доступа не хранится в браузере**: вводится один раз для обмена на токен.
- Клиент хранит только **сессионный токен** (подписан сервером) в `sessionStorage`:
  - автоматически очищается при закрытии вкладки
  - минимизирует риск “утечки” постоянного секрета
- Токен имеет TTL (`TOKEN_TTL_SECONDS`), после истечения фронт просит ключ заново.

## Методы решения функциональных задач (только словами)

### Авторизация по ключу
- Валидация на фронте: regex `^[A-Za-z0-9_-]{8,255}$`, блокировка кнопки, сообщение ошибки.
- На бэке:
  - повторить валидацию формата
  - сравнить с `ACCESS_KEY` из окружения
  - при успехе выдать signed token (срок жизни) и использовать Bearer-схему на остальных эндпоинтах

### Тематический чат
- Системный промпт хранится на сервере (`SYSTEM_PROMPT`) и не редактируется клиентом.
- Вызов Gemini выполняется в отдельном сервисе, чтобы легко заменить модель/провайдера.
- Ошибки LLM: отлавливать и возвращать понятный код/сообщение, фронту — показывать UI-ошибку.

### История переписки
- Выбрать постоянное хранилище (SQLite как “простое, надёжное, 0 инфраструктуры”).
- Сохранять каждое сообщение отдельно с:
  - role (`user|assistant`)
  - text
  - created_at (UTC ISO)
- Отдавать историю одним запросом при загрузке чата и после отправки сообщения.

## Детальная структура проекта

```
ChatGemini/
  README.md
  Task.md
  ARCHITECTURE.md
  .env.example
  .gitignore
  docker-compose.dev.yml
  docker-compose.prod.yml

  nginx/
    dev.conf              # SPA + proxy /api -> backend
    prod.conf

  frontend/
    index.html            # login view + chat view
    styles.css            # современная минимальная тема
    app.js                # состояние, валидации, работа с API
    Dockerfile            # prod image (nginx + static)

  backend/
    requirements.txt
    Dockerfile            # prod
    Dockerfile.dev        # dev (uvicorn --reload)
    data/                 # volume для SQLite (локально)
    app/
      main.py             # FastAPI app + routers
      api/
        deps.py           # auth dependency (Bearer token)
        routes_auth.py    # /api/auth/*
        routes_chat.py    # /api/messages
      core/
        config.py         # env settings
        security.py       # key format + token service
      models/
        message.py        # Pydantic схемы API
      services/
        llm/
          gemini.py       # вызов google-genai
        storage/
          sqlite.py       # SQLite: init/list/add
```

## Docker: dev vs prod (как задумано)

- **dev**:
  - backend: `uvicorn --reload`, монтируется `backend/app`
  - frontend: `nginx` с volume на `frontend/`, изменения видны сразу при refresh
  - единый вход: `http://localhost:8080`

- **prod**:
  - backend: без reload
  - frontend: отдельный образ с копированием статики + nginx конфигом
  - данные: volume на `backend/data` (SQLite файл)

