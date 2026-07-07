# Coding Standards & Guidelines — AI-BOS Enterprise

This manual establishes the engineering principles, directory organization conventions, language paradigms, and testing rules enforced across the AI-BOS codebase.

---

## 1. Core Engineering Principles

All developers must write code compliant with:

- **SOLID Principles:** Keep interfaces narrow, classes focused, and extend features via composition over inheritance.
- **Clean Architecture:** Domain layers and business logic (Use Cases) must remain decoupled from databases, network gateways, and framework frameworks.
- **Domain-Driven Design (DDD):** Use rich aggregates and value objects in critical cores (e.g. agent state definitions) rather than anaemic schemas.
- **Strict Typing:** Declare precise type signatures across Python (Pydantic, typing annotations) and TypeScript. Avoid `Any` or `unknown` fallbacks.

---

## 2. Backend Coding Rules (Python & FastAPI)

### Coding Style & Formatting
- Code formatting is managed automatically by **Black** (configured to 88 characters line-length in `pyproject.toml`).
- Lint checks are processed by **Ruff**, searching for code quality smells, unused imports, or anti-patterns.
- Always use asynchronous definitions (`async def`) for all routes, database calls, and client request handlers.

### Package Management & Imports
- Group imports in alphabetical order inside three distinct logical blocks:
  1. Standard Library imports
  2. Third-party packages
  3. Internal application components
- Never use wildcard (`from module import *`) mappings.

---

## 3. Frontend & Mobile Coding Rules (React / TypeScript)

### Structural Formatting
- Structure interfaces and React components modularly. Keep business logic separate from pure rendering components.
- Use React Hook patterns to encapsulate API fetch operations, state transformations, or event subscriptions.

### Styling & CSS Custom Properties
- Ad-hoc styling is strictly prohibited. Use design tokens (`variables.css` / `tokens.ts`) for all metrics (spacing, color, typography, curves).
- Write responsive grid layouts using pure CSS flexbox and grid rules. Avoid injecting framework utilities classes.

---

## 4. Error Handling and Telemetry

- **No Silent Errors:** Catch specific exceptions rather than basic `Exception` catch-alls. Provide human-readable, contextual error reports.
- **Audit Logging:** Database edits, authentication steps, and agent transitions must register logs inside the PostgreSQL audit table or MongoDB system collections.
- **Tracing Context:** Ensure FastAPI correlation headers pass through LangGraph run states.
