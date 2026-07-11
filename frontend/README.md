# Big Five — Frontend

React 19 + Vite + TypeScript (strict). Routing via `react-router`, server state
via `@tanstack/react-query`, test-taking state via `zustand`. Fonts are
self-hosted with `@fontsource` (no external CDN).

## Local development (without Docker)

```bash
npm install
npm run dev        # Vite dev server on :5173
npm run build      # type-check (tsc -b) + production build
```

In Docker Compose the frontend runs in a `node:22-alpine` container that installs
deps and starts the dev server for you — see the repo `README.md`.

## Dev-server API proxy

Vite proxies `/api` to the backend. The target is `VITE_API_PROXY_TARGET`,
defaulting to `http://localhost:8000` for host-run dev; Compose sets it to
`http://backend:8000`.

## Layout

- `src/main.tsx` — entry (Query client + Router providers)
- `src/router.tsx` — route table
- `src/components/AppShell.tsx` — top-nav shell (Report/Coach); Start and Test
  render their own full-bleed chrome
- `src/routes/` — `StartPage` (2a), `TestPage` (2b), `ScoringPage` (2c),
  `ReportPage`, `CoachPage`
- `src/components/Slider.tsx` — continuous 0–100 slider mapped to a 1–5 Answer
- `src/lib/useCountdown.ts` — the 30s soft timer (rAF; TimeBar semantics)
- `src/store/runStore.ts` — zustand store for the active Test Run
- `src/api/` — typed API client + `ensureProfileId` (localStorage Profile)
- `src/theme/tokens.css` — design tokens (colors, radii, sticker shadows, type)

## Test mode

With `VITE_TEST_MODE=true` the Start screen prefills demographics and the Test
screen shows an "⚡ Autofill & finish" control — see the repo `README.md`
Testing section. The flag is read in `src/config.ts`; unset, the controls are
absent from the DOM.
