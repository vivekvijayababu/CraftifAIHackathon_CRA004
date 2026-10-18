# Verification — 18 October 2026

## Executed checks

- Backend: **12 pytest tests passed** (0.56 seconds on final run). HTTP health and validation, real-ingest gate, class mapping, crossing and reverse direction, deadband jitter, one-second debounce, repeat frame suppression, finite line segment, changed IDs and tracker sessions, synthetic/real isolation, SQLite history after state clear, persisted counting lines, camera metadata/source persistence, pixel normalization, letterbox reversal, duplicate IDs, WebSocket frames, concurrent viewers sharing synthetic trajectories, simulation stop/start, CSV export and error handling.
- One upstream Starlette TestClient/httpx deprecation warning; no failing tests.
- Frontend: strict TypeScript compilation and Vite production build passed. Browser-tested real zero state, synthetic warning, moving overlays, counters/charts/timeline, start/stop and persisted line creation/reload/deletion. See `evidence/frontend-browser-verification.md`.
- Live localhost smoke: dashboard/API/docs/video return HTTP 200, real WebSocket reports awaiting_pipeline, synthetic WebSocket carries six classes and increasing crossings; real event history remains empty. See `evidence/localhost-smoke.json`.
- Video: source and derived clip fully decoded with ffmpeg exit 0. Final sample H.264 1280×720, 30 FPS, 30 seconds, 5,316,950 bytes. Probe and SHA256 evidence retained.

## Boundaries

No actual DeepStream inference was run. NVIDIA-SMI cannot communicate with the driver. Docker itself is accessible; GPU container operation remains unverified. PipeGen's actual class IDs, preprocessing metadata, tracker semantics and export transport remain unconfirmed. HTTP ingestion is implemented; no claim is made that PipeGen emits this canonical contract without a bridge.

Frontend browser review covered desktop and persisted line drawing, not an exhaustive mobile/accessibility/device matrix. Sample video playback and synthetic movement are independent. Tracker identity is not durable across backend restarts; SQLite event history is durable. Run one backend worker. Export currently caps results at 10,000 records; event UI shows recent history. The pipeline health freshness window is ten seconds. Authentication is not provided for remote hosting; bind locally.

Git repository is initialized locally with generated media, dependencies, databases and secrets excluded. GitHub connector authentication was detected, but no verified target remote or repository-creation capability is available in this session. No remote was created, no push was performed, and nothing was made public.
