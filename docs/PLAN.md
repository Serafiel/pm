# Project Plan

## Part 1: Plan ✅
Enrich this document and create frontend/CLAUDE.md. Get user sign-off before proceeding.

---

## Part 2: Scaffolding ✅

Set up the Docker infrastructure, FastAPI backend, and start/stop scripts. At the end of this part the app serves a "hello world" HTML page and can make a backend API call — no frontend, no database yet.

### Steps

- [x] Create `backend/main.py` with a minimal FastAPI app:
  - `GET /` returns a plain HTML "hello world" response
  - `GET /api/ping` returns `{"status": "ok"}`
- [x] Create `backend/pyproject.toml` (or `uv`-compatible config) with FastAPI and uvicorn as dependencies
- [x] Create `Dockerfile` at project root:
  - Base image: `python:3.12-slim`
  - Install `uv`, use it to install backend dependencies
  - Copy and statically build the Next.js frontend (or skip for now — just backend)
  - Expose port 8000, run uvicorn
- [x] Create `scripts/start.sh` (Mac/Linux) and `scripts/start.bat` (Windows) that build and run the Docker container
- [x] Create `scripts/stop.sh` and `scripts/stop.bat` that stop and remove the container

### Tests & Success Criteria

- [x] `docker build` completes without errors
- [x] After running the start script, `curl http://localhost:8000/` returns HTML with "hello world"
- [x] `curl http://localhost:8000/api/ping` returns `{"status": "ok"}`
- [x] Stop script cleanly halts the container

---

## Part 3: Add in Frontend ✅

Statically build the Next.js frontend and serve it from FastAPI at `/`. The Kanban board demo is visible in the browser.

### Steps

- [x] Update the Next.js build to output a static export (`output: 'export'` in `next.config.ts`)
- [x] Update `Dockerfile` to:
  - Install Node and build the frontend (`npm ci && npm run build`)
  - Copy the static export into the backend's static file directory
- [x] Update `backend/main.py` to mount the static files and serve `index.html` as the catch-all route
- [x] Confirm all existing frontend unit and E2E tests still pass (run inside Docker build or CI step)
- [x] Add backend integration tests confirming static files are served correctly

### Tests & Success Criteria

- [ ] `docker build` completes without errors
- [ ] Navigating to `http://localhost:8000/` in a browser shows the Kanban board
- [ ] All frontend unit tests pass (`npm run test:unit`)
- [ ] All frontend E2E tests pass against the Docker-served URL

---

## Part 4: Fake User Sign-In ✅

Add a login gate: users must sign in with `user` / `password` to see the Kanban board. A logout option is available.

### Steps

- [x] Add `POST /api/auth/login` endpoint accepting `{username, password}`, returning a session token (simple signed cookie or JWT — keep it minimal)
- [x] Add `POST /api/auth/logout` endpoint that clears the session
- [x] Add `GET /api/auth/me` endpoint that returns the current user or 401
- [x] Add a login page in the Next.js frontend (`src/app/login/page.tsx`)
- [x] Gate the Kanban board: if `/api/auth/me` returns 401, redirect to `/login`
- [x] Add a logout button visible on the board

### Tests & Success Criteria

- [ ] Visiting `/` without a session redirects to `/login`
- [ ] Logging in with wrong credentials shows an error, does not redirect
- [ ] Logging in with `user` / `password` redirects to `/` and shows the board
- [ ] Clicking logout clears the session and redirects to `/login`
- [x] Backend unit tests cover login, logout, and me endpoints
- [ ] Frontend E2E tests cover the full login → board → logout flow

---

## Part 5: Database Modeling

Design and document the SQLite schema for the Kanban. Get user sign-off before proceeding to Part 6.

### Steps

- [ ] Propose a schema covering: users, boards, columns, cards (with ordering)
- [ ] Document the schema in `docs/database.md` with table definitions, relationships, and rationale
- [ ] Include migration approach (create tables if not exist on startup)
- [ ] Present to user for approval

### Tests & Success Criteria

- [ ] User has reviewed and approved `docs/database.md`
- [ ] Schema supports multiple users (even though MVP has one)
- [ ] Schema supports column ordering and card ordering within columns

---

## Part 6: Backend API ✅

Add API routes to read and mutate the Kanban for the authenticated user. Database is created automatically on first run.

### Steps

