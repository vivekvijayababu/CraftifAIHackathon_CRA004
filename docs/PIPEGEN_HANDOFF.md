# Verified PipeGen integration handoff

## Implemented transport

The completed run is imported read-only from an actual PipeGen `metadata.json` JSON object. Its root fields are `pipeline`, `source`, `min_confidence`, and `frames`. This is a completed-file adapter, not a streaming tailer or an assumed HTTP/MQTT PipeGen integration. `PIPEGEN_METADATA_PATH` selects the original output; the audited snapshot is the default fallback for reproducibility.

## Verified format and mappings

Each frame has `frame`, `source_id`, `pts_ns`, `width`, `height`, `objects`, `shapes`, and `fields`. Objects contain numeric `id`, `class_id`, `label`, `confidence`, `tracker_confidence`, and pixel `bbox: {left,top,width,height}`.

Observed traffic label IDs: 0=`person` (dashboard pedestrian), 1=bicycle, 2=car, 3=motorcycle, 7=truck. No bus object is present. Class labels in the actual pipeline label file include bus at ID 5, but zero bus observations/crossings are reported. Other observed IDs are 9 traffic light, 24 backpack, 26 handbag. Nontraffic detections remain visible in evidence and detection totals and do not contribute to traffic crossing counters.

The adapter preserves tracking ID0 and all source labels. Source boxes are already at 1280×720; dividing x/width by 1280 and y/height by 720 gives normalized geometry shared by the display and source counting line. No inference-tensor dimensions or crop transform are guessed.

## Authoritative crossing records

For `n` in `[0,num_events)`, `fields` contains `event_n_id`, `event_n_track_id`, `event_n_label`, `event_n_direction`, `event_n_ix`, `event_n_iy`. These are direct source events. Directions are `left_to_right` / `right_to_left`. Per-class cumulative fields use `_l2r` and `_r2l`, plus `total_crossings`. Matching event polylines are present in `shapes`.

The importer validates all 900 frames: explicit event class/direction counts must match cumulative differences and crossing shapes; total counters must match their per-class sums. Any mismatch rejects the run. Events are saved to separate SQLite recorded-run tables keyed by source SHA256 and index; repeated imports do not add crossings.

Crossing `class_id` is joined only from a matching track/label object in the same frame. Event confidence is absent and remains null; object confidence remains a detection measurement. Event IDs and track IDs are retained. The source supplies one counting line `(640,100)`→`(640,620)`; recorded mode renders it read-only. Editing synthetic lines cannot change this run.

## Time and identity limits

`pts_ns` is a presentation timestamp, not UTC. Relative video time is `(pts_ns-first_pts_ns)/1e9`, with first PTS 66,666,666ns. The original video path is corroborated by the generated pipeline script and sanitized Pipeline IR; the metadata root `source` is empty. Source matching and hash are recorded in evidence. Playback frame selection follows the verified constant PTS offset; this is not a live feed.

Tracks are tracker identities, not guaranteed physical objects. This run contains 130 IDs,122 in traffic classes. Repeated frame observations must not be called distinct vehicles. Classification or ID changes, occlusion and resets can affect model/pipeline counts. This adapter reports supplied pipeline results and does not establish ground truth.

## API

- `GET /api/pipegen/summary`: run totals, label observations/track counts, hash, timestamps, gaps and source events.
- `GET /api/pipegen/frame?index=20` or `?seconds=0.7`: normalized recorded detections and cumulative frame statistics.
- `GET /api/stats?mode=real`: final recorded-run crossing totals.
- `GET /api/events?mode=real`: native source events, with class/direction filtering.
- `GET /api/export?mode=real&format=json|csv`: filtered source event export.
- `GET /api/replay?seconds=…`: genuine cumulative snapshot through playback time.
- `GET /api/replay/export?seconds=…&format=json|csv`: events reached in playback, respecting filters.
- Existing synthetic REST/WebSocket functionality remains separate.

While a recorded run is loaded, live real ingestion and real line edits are rejected to prevent mixing recomputed events with authoritative run counts.

## Remaining work

This requested completed-run integration is functional. A continuously running live bridge would require confirming an actual PipeGen streaming transport, handling file rollover/tracker sessions and testing ordering/reconnect behavior. Do not describe this recorded-file import as live ingestion. Remote hosting needs authentication and a deployment access policy; local service binds loopback and uses a single worker. No model retraining or GPU/Docker changes were made.
