# ChequeVerify frontend (F1)

From the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173/. Dashboard: http://127.0.0.1:5173/dashboard.
The backend runs separately on http://127.0.0.1:8000 using the existing environment:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Optionally set `VITE_API_BASE_URL` in the shell before Vite starts. The configured origin must be allowed by the backend's `CV_CORS_ORIGINS`. No secrets belong in Vite environment variables; all VITE values are public.

```powershell
npm run typecheck
npm test
npm run build
```

F1 includes the introduction, responsive shell, typed API client, manual readiness refresh and live dashboard. Recognition and benchmarks are pending routes. No automatic inference, image/result storage or application analytics. System fonts only. The credited external light scene is isolated in its entry iframe and receives no application data; it is removed before entering the landing or dashboard.

API types use the backend code and saved responses. Health 503 is a valid health body; other errors are parsed defensively. JSON body request IDs are used because the frozen backend does not expose X-Request-ID through CORS. Header fallback remains best-effort. Contrary to a broad statement in FRONTEND_REQUIREMENTS, health/model-info/benchmark bodies do not themselves contain request_id; no such field is assumed.

See DESIGN_DIRECTION.md for implemented visual placements and resource limits, and VISUAL_CREDITS.md for third-party attribution. Source was created with Codex assistance; the student team should review and understand it.

## Visual correction (27 Nov 2026)

The original F1 light/document illustration has been replaced. The entry displays Cullen Webber's credited original hosted light scene in an isolated iframe; this requires an internet connection. Enter removes that iframe and opens the local interactive tiled wave hero. Below it, Field Notes uses the actual MIT-licensed LeafThrough reader with six original local SVG pages and a full text alternative. See DESIGN_DIRECTION.md and VISUAL_CREDITS.md. Other application routes retain their F1 status.
