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

- `src/main.tsx` — entry (ClerkGate + Query client + Router providers)
- `src/router.tsx` — route table (every screen renders its own full-bleed chrome)
- `src/routes/` — `StartPage` (2a), `TestPage` (2b), `ScoringPage` (2c),
  `ReportPage` (2d), `CoachPage` (2f intro / 2g workspace, in `routes/coach/`)
- `src/auth/ClerkGate.tsx` — mounts `ClerkProvider` only when a publishable key
  is set, and bridges the session token to the API client
- `src/components/Slider.tsx` — continuous 0–100 slider mapped to a 1–5 Answer
- `src/lib/useCountdown.ts` — the 30s soft timer (rAF; TimeBar semantics)
- `src/store/runStore.ts` — zustand store for the active Test Run
- `src/api/` — typed API client, `coach.ts` (coach endpoints + SSE stream),
  `ensureProfileId` (localStorage Profile)
- `src/theme/tokens.css` — design tokens (colors, radii, sticker shadows, type)

## Coach (Clerk)

The coach account gate mounts Clerk only when `VITE_CLERK_PUBLISHABLE_KEY` is
set (`clerkEnabled` in `src/config.ts`). Keyless, `/coach` shows the intro with
an on-tone setup card and never renders a Clerk component — nothing crashes. Set
the two Clerk keys (`VITE_CLERK_PUBLISHABLE_KEY` here, `CLERK_SECRET_KEY` on the
backend) to enable sign-in, coach creation, and chat.

## Test mode

With `VITE_TEST_MODE=true` the Start screen prefills demographics and the Test
screen shows an "⚡ Autofill & finish" control — see the repo `README.md`
Testing section. The flag is read in `src/config.ts`; unset, the controls are
absent from the DOM.

## End-to-end (Playwright)

`@playwright/test` is a host-side devDependency (it runs on your machine, not in
the container). One spec, `e2e/happy-path.spec.ts`, drives the running Compose
stack through the Quick form: start → select Quick → autofill 60 items → assert
the domain-only report (5 bars + narrative) → verify the PDF endpoint returns
`%PDF`. `playwright.config.ts` reads `FRONTEND_URL` (default
`http://localhost:15173`) and does **not** start its own server, so the stack
must be up with `VITE_TEST_MODE=true`.

```bash
npm install            # pulls @playwright/test
npm run e2e:install    # one-time: download the Chromium browser
npm run e2e            # run the spec against the running stack
```
