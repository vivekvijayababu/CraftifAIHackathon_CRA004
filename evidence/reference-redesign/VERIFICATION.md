# Reference-based frontend redesign

The attached dark traffic-management reference guided the flat application UI. The existing React App and CSS were edited in place; no replacement project, new dependency, backend/API change, model, tracker, TensorRT or DeepStream modification was made.

## Design and information hierarchy

- Desktop: compact left analytics column and dominant right video monitor. At 1440×1050, available content 1365 px, left 496.906 px (36.40%), right 846.094 px (61.98%), with 22 px gutter.
- Deep graphite background, layered charcoal surfaces, rounded panels, subtle borders and muted sage/slate charts. Slim navigation with accurate current-section indication and actual connection state.
- Four compact metrics separate source crossings 28, directional crossings 24/4 and road-user frame observations 6,651. Distribution uses genuine per-class frame observations, explicitly not unique physical road users or crossings. All-class tracker IDs 130 remain separate.
- Left activity chart uses real source-second events. Three recent source events link to the full event log. Right video retains 16: 9 geometry, native playback, source boxes/labels/IDs and source counting line, with actual playing/paused label. Native directional comparison remains below it.
- Existing source/line/export controls remain in Settings, which opens the technical disclosure. Real source lines remain immutable. Existing hash navigation, filters, event expansion and error handling are preserved.

## Executed verification

- Strict TypeScript check: passed.
- Vite 6.4.4 production build: passed,28 modules;247.64 kB JS (76.61 kB gzip),29.82 kB CSS (6.52 kB gzip).
- Existing backend tests: 17 passed in 0.87 s; one upstream Starlette/httpx deprecation warning. No separate frontend unit-test script exists.
- Live metadata summary: 900 frames;6,651 traffic observations;28 crossings (car 20,motorcycle 3,person 5);24 left-to-right/4 right-to-left. Distribution displayed car 3748,person 1717,bicycle 739,truck 259,motorcycle 188,bus 0. Values match the backend.
- Browser playback advanced source time and overlay frames; source boxes/track IDs appeared; pausing changed the playback status. Real line controls remained disabled as intended.
- Native direction filter returned 4 events; person filter returned 5 events. Export links carried matching mode/class filters. Settings route opened source/model/health/raw-evidence/export controls and also opened after reload at its hash.
- Event log expanded to 28 rows and collapsed to 6; sidebar retained 3 preview cards. Navigation and disclosure operated via keyboard.
- Synthetic mode streamed 6 classes and crossing total 18→24. Simulation stopped and real mode restored 28 unchanged. Synthetic observations are labeled unmeasured rather than invented.
- Mobile 390×844: no page overflow; document 375 px, video 347 px; video top 206 px before overview top 518 px. Tablet 860×1000: no overflow; document 845 px, video 801 px, video before overview. Viewport reset after screenshots.
- Screenshots capture the real connected data from the final build. Prior redesign evidence remains historical and is not overwritten.

No new map, GPS location, FPS/efficiency claims or fabricated counts were introduced. Only presentation and navigation behavior changed.
