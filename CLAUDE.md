# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Project Management MVP web app — a Kanban board with AI chat integration. See `AGENTS.md` for full business requirements and `docs/PLAN.md` for the implementation roadmap before making significant changes.

**Current state**: Frontend MVP is complete (pure frontend demo). Backend (FastAPI + SQLite + Docker) is planned/in-progress.

## Commands

All commands run from `frontend/`:

```bash
npm run dev          # Start Next.js dev server
npm run build        # Build for production
npm run lint         # ESLint
npm run test:unit    # Unit tests (Vitest)
npm run test:unit:watch  # Unit tests in watch mode
npm run test:e2e     # E2E tests (Playwright)
npm run test:all     # All tests
```

## Architecture

**Stack**: Next.js 16 / React 19 / TypeScript frontend; FastAPI (Python) backend (planned); SQLite; OpenRouter API (`openai/gpt-oss-120b`) for AI; Docker container deployment.

**Frontend entry point**: `frontend/src/app/page.tsx` → renders `<KanbanBoard />`

**Key data structures** (`frontend/src/lib/kanban.ts`):
- `BoardData` holds `columns[]` (ordered) and `cards` (Record by id)
- Columns contain `cardIds[]` for ordering; full card data lives in the cards record
- `createId()` generates unique IDs; `moveCard()` handles same-column, cross-column, and column-drop scenarios

**Component tree**:
- `KanbanBoard` — top-level state owner, drag-and-drop context (@dnd-kit)
- `KanbanColumn` — droppable area
- `KanbanCard` — draggable card
- `KanbanCardPreview` — drag overlay
- `NewCardForm` — add cards to columns

**Styling**: Tailwind CSS v4. CSS custom properties for the color palette are defined in `globals.css` — use these variables rather than raw hex values:
- `#ecad0a` accent yellow, `#209dd7` primary blue, `#753991` secondary purple, `#032147` dark navy, `#888888` gray text

**Testing**: Vitest + @testing-library/react for unit tests; Playwright for E2E (card operations, drag-drop).

## Coding Standards

- Keep it simple — no over-engineering, no unnecessary defensive programming, no extra features
- No emojis, ever
- When hitting issues, identify the root cause with evidence before applying a fix
- Use latest, idiomatic approaches for all libraries
