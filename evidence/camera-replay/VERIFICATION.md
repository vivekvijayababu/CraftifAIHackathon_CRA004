# Camera replay verification — 2026-10-18

Final automated checks: **20 backend tests passed**, TypeScript check passed, Vite production build passed (29 modules). One upstream Starlette/httpx deprecation warning remains. Tests cover event boundaries, prefix observations, restart/repeat behavior, validation, unavailable metadata, filtered exports and stable/synthetic isolation in addition to the existing suite.

The final built frontend and live backend at http://127.0.0.1:8005 passed HTTP checks for root, health, video and metadata frame routes. See localhost-smoke.json.

| Video seconds | Frame | Crossings | Traffic observations |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 0.667 | 20 | 1 | 134 |
| 5 | 150 | 3 | 881 |
| 15 | 450 | 10 | 2650 |
| 30 | 899 | 28 | 6651 |

Final crossings: car 20, person 5, motorcycle 3; directions left-to-right 24, right-to-left 4. Final observations are repeated frame observations, not unique physical objects. There are 122 traffic tracker identities and 130 identities across all classes. The original metadata SHA256 remained `51f80e7a468d185c628b6bc52168efb37aa43c20fcbcc28586e7286a6c223f30`. SQLite retained exactly 28 recorded events. At 15 seconds CSV contained 10 events; final right-to-left CSV contained 4.

## Browser checks performed during this feature

Default replay autoplay was observed at playback rate 1. Pause held video time 24.179269 seconds, 21 crossings and 5436 traffic observations across repeated reads, matching backend frame 725. Restart returned zero totals. End playback reached 28 crossings and 6651 observations. Recorded Video retained full totals, native playback and looping. Physical mode displayed “No USB camera detected,” with no video element or detection overlay. Switching back restarted progressive replay.

Automatic fallback was exercised against the existing stable server without a replay endpoint; the selector changed to Recorded Video, full totals remained 28, and the explanatory notice was visible. Screenshots automatic-fallback.jpg and usb-hardware.jpg record these cases.

Browser control became disabled in Work settings before the final build. Consequently the final small changes (slow-response fallback and disabling hardware exports) have TypeScript/build verification, but no new browser screenshot or final browser retest. No main replay screenshot is claimed. The final automated checks above were rerun after these changes.

No physical USB inference or new model benchmark was performed. This feature reuses genuine recorded PipeGen output; it does not retrain or execute TensorRT, modify source metadata, or change GPU/Docker configuration.
