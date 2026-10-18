# Real PipeGen metadata audit

Audited 18 October 2026, read-only. The submitted `evidence/pipegen/metadata.json` is a byte-identical snapshot of the successful PipeGen run, 2,462,702 bytes, SHA-256 `51f80e7a468d185c628b6bc52168efb37aa43c20fcbcc28586e7286a6c223f30`. No source output, model, GPU or Docker configuration was changed.

## Actual format and fields

One complete JSON object, not JSONL: root `pipeline`, `source`, `min_confidence`, and `frames`. `frames` contains 900 records numbered 0–899 at 1280×720. Every frame contains `source_id`, `pts_ns`, `objects`, `shapes`, and `fields`.

Each object has a genuine numeric `id` (tracking ID, including valid zero), `class_id`, `label`, detector `confidence`, `tracker_confidence`, and pixel bounding box `{left, top, width, height}`. All 130 observed tracking IDs retain one class and label throughout this file. Track IDs represent tracker output, not a guarantee of distinct real-world people or vehicles; fragmented tracks can inflate unique-ID totals. Repeated per-frame observations must not be presented as unique traffic counts.

| Label (class ID) | Object observations | Distinct track IDs | L→R crossings | R→L crossings |
|---|---:|---:|---:|---:|
| person (0) | 1,717 | 17 | 4 | 1 |
| bicycle (1) | 739 | 3 | 0 | 0 |
| car (2) | 3,748 | 94 | 17 | 3 |
| motorcycle (3) | 188 | 4 | 3 | 0 |
| bus (5) | 0 | 0 | 0 | 0 |
| truck (7) | 259 | 4 | 0 | 0 |
| traffic light (9) | 899 | 1 | outside road-user counts | outside road-user counts |
| backpack (24) | 12 | 1 | outside road-user counts | outside road-user counts |
| handbag (26) | 295 | 6 | outside road-user counts | outside road-user counts |

Totals: **7,857 all-class observations**, **6,651 road-user observations**, **130 all-class track IDs**, **122 road-user track IDs**, and **28 recorded road-user crossing events** (24 left to right, 4 right to left). There are 23 vehicle crossings and 5 person crossings. A person detection may include a rider; this model output does not independently establish pedestrian activity.

## Genuine crossings

`fields.num_events` gives the current-frame event count. Indexed fields contain `event_N_id`, `event_N_track_id`, `event_N_label`, `event_N_direction`, `event_N_ix`, and `event_N_iy`. There is no separate event class-ID or per-event timestamp field. Verified workaround: join an event to its same-frame object's tracking ID and label to obtain the class ID; use the enclosing frame's `pts_ns` as event observation timestamp. Do not claim interpolated physical crossing time.

The generated C++ parser uses bounding-box centers, retained per-track previous side, and finite segment intersection with the vertical line from (640,100) to (640,620). `left_to_right` means motion from screen-left to screen-right; it does not establish compass headings or entering/exiting a road. The event ID is track ID plus per-track crossing sequence (`2:1`, for example). IDs suppress duplicate event accumulation. Exported event polylines describe travel segments; a separate `counting_line` polyline describes the fixed boundary. Cumulative fields are `{label}_l2r`, `{label}_r2l`, and `total_crossings`.

Independently checked all 900 records: contiguous frame numbers; 28 unique event IDs; 28 event polylines; same-frame object ID/label match for every event; all intersection points lie on the counting segment; every directional cumulative increment equals that frame's events; all cumulative class sums equal `total_crossings`. No mismatch was found. Exact extracted events are in `evidence/pipegen/crossing-events.json`.

## Timing and source limits

PTS spans 66,666,666–30,033,333,333 ns, with 599 steps of 33,333,333 ns and 300 steps of 33,333,334 ns: continuous 30 FPS. These are stream presentation times, not UTC wall-clock timestamps. The first timestamp is offset approximately two frames from zero. For video replay alignment, subtract the first PTS; preserve raw PTS separately.

Metadata `source` is empty. Source footage identity is corroborated by the actual Pipeline IR input URL, which targets `intersection-pexels-30654965-30s-720p.mp4` already in this application. Its read-only SHA-256 and byte size are recorded in `source-video.json`. The filename/IR link is not an embedded media hash in metadata.

Raw objects contain non-road classes even though the IR describes selected road users. Filter by the verified road-user class IDs for dashboard traffic summaries; retain the raw file as evidence. There are no measured speed, traffic-signal phase, real geographic direction, or authoritative unique physical-road-user counts. Do not derive such claims from these records.

## Preserved engine and run evidence

- `PipelineIR.sanitized.json`: actual `pipeline_ir` graph; local directories replaced with project placeholders and internal traversal state omitted.
- `tensorrt-benchmark.json`: extracted recorded `trtexec` metrics from `engine.data.json`, not a new benchmark. TensorRT 10.3.0, FP16 build, input [1,3,480,640], 189 layers (170 FP16, 19 FP32), 64,634,652-byte engine. Recorded mean engine latency **7.23427 ms**, mean GPU compute **6.4127 ms**, throughput **155.522 QPS**. Engine QPS is not end-to-end video FPS. Per-layer profile is preserved separately. Recorded power values have implausible maxima and are deliberately omitted from the summary rather than endorsed.
- `tensorrt-compile.sanitized.json`: compile result and precision mix, paths removed.
- `model-stage.sanitized.log`: original stage chronology with project identity removed.
- `deepstream-run.sanitized.log`: engine deserialized; tracker initialized; EOS handled normally; **900 frames, 7,857 objects**; recorded execution **29.967947322 seconds**. The log includes a video-capabilities warning followed by successful completion. This audit did not rerun DeepStream.
- `deepstream-compile-attempt.sanitized.log`: an earlier failed compile and repair route, retained for honest provenance. Successful later run evidence is separate.
- `line_crossing_render_process.sanitized.cpp`: parser implementation showing event and cumulative-count semantics.
- `provenance.json`: SHA-256 and size of each original input used for evidence, with paths project-relative. OS permission denied access to `ModelStage.json` and cached evidence artifacts; no permission was bypassed. Readable engine/compile data and actual run output provide the recorded results above.

Only sanitized excerpts and metadata with labels, coordinates and stream timing are submitted. Account state, credentials, exported weights and private absolute paths are excluded. Dashboard/API verification is recorded by the integration owner separately.
