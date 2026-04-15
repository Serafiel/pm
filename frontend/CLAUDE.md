# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run from this directory (`frontend/`):

```bash
npm run dev              # Start dev server (http://localhost:3000)
npm run build            # Production build
npm run lint             # ESLint
npm run test:unit        # Unit tests (Vitest, run once)
npm run test:unit:watch  # Unit tests in watch mode
npm run test:e2e         # E2E tests (Playwright)
npm run test:all         # Unit + E2E
```

## Architecture

**Entry point**: `src/app/page.tsx` renders `<KanbanBoard />` which owns all board state.

**State**: A single `BoardData` object held in `useState` at `KanbanBoard`. No external state library. `BoardData` is a normalized structure: `columns[]` holds ordered `cardIds[]`; full `Card` objects live in `cards` (a `Record<string, Card>`). All mutations (rename column, add card, delete card, drag-drop) produce a new `BoardData` via immutable updates.

**Drag-and-drop**: `@dnd-kit/core` wraps the board; `@dnd-kit/sortable` wraps each column's card list. `moveCard()` in `src/lib/kanban.ts` handles three cases: reorder within column, move to another column (insert at position), drop onto empty column (append).

**Component responsibilities**:
- `KanbanBoard` — state owner, DnD context, event handlers
- `KanbanColumn` — droppable area, renders its cards via `SortableContext`, inline-editable title
- `KanbanCard` — sortable/draggable, displays title + details, has Remove button
- `KanbanCardPreview` — rendered inside `DragOverlay` during drag
- `NewCardForm` — toggled form at column bottom; add card on submit

**Fonts**: Space Grotesk (`--font-display`) for headings, Manrope (`--font-body`) for body. Both loaded via `next/font/google` in `layout.tsx`.

**Styling**: Tailwind CSS v4. CSS custom properties defined in `globals.css` — always use these variables, not raw hex values:
- `--accent-yellow` (`#ecad0a`), `--primary-blue` (`#209dd7`), `--secondary-purple` (`#753991`), `--navy-dark` (`#032147`), `--gray-text` (`#888888`)

**Tests**:
- Unit: Vitest + @testing-library/react. Setup in `src/test/setup.ts`. Existing tests: `src/lib/kanban.test.ts` (moveCard logic), `src/components/KanbanBoard.test.tsx`.
- E2E: Playwright in `tests/`. Tests card add, delete, and drag operations against the running dev server.
