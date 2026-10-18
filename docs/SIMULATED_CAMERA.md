# Simulated camera demo

The default real-data source replays the existing 30-second, 30 FPS intersection MP4 at 1×. It is labeled **SIMULATED CAMERA — RECORDED REPLAY** and never described as physical live inference. The white/light two-column interface with black text, muted blue chart accents and enlarged typography keeps statistics on the left and the prominent video and source selector on the right.

The browser video clock selects the latest genuine PipeGen frame by relative presentation timestamp. The backend returns cumulative observations, tracker identities and explicit crossing events through that frame. Repeated requests are read-only; pause holds the timestamp, restart returns to zero, and seeking reconstructs the prefix without inserting events. Original PipeGen timestamps are relative, not UTC capture times.

Recorded Video remains one click away and retains full-run totals. Two replay request failures (including inability to keep up with playback) trigger a friendly automatic switch to Recorded Video. Video replay errors also trigger fallback. Browser autoplay policies can require pressing Start.

USB Camera is a future hardware option. Device enumeration does not request a camera stream or run inference. With no video input, the interface says “No USB camera detected.” An enumerated input alone is not proof of a compatible USB device. Hardware controls and exports are unavailable. Synthetic mode remains a separate test source.

## Run and check

From the repository root, build the frontend and run `./scripts/run.sh`; its default URL is http://127.0.0.1:8005. `PORT` overrides the port. Use the dependency setup in README for a fresh checkout.

```bash
.venv/bin/python -m pytest backend/tests -q
cd frontend
pnpm exec tsc --noEmit
pnpm build
```

The recorded clip must be available as described in VIDEO_PROVENANCE.md. Missing replay metadata safely selects Recorded Video; missing video still requires restoring the configured clip.

## Recovery

All pre-feature work was committed as `ef7b1f8`, tagged `checkpoint-before-simulated-usb`, before creating `feature/simulated-usb-camera`. This checkpoint includes the prior white interface and existing evidence.

To inspect the preserved version without replacing current files, create a separate checkout with `git worktree add ../trafficflow-before-camera checkpoint-before-simulated-usb`. To undo the feature in the current branch, first preserve any later edits, then use `git revert` on the feature commit. Do not reset or clean the repository. PipeGen outputs, model and GPU/Docker settings were not changed.
