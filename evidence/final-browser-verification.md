# Genuine recorded PipeGen dashboard browser verification

Verified in the in-app browser at http://127.0.0.1:8003/ on 2026-10-18.

- Backend connected; explicit RECORDED PIPEGEN RUN label, 900 frames, 29.97 second metadata span.
- Full-run crossings: 28; car 20, pedestrian 5, motorcycle 3, bus/truck/bicycle 0.
- Detection observations 7,857; distinct tracking IDs 130. Separate repeated observations and track identity explanation visible.
- Direction counters left_to_right 24 and right_to_left 4. Native right_to_left filter showed four events, track IDs 114, 82, 69 and 17. Pedestrian class filter showed five events, IDs 128,17,19,31,28.
- Event rows display actual track IDs and relative PTS seconds, with no fabricated wall-clock timestamps.
- Export links preserve native direction/class filters.
- Verified source video loaded with duration 30 seconds, readyState 4, /media/sample.mp4. Native Play advanced currentTime from 2.846 to 11.500 seconds; recorded frame advanced to339, PTS11366666666ns, and source bounding boxes rendered over footage.
- Native scrubber Home then Right sought to0.300s; adapter selected frame9, PTS366666666ns. Paused playback preserved matching overlays.
- Real source counting line visible and edit/delete disabled.
- Synthetic mode kept explicit synthetic labeling, editable independent line and synthetic tracker IDs; start generated counts8→10, then stopped. Restoring real mode showed unchanged28 genuine crossings.
- Browser console errors: none.

Evidence: dashboard-real-run.jpg (full page), dashboard-real-overview.jpg (viewport), dashboard-real-dom.txt, dashboard-synthetic-isolation.jpg.
