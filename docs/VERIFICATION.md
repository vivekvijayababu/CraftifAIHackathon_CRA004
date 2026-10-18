# Verification record

Current documentation audit: [current dashboard evidence](../evidence/final-submission/current-dashboard/README.md). Latest rerun: 20 backend tests passed, TypeScript and production build passed at source commit `691a4ad`. The app runs on port 8005. The official IR screenshot is now present; the feature branch is pushed. Export completeness remains unresolved.

## Historical integration results (before camera replay and final styling)

# Final integration verification — 18 October 2026

## Executed results

- **17 backend tests passed** in 0.95s. Twelve existing tests cover synthetic/live HTTP validation, tracking, finite-line crossing, duplicate suppression, reverse directions, tracker session resets, persistence, transforms, WebSockets and synthetic control. Five additional tests cover genuine metadata totals/provenance, read-only/idempotent import, replay invariance, rejection of altered cumulative counts, source-line immutability, real filtering/export and synthetic isolation. One upstream Starlette/httpx TestClient deprecation warning; no failures. See `evidence/real-backend-tests.txt`.
- Strict TypeScript and Vite 6.4.4 production build passed. See `evidence/real-frontend-build.txt`.
- Browser verified real 900-frame run, 28 crossings (car 20 / person 5 / motorcycle 3), 7,857 observations, 130 IDs, video playback/seek and source overlays. Right-to-left filtering returned 4 events; pedestrian filtering returned 5 with real tracking IDs. Synthetic counts increased independently; real total stayed 28. No browser console errors. See `evidence/final-browser-verification.md`, screenshots and DOM evidence. Browser interaction checks used port 8003; final port 8004 serves the same frontend and adds source IDs to CSV and recorded-run WebSocket status.
- Final localhost smoke at **http://127.0.0.1:8004** passed: dashboard/docs/health/video HTTP 200; 28 JSON/CSV source events; native filters; repeated replay preserving run totals; `recorded_run_ready` real WebSocket; six-class synthetic stream with increasing counts and real total unchanged; SQLite recorded-event count 28 after repeated imports. See `evidence/real-localhost-smoke.json`.
- All 900 metadata frames independently audited. Explicit events, event shapes and cumulative increments agree. All 28 events join matching same-frame track/label objects. Original metadata SHA256 stayed unchanged after integration: `51f80e7a468d185c628b6bc52168efb37aa43c20fcbcc28586e7286a6c223f30`.
- Source video corroborated by generated pipeline URI and IR. Existing clip SHA256 matches preserved provenance. Earlier preparation fully decoded source and 30-second derivative: H.264,1280×720,30FPS,5,316,950bytes. No replacement video downloaded during this integration.

## Evidence boundaries

TensorRT and DeepStream results are genuine supplied artifacts inspected read-only, not fresh benchmarks. DeepStream log reports normal EOS,900 frames,7,857 objects. Engine mean latency 7.23427 ms and throughput 155.522 QPS describe the recorded engine test, not dashboard/video throughput.

This is a **completed recorded run**, not a live pipeline. UTC capture timestamps and event confidence are absent and remain null. Event class IDs join verified same-frame detections; relative time comes from frame PTS. Tracker IDs and observations are not authoritative physical-road-user identities. Screen directions are not compass headings.

The byte-identical metadata snapshot and sanitized Pipeline IR/benchmark/run evidence make this reproducible without private directories. Original PipeGen output, model, GPU/Docker and system configuration were not changed. Private accounts and absolute host paths were excluded from tracked evidence; source video and weights are excluded.

At this historical checkpoint no remote push had occurred. This has been superseded by the feature-branch publication documented above. Service uses one worker and loopback. Live transport, authentication and remote deployment remain separate future work.
