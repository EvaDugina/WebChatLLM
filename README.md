# WebChatLLM — тематический чат с Gemini

Небольшое одностраничное веб‑приложение: вход по ключу доступа, чат в рамках заданной темы (system prompt), история сообщений хранится постоянно.

## Быстрый старт

1) Установите Docker:

   - **Linux:**  
     ```bash
     curl -fsSL https://get.docker.com | sudo sh
     ```

   - **Windows / Mac:**  
     Скачайте и установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2) Убедитесь, что в `.env` заданы правильные значения

3) Соберите и поднимите prod‑окружение:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

4) Откройте: `http://localhost:8080` (или хост/порт, проброшенные в compose).
5) Остановка:

```bash
docker compose -f docker-compose.prod.yml down
```

## Устройство проекта (кратко)

- `frontend/` — чистые HTML/CSS/JS, два экрана: логин и чат.
- `backend/` — FastAPI API:
  - авторизация по ключу доступа → выдача подписанного токена
  - endpoints для истории и отправки сообщений
  - сервис LLM (Gemini) и сервис хранения (SQLite)
- `nginx/` — единая точка входа: раздаёт фронт и проксирует `/api/*` на бэкенд. Поэтому нет CORS и проще UX.
- `docker-compose.*.yml` — отдельные конфигурации для dev и prod.

## Что можно доработать

- Стриминг ответа модели (SSE/WebSocket), “печатает…”
- Контекст/память диалога (windowed context) и системные инструменты/функции
- Ротация/инвалидация токенов, rate limiting, аудит логов
- Миграции БД (Alembic) и индексы/поиск по истории
- UI: темы, markdown‑рендер, подсветка кода, управление историей
