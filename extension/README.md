# Project Capsule — Browser Extension

A WXT-based Chrome extension (Manifest V3) that captures AI conversations from ChatGPT, Claude, and Gemini and sends them to the Project Capsule backend for storage and retrieval.

## Stack

- **Framework**: [WXT](https://wxt.dev/) (Vite-powered, MV3)
- **UI**: React 18 + TailwindCSS
- **Language**: TypeScript (strict)
- **Target**: Chrome (Manifest V3)

## Architecture

```
popup ──CAPTURE_REQUEST──▶ background.ts ──CAPTURE_REQUEST──▶ content.ts
                                │                                  │
                                │                           adapter.extract()
                                │                                  │
                                │◀──────── messages ───────────────┘
                                │
                         POST /api/v1/ingest/conversation
                                │
                         ◀── IngestResponse ──▶ popup (success state)
```

## Supported Platforms

| Platform | URL Pattern | Adapter |
|----------|-------------|---------|
| ChatGPT | chatgpt.com, chat.openai.com | `src/adapters/chatgpt.ts` |
| Claude | claude.ai | `src/adapters/claude.ts` |
| Gemini | gemini.google.com | `src/adapters/gemini.ts` |

## Development

```bash
# Install dependencies
npm install

# Start development server (hot reload)
npm run dev

# Build for production
npm run build
```

After `npm run dev`, Chrome DevTools will show you a `.output/chrome-mv3/` directory. Load it as an unpacked extension.

## Backend

The extension expects a backend running at `http://localhost:8000` with the endpoint:

```
POST /api/v1/ingest/conversation
Content-Type: application/json

{
  "source": "chatgpt",
  "project_hint": "My Project",
  "messages": [...],
  "url": "https://chatgpt.com/c/...",
  "title": "Page Title",
  "captured_at": "2024-01-01T00:00:00.000Z"
}
```

## Adding New Adapters

1. Create `src/adapters/yoursite.ts` extending `ConversationExtractor`
2. Implement `canHandle(url)` and `extract()`
3. Register it in `src/entrypoints/content.ts`'s `ADAPTERS` array
4. Add `host_permissions` entry in `wxt.config.ts`
