# PipeGen export for TrafficFlow AI

This folder preserves sanitized generated Pipeline IR, DeepStream configuration, label map, parser sources and original run-script template from the verified project. Original files were read-only. Hashes of originals and exported text are in `manifest.json`.

`${PIPEGEN_PROJECT}`, `${TRAFFICFLOW_VIDEO}` and `${LOCAL_PATH}` replace private machine paths. Configuration placeholders must be rendered for a target host before GPU execution; these are submission templates, not an automatically deployable container. Standard NVIDIA library/include paths remain where needed by the generated source.

`model-info.json` identifies the exported TensorRT model by SHA256 and size. The 64.6 MB engine, ONNX weights, compiled libraries, key files and timing cache are excluded. The actual model remains in the owner's original project. No retraining, GPU configuration change or model conversion was performed by final verification.

The genuine output snapshot, engine FP16 speed report, per-layer profile, successful DeepStream log and metadata audit are in `../evidence/pipegen/`. See `../docs/REAL_METADATA_AUDIT.md` for scope and gaps. An official Pipeline IR UI screenshot was unavailable; the actual sanitized IR JSON is provided without claiming it is a screenshot.
