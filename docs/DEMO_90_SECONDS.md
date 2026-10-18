# 90-second demonstration script

Prepare the dashboard in recorded real mode, video paused, all filters cleared. Have the benchmark JSON and successful DeepStream log ready in separate tabs. Rehearse once; the times include navigation.

| Time | Action and narration |
|---|---|
| 0–12s | Show dashboard title and recorded-run badge. “TrafficFlow AI turns real CraftifAI PipeGen output into intersection analytics. This is a completed YOLOv8m TensorRT FP16 run on an RTX 3050, clearly labeled as recorded data.” |
| 12–28s | Play the source video; point at boxes and IDs. “The matching traffic clip has 900 frames. These boxes, classes and tracking IDs come from genuine metadata. Playback uses source presentation timestamps; we do not manufacture wall-clock time.” |
| 28–44s | Show counters and directions. “The pipeline reports 28 crossings: 20 cars, five persons and three motorcycles. Twenty-four move left to right and four right to left. Repeated detections across frames are shown separately from tracker IDs and crossings.” |
| 44–58s | Filter Right → left and point at four timeline rows. “Every row retains its real source event and track identity. We check all frame-level events against cumulative counters and crossing shapes. CSV and JSON export preserve those results.” |
| 58–71s | Show preserved benchmark and DeepStream log. “The recorded TensorRT report measures 7.234 milliseconds mean engine latency and 155.522 queries per second. That is engine throughput, not video FPS. DeepStream completed all 900 frames with normal EOS.” |
| 71–82s | Switch briefly to synthetic mode, then restore real. “Synthetic mode is explicitly labeled and stored separately. It lets us test lines and WebSockets without changing the real totals.” |
| 82–90s | Show README/evidence index. “Seventeen backend tests, the TypeScript check, production build and live integration checks pass. Source, sanitized pipeline export and evidence are packaged for review.” |

Do not claim live streaming, ground-truth physical-road-user counts, a fresh benchmark, a GitHub push or a portal submission unless separately completed. The official IR UI screenshot remains missing; use actual IR JSON as configuration evidence and label it accurately.
