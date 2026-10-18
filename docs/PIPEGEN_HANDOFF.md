# PipeGen integration handoff

Real ingestion is deliberately gated until an actual metadata sample confirms the mapping. No synthetic result is an inference result.

## Capture from the actual configured pipeline

- PipeGen version, pipeline export/configuration, detector model labels and class IDs.
- One raw output message with no credentials, and several consecutive frames for the same tracked object.
- Supported output transport and delivery semantics. HTTP is implemented; select it only if PipeGen can emit HTTP or use a small external bridge from its verified output. Do not assume MQTT or file output support.
- Source/camera ID, original source width/height, inference tensor width/height, resize policy, padding offsets, crop/ROI offsets, orientation and timestamps/timebase.
- Frame ID or presentation timestamp; session/tracker reset identifier.
- Stable tracker ID, raw class ID/name, confidence, bounding box origin/units/order and reference dimensions.
- Dropped frames, ID reuse, reconnect/reset semantics and whether messages can arrive out of order.

## Canonical HTTP envelope

POST `/api/ingest` with `mode: "real"`, `camera_id`, `frame_id`, ISO `timestamp`, `width`, `height`, `coordinate_space: "pixels"` or `"normalized"`, and `detections`: `{track_id,class_id,confidence,bounding_box:{x,y,width,height}}`.

Coordinates must describe the original visible source frame. For letterboxing: source_x=(inference_x-padding_x)/scale_x and source_y=(inference_y-padding_y)/scale_y; apply crop offsets and rotate before normalization. Width/height use the same scales. For stretched inference, use separate x/y scales. Never normalize directly against tensor dimensions when padding/cropping is present. The browser renders a matching video aspect ratio and normalized overlays.

After verifying labels, configure `PIPEGEN_CLASS_MAP` as JSON mapping raw numeric IDs to canonical names: car, bus, truck, motorcycle, bicycle, pedestrian; set `PIPEGEN_MAPPING_CONFIRMED=true`. The development default mapping is only for synthetic testing. Inspect `/api/health` and backend schema at `/docs` before connecting the bridge.

Backend-generated crossing records include timestamp, camera_id, frame_id, track_id, class_id, class_name, confidence, bounding_box, counting_line_id, crossing_direction and crossing_event_type. Never send a count for every detection; submit tracked frames and let the crossing engine establish transitions.

## Counting limitations

Counting uses bbox centers, a deadband around each finite line, and per-track state. A new ID starts a new trajectory and cannot be matched reliably to a prior ID. Lost detections, occlusion and tracker resets may miss crossings; ID reuse may corrupt identity. Clear/reset tracking state at pipeline restarts, use a new session-prefixed ID, and verify representative clips before trusting totals. A camera or line edit requires fresh trajectory state. Counts are operational telemetry, not ground truth.

## Remaining acceptance checklist

1. Restore working GPU/driver and authorized Docker access outside this application.
2. Run the actual DeepStream tracker and collect the metadata above.
3. Confirm classes, geometry and transport; implement only necessary raw-to-canonical bridge.
4. Align frame PTS and overlays with the displayed video. The current demo video is an independent sample; synthetic tracks are unrelated to its imagery.
5. Replay labeled crossings and compare directions, missed counts, duplicate counts and reconnect behavior.
6. Configure durable deployment, authentication and access restrictions before exposing ingestion beyond localhost.

### Optional verified inference-coordinate transform

The HTTP adapter also accepts `coordinate_space: "inference"` with `inference_transform: {scale_x,scale_y,padding_x,padding_y,crop_x,crop_y}`. Frame `width`/`height` remain the original source dimensions. It removes tensor padding, reverses x/y scale, applies source crop offsets, then normalizes. Out-of-frame boxes and missing transforms are rejected. Rotation must be resolved before ingestion. Example: a 1280×720 source letterboxed into 640×640 uses scale_x=scale_y=0.5, padding_x=0, padding_y=140, crop offsets 0. Do not use that example unless it matches the actual preprocessing.
