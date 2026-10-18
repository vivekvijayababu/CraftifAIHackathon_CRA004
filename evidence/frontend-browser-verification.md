# Frontend browser verification

Verified through Codex browser automation on 18 October 2026.

- Production dashboard loads at http://127.0.0.1:8001 with backend and WebSocket connected.
- Production mode shows zero actual crossing events and awaits camera/pipeline input.
- Synthetic mode selection displays the explicit SYNTHETIC MODE warning and independent counters.
- Start simulation produced all six normalized detection overlays and persisted crossings, updating counters, composition, activity bars, direction counts, and timestamped history.
- Stop simulation succeeded. Simulation is stopped after verification.
- Verified sample video `/media/sample.mp4` loads and displays the actual intersection footage in synthetic mode. The UI states synthetic overlays are unrelated to sample footage.
- Drew a second synthetic counting line with two pointer clicks; it appeared in the overlay and line list.
- Reloaded the page, selected synthetic mode, and confirmed the saved second line remained. Deleted the temporary test line afterwards; original line retained.
- Reviewed desktop screenshot: dark dashboard, counters, warning, video, composition, charts, directions, and timeline are readable without overlaps.
- CSV/JSON links carry data mode and selected filters. Backend export testing is documented separately.

Build verification: TypeScript strict typecheck passed; Vite 6.4.4 production build passed, 28 modules transformed. Bundle size: 237.13 kB JS (74.09 kB gzip), 9.52 kB CSS (2.89 kB gzip).

Remaining frontend limitation: playback URL editing is session-local. Persistent camera source configuration uses the backend camera API. Video is rendered to a 16:9 workspace; normalized overlays share that exact display transform, matching the bundled 1280×720 sample and default camera metadata.

Final browser reload on port 8001 additionally verified `/api/health` polling: Pipeline awaiting verified ingestion, Class mapping unconfirmed, Database ok. Backend/WebSocket connectivity is displayed separately from pipeline ingestion freshness.
