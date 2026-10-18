# Current dashboard capture and submission audit — 18 October 2026

Source branch: `feature/simulated-usb-camera`; source commit before this documentation-only audit: `691a4ad3fc762a076ff06348a241ada089ef3dd9`. Working tree was clean before editing. Rollback checkpoint `ef7b1f8` and tag `checkpoint-before-simulated-usb` remain intact.

Screenshots were captured directly from the running localhost:8005 browser with genuine backend data; image bytes were saved without alteration. The current interface matches white/light surfaces, dark typography, muted blue charts, larger text and video-focused two-column layout. Some secondary labels remain visually pale; no frontend styling was changed during this documentation task.

- [overview.jpg](overview.jpg): primary replay at end, frame 899, 28 crossings / 6651 traffic observations / directions 24 and 4.
- [full-dashboard.jpg](full-dashboard.jpg): full page at the same completed replay, including charts and event log.
- [simulated-replay.jpg](simulated-replay.jpg): after genuine Restart then Pause, source frame 128 around 4.27s, 3 crossings / 766 traffic observations. The screenshot is a paused replay, not a physical camera stream.
- [crossing-events.jpg](crossing-events.jpg): three explicit events reached at that replay timestamp, with IDs and screen directions.
- [recorded-video.jpg](recorded-video.jpg): selected stable Recorded Video source, full run totals 28 / 6651 / 24 / 4.

The source selector was restored to primary simulated replay. Existing saved automatic-fallback testing remains historical evidence; no new failure was injected during this audit.

Latest executed checks: TypeScript passed; Vite production build passed (29 modules); 20 backend tests passed with one upstream Starlette/httpx deprecation warning. Live root/health/summary/replay requests succeeded; stored metadata was independently recounted (900 frames, 7857 raw observations, 6651 traffic observations, 122 traffic tracker IDs, 28 crossings). Benchmark evidence retains mean engine latency 7.23427ms and throughput 155.522QPS; no GPU benchmark was rerun. See [audit-results.json](audit-results.json).

The genuine supplied Pipeline IR screenshot remains unchanged. Complete official export remains missing; see [export audit](../../../pipegen-export/EXPORT_COMPLETENESS.md). Application source, model and pipeline were not modified. Historical images are retained and labeled separately.

Post-push GitHub verification: README preview on branch feature/simulated-usb-camera rendered both current dashboard embeds and the supplied IR graph; all three images had complete=true and nonzero natural width (1034, 1034 and 661 pixels respectively). The separate Mermaid architecture also rendered. [GitHub README screenshot](github-readme.jpg) records the published page.
