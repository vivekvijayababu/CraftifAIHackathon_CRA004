# 90-second demonstration script

Prepare the dashboard in Simulated USB Camera real-data mode, video paused, all filters cleared. Have the benchmark JSON and successful DeepStream log ready in separate tabs. Rehearse once; the times include navigation.

| Time | Action and narration |
|---|---|
| 0–12s | Show dashboard title and recorded-run badge. “TrafficFlow AI turns real CraftifAI PipeGen output into intersection analytics. This is a completed YOLOv8m TensorRT FP16 run on an RTX 3050, clearly labeled as recorded data.” |
| 12–28s | Play the source video; point at boxes and IDs. “The matching traffic clip has 900 frames. These boxes, classes and tracking IDs come from genuine metadata. Playback uses source presentation timestamps; we do not manufacture wall-clock time.” |
| 28–44s | Let the replay finish or seek to its end, then show counters and directions. “The pipeline reports 28 crossings: 20 cars, five persons and three motorcycles. Twenty-four move left to right and four right to left. Repeated detections across frames are shown separately from tracker IDs and crossings.” |
| 44–58s | Filter Right → left and point at four timeline rows. “Every row retains its real source event and track identity. We check all frame-level events against cumulative counters and crossing shapes. CSV and JSON export preserve those results.” |
| 58–71s | Show preserved benchmark and DeepStream log. “The recorded TensorRT report measures 7.234 milliseconds mean engine latency and 155.522 queries per second. That is engine throughput, not video FPS. DeepStream completed all 900 frames with normal EOS.” |
| 71–82s | Show Recorded Video stable mode, then restore replay. “Recorded Video preserves full-run totals and is the automatic fallback if replay fails. Synthetic mode is separately labeled for development.” |
| 82–90s | Show README/evidence index. “Twenty backend tests, the TypeScript check, production build and live integration checks pass. Source, sanitized pipeline export and evidence are packaged for review.” |

Show the genuine Pipeline IR node graph embedded in README separately from the Mermaid architecture diagram. Use the current white/black interface. GitHub feature-branch publication is verified; a main merge and portal submission are not. Do not claim physical live USB inference, ground-truth road-user counts, a fresh GPU benchmark or a complete official export. The sanitized export remains partial.
