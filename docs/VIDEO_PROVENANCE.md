# Sample video provenance

Source: [Busy Urban Intersection with Traffic Crossing](https://www.pexels.com/video/busy-urban-intersection-with-traffic-crossing-30654965/), by FÁBIO REIS DE ABREU (PORTUGA), Pexels video 30654965. Source and license checked 18 October 2026.

License: [Pexels License](https://www.pexels.com/license/). Free use and modification allowed; attribution appreciated. Do not imply endorsement, sell unchanged copies, use the media as a trademark, or redistribute it as stock content. This project credits the creator voluntarily and keeps downloaded video out of Git.

The source page identifies vehicles and pedestrians at an intersection, 1920×1080, 62 seconds and 59.94 FPS. Its download link redirected to:

https://videos.pexels.com/video-files/30654965/13118916_1920_1080_60fps.mp4

Before downloading, an HTTP HEAD returned 200, video/mp4, Content-Length 91,969,775 bytes (~87.7 MiB). Destination was the task scratch directory (`work/video`), with only a derived clip retained in project `media/`. No large dataset or redundant video was downloaded. Existing-media scoped search found no usable sample.

Preparation: retain source seconds 30–60, resize to 1280×720, 30 FPS, H.264 via libx264 CRF 23, no audio, MP4 faststart. This is camera footage, not inference evidence. No detections or class counts have been asserted from this video.

Run `ffprobe -v error -show_streams -show_format media/intersection-pexels-30654965-30s-720p.mp4` from project root. Verification details are recorded in `evidence/video-ffprobe.json`; both source and derivative fully decoded successfully (exit 0) with `ffmpeg -v error -xerror -i <file> -f null -`. Exact verified local path is supplied in the task completion message rather than committed host-specific paths.

Visual QA: sampled source frames at five-second intervals show a nearly stationary intersection camera, multiple moving cars, motorcycles, a pedestrian traversing the zebra crossing around source second 40, and a bicycle at the right curb. The selected 30–60 second segment includes these events. No inference was performed.
