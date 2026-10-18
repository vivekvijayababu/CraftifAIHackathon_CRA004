# TrafficFlow AI — hackathon submission

**Track A — Embedded SF × CraftifAI Physical AI Hackathon**

TrafficFlow AI turns genuine CraftifAI PipeGen traffic-video output into an auditable intersection analytics dashboard. YOLOv8m detection, TensorRT FP16 execution and DeepStream tracking provide source detections and line-crossing events. FastAPI validates the completed run and persists its events in SQLite; React displays playback-aligned boxes, traffic composition, directional counters, event history and CSV/JSON exports.

The verified 30-second source contains 900 metadata frames and 7,857 object observations, including 6,651 traffic-class observations and 122 traffic-class tracker IDs. Explicit pipeline records report **28 crossings: 20 cars, 5 persons and 3 motorcycles**, with **24 left-to-right and 4 right-to-left**. All 900 frame counters agree with explicit events and crossing shapes. Observations repeat across frames; tracker identities are not guaranteed unique physical road users.

The preserved TensorRT benchmark records **7.23427 ms mean engine latency**, **6.4127 ms mean GPU compute time** and **155.522 QPS** on the RTX 3050 Laptop GPU. These engine measurements are not end-to-end video FPS. The successful DeepStream log reports EOS, 900 frames and 7,857 objects. This final verification inspected those original measurements without rerunning GPU benchmarking or changing system configuration.

The application distinguishes a **recorded real PipeGen run** from an isolated synthetic test mode. It preserves native event/track IDs and PTS time, leaves absent UTC timestamps and event confidence null, and does not invent crossings. Read-only import is idempotent by source SHA256; source counting geometry remains immutable.

Included: source, tests, setup instructions, model hash/information, sanitized PipeGen IR/configuration/parser export, genuine metadata snapshot, benchmark/run evidence and dashboard screenshots. Model weights, engine binaries, private paths and credentials are excluded.

Local demonstration: http://127.0.0.1:8005

GitHub: https://github.com/vivekvijayababu/CraftifAIHackathon_CRA004/tree/feature/simulated-usb-camera (the original TrafficFlow-AI URL redirects here). The feature branch has been pushed; no main merge or portal submission is claimed.

The current white/black dashboard uses blue graph accents and larger typography. Simulated USB Camera is the primary recorded replay: start/pause/restart/seek drive genuine progressive metadata, charts and events. Recorded Video remains a stable full-run fallback. Hardware checking does not implement physical USB AI inference.

Current screenshots: [overview](../evidence/final-submission/current-dashboard/overview.jpg), [replay](../evidence/final-submission/current-dashboard/simulated-replay.jpg). The genuine supplied [IR node graph](../evidence/pipegen/pipeline-ir-graph.png) is included. Twenty backend tests, TypeScript and production build passed during the latest documentation audit.

Remaining blocker: pipegen-export is a sanitized subset. Supply the complete official Export Project download or an accepted project link; see [completeness audit](../pipegen-export/EXPORT_COMPLETENESS.md). No hackathon portal submission was performed.
