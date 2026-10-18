# Host readiness — 18 October 2026

Read-only inspection only. No drivers, Docker storage, containerd, partitions or system configuration were changed.

| Check | Observed result |
|---|---|
| OS | Ubuntu 26.04.1 LTS, Linux 7.0.0-38-generic x86_64 |
| Workspace | Separate TrafficFlow project under this task outputs; no other team repository copied |
| Disk | 49 GiB available on workspace filesystem at inspection |
| Python | 3.14.4 system interpreter |
| Node | Not on default PATH; bundled runtime used by main application setup |
| PipeGen | 0.5.1 |
| Docker | Client/server 29.9.1, context `default`; `docker info` succeeded after permission grant |
| NVIDIA | `nvidia-smi` exit 9: cannot communicate with NVIDIA driver |
| FFmpeg | 8.0.1; ffprobe available |
| Existing media/models | Scoped read-only search in task/Codex workspace, Videos, Downloads and conventional NVIDIA/DeepStream locations returned no matching MP4/ONNX/engine/PT assets |

The existing-media search was scoped, not an exhaustive machine inventory. GPU hardware/model was not established because NVIDIA-SMI failed. Docker server access does not establish GPU container readiness. PipeGen version does not establish pipeline readiness or transport support. A genuine inference run remains necessary after the user resolves GPU readiness. No account/session files were read.