- [ ] Add database init on FastAPI startup: create tables if they don't exist, seed the default board for a new user
- [ ] Add routes:
  - `GET /api/board` — return the authenticated user's board as JSON
  - `PUT /api/board/columns/{column_id}` — rename a column
  - `POST /api/board/cards` — create a card in a column
  - `DELETE /api/board/cards/{card_id}` — delete a card
  - `PATCH /api/board/cards/{card_id}/move` — move a card (target column + position)
- [ ] All routes require authentication (return 401 otherwise)
- [ ] Use the same `BoardData` JSON shape the frontend already understands

### Tests & Success Criteria

- [ ] Backend unit tests (pytest) cover each route: happy path, auth failure, not-found
- [ ] Database file is created automatically if it doesn't exist
- [ ] A second login as the same user returns the same persisted board state
- [ ] All existing frontend and E2E tests still pass

---

## Part 7: Frontend + Backend Integration ✅

Have the frontend use the real backend API instead of `initialData`. The board is now fully persistent.

### Steps

- [ ] Replace `initialData` with a `GET /api/board` fetch on mount
- [ ] Wire all user actions (rename column, add card, delete card, drag-drop) to their respective API calls
- [ ] Handle loading and error states minimally (no spinners needed — keep it simple)
- [ ] Optimistic updates are acceptable but not required; correctness over smoothness

### Tests & Success Criteria

- [ ] Adding a card, refreshing the page, and seeing the card still there
- [ ] Moving a card, refreshing the page, and seeing it in the new position
- [ ] Renaming a column persists across refresh
- [ ] Deleting a card persists across refresh
- [ ] Full E2E test suite passes against Docker-served app
- [ ] No console errors during normal usage

---

## Part 8: AI Connectivity

Connect the backend to OpenRouter. Verify the connection with a minimal test before building the full AI feature.

### Steps

- [ ] Read `OPENROUTER_API_KEY` from `.env` at project root; fail fast on startup if missing
- [ ] Add `POST /api/ai/ping` endpoint that sends "What is 2+2?" to OpenRouter using model `openai/gpt-oss-120b` and returns the raw response
- [ ] Use the `openai` Python SDK pointed at the OpenRouter base URL (standard approach)

### Tests & Success Criteria

- [ ] `POST /api/ai/ping` returns a response containing "4" (or equivalent)
- [ ] If `OPENROUTER_API_KEY` is missing or invalid, a clear error is logged and the endpoint returns 500 with a descriptive message

---

## Part 9: AI Board Integration

Extend the AI endpoint to accept the user's full board state and conversation history. The AI responds with structured output that optionally includes board mutations.

### Steps

- [ ] Define a Structured Output schema: `{ reply: string, board_update: BoardUpdate | null }` where `BoardUpdate` describes card create/move/delete/rename operations
- [ ] Add `POST /api/ai/chat` endpoint:
  - Accepts `{ message: string, history: Message[] }`
  - Fetches the user's current board from the database
  - Sends system prompt (board JSON + instructions) + conversation history + user message to OpenRouter with structured outputs enabled
  - If `board_update` is non-null, applies the mutations to the database
  - Returns `{ reply, board_updated: boolean }`
- [ ] Document the system prompt and structured output schema in `docs/ai.md`

### Tests & Success Criteria

- [ ] Sending "Move the first card to Done" results in the card being moved in the database
- [ ] Sending "Add a card called X to Backlog" creates the card
- [ ] The reply is always a non-empty string
- [ ] Board is unchanged when `board_update` is null
- [ ] Backend tests cover: mutation applied, no mutation, malformed AI response handled gracefully

---

## Part 10: AI Chat Sidebar UI

Add the AI chat sidebar to the frontend. Board updates from AI are reflected immediately without a page refresh.

### Steps

- [ ] Add a sidebar panel to `KanbanBoard` (toggle open/closed)
- [ ] Sidebar contains a scrollable message history and a text input
- [ ] On submit, call `POST /api/ai/chat` with the message and local history
- [ ] Display the AI's `reply` in the message history
- [ ] If `board_updated` is true, re-fetch `GET /api/board` and update local state
- [ ] Keep the sidebar styling consistent with the existing color palette and design language

### Tests & Success Criteria

- [ ] Sending a chat message displays the AI reply in the sidebar
- [ ] Asking the AI to move a card results in the card moving on the board without a manual refresh
- [ ] Sidebar opens and closes cleanly
- [ ] E2E tests cover: send message, receive reply, board update reflected in UI
