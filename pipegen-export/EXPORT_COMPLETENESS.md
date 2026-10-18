# Official export completeness audit

## Result: sanitized subset, not complete official Export Project

The accessible original PipeGen working project was compared read-only with this directory. All 13 original/generated source/config/script entries in manifest.json matched their original SHA256 values and all 13 committed copies matched their recorded export hashes. PipelineIR.sanitized.json, manifest.json, model-info.json and README.md are also present. A relative-path inventory is saved in [export-comparison.json](../evidence/pipegen/export-comparison.json); a working-project directory is not itself proof of an official export archive.

Included: sanitized Pipeline IR; detector/tracker DeepStream configs; COCO labels; all nine parser/source/header/Makefile files listed in the manifest; generated run.sh template; model identity, engine size and SHA256 manifest. Genuine metadata, benchmark, compile/profile evidence and successful run log are separately committed under evidence/pipegen.

Not included from the original working project:

- Project/session state: state.json, RequirementState.json, .pir_bindings.json, UserInfo.json and requirement documents/cache. These can contain account information, conversation history or private source paths and are not automatically published.
- Model-stage artifacts: yolov8m.fp16.plan (64,634,652 bytes), its .plan.key, timing cache, modules JSON, visualization/engine/tactics JSON, model-stage configuration and engine_paths.json. Some model-stage files were not readable with current permissions. The model manifest identifies the engine but does not replace it. Key files must remain private.
- Compiled shared libraries under pipeline/deepstream/build (parser sources and Makefile are included); diagnostic run.debug.sh/run.vms.sh, raw debug logs, local output and verification frame cache. The successful sanitized execution log and metadata are included separately.
- The source video and required installed NVIDIA/DeepStream/custom GStreamer runtime dependencies. No standalone container/runtime distribution or ONNX weights were verified in the export folder.

No separate official “Export Project” archive/folder was found in the inspected workspace. Adding private working-project state or engine files indiscriminately would not establish that this is the official export. No additional export source was fabricated, and no model binary or credential was added.

## What the owner must supply

Provide the actual CraftifAI PipeGen **Export Project** download (with its project manifest/configuration and required model/runtime references), or an accessible PipeGen project/export link accepted by the submission organizer. Review private fields and distribute large models through an appropriate authorized artifact link. A complete exported project's import/run instructions must accompany it. Until supplied and verified, the complete-export form answer remains **NO**.

## Running the supplied subset

The dashboard runs independently using the root README and recorded metadata; it requires no GPU. This subset is not a one-command official project import.

For GPU execution on a separately prepared matching host, the generated Makefile references CUDA 12.6 and DeepStream 7.1, and the script requires nvinfer_backport, nvcustomprocess, nvtracker, NVIDIA display/GStreamer plugins and the associated development headers/libraries. Supply the engine identified in model-info.json and matching video. Set PIPEGEN_PROJECT and TRAFFICFLOW_VIDEO for run.sh. Replace the literal ${PIPEGEN_PROJECT} paths in the detector config in a separate deployment copy: the GStreamer config file does not automatically expand shell variables. Build libraries with the provided Makefile, then use the generated script. This deployment procedure has not been rerun here and runtime dependencies are not bundled. Do not overwrite original PipeGen output or keys; use an isolated deployment copy and a separate JSON_OUT.
