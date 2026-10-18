# TrafficFlow AI — hackathon submission

**Track A — Embedded SF × CraftifAI Physical AI Hackathon**

TrafficFlow AI turns genuine CraftifAI PipeGen traffic-video output into an auditable intersection analytics dashboard. YOLOv8m detection, TensorRT FP16 execution and DeepStream tracking provide source detections and line-crossing events. FastAPI validates the completed run and persists its events in SQLite; React displays playback-aligned boxes, traffic composition, directional counters, event history and CSV/JSON exports.

The verified 30-second source contains 900 metadata frames and 7,857 object observations, including 6,651 traffic-class observations and 122 traffic-class tracker IDs. Explicit pipeline records report **28 crossings: 20 cars, 5 persons and 3 motorcycles**, with **24 left-to-right and 4 right-to-left**. All 900 frame counters agree with explicit events and crossing shapes. Observations repeat across frames; tracker identities are not guaranteed unique physical road users.

The preserved TensorRT benchmark records **7.23427 ms mean engine latency**, **6.4127 ms mean GPU compute time** and **155.522 QPS** on the RTX 3050 Laptop GPU. These engine measurements are not end-to-end video FPS. The successful DeepStream log reports EOS, 900 frames and 7,857 objects. This final verification inspected those original measurements without rerunning GPU benchmarking or changing system configuration.

The application distinguishes a **recorded real PipeGen run** from an isolated synthetic test mode. It preserves native event/track IDs and PTS time, leaves absent UTC timestamps and event confidence null, and does not invent crossings. Read-only import is idempotent by source SHA256; source counting geometry remains immutable.

Included: source, tests, setup instructions, model hash/information, sanitized PipeGen IR/configuration/parser export, genuine metadata snapshot, benchmark/run evidence and dashboard screenshots. Model weights, engine binaries, private paths and credentials are excluded.

Local demonstration: http://127.0.0.1:8004

GitHub URL: pending the owner's exact authorized repository URL. No remote push has occurred. No hackathon submission portal was supplied, so this description is ready to paste rather than claimed submitted.

Missing evidence: official Pipeline IR UI screenshot. Actual sanitized IR JSON is included; no substitute image is labeled official.
