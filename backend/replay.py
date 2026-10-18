"""Read-only prefix index for replaying verified recorded metadata, never inference."""
import bisect
import csv
import io
from collections import Counter, defaultdict

TRAFFIC_LABELS = {'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck'}

class ReplayIndex:
    def __init__(self, run):
        self.run = run
        self.times = [(f['pts_ns'] - run.first_pts) / 1e9 for f in run.frames]
        self.prefixes = []
        observations = Counter()
        tracks = defaultdict(set)
        ids = set()
        for frame in run.frames:
            for obj in frame['objects']:
                observations[obj['label']] += 1
                tracks[obj['label']].add(obj['id'])
                ids.add(obj['id'])
            self.prefixes.append(dict(
                detection_observations=sum(observations.values()),
                traffic_detection_observations=sum(observations[k] for k in TRAFFIC_LABELS),
                unique_track_ids=len(ids), observations_by_label=dict(observations),
                unique_tracks_by_label={k: len(v) for k, v in tracks.items()},
            ))

    def packet(self, seconds=0):
        index = max(0, min(bisect.bisect_right(self.times, seconds) - 1, len(self.times) - 1))
        packet = self.run.packet(index)
        packet['events'] = [e for e in self.run.events if e['frame_id'] <= packet['frame_id']]
        packet['summary'] = dict(
            available=True, sha256=self.run.sha256,
            frame_count=len(self.times), processed_frames=index + 1,
            duration_seconds=self.times[-1], first_pts_ns=self.run.first_pts,
            last_pts_ns=self.run.frames[-1]['pts_ns'],
            **self.prefixes[index], **packet['stats'],
        )
        packet['playback_rate'] = 1
        packet['label'] = 'SIMULATED CAMERA — RECORDED REPLAY'
        return packet

    def events(self, seconds, class_name=None, direction=None):
        return list(reversed([e for e in self.packet(seconds)['events']
            if (not class_name or e['class_name'] == class_name)
            and (not direction or e['crossing_direction'] == direction)]))

    def csv(self, seconds, class_name=None, direction=None):
        out = io.StringIO()
        fields = ['source_event_id', 'frame_id', 'pts_ns', 'relative_seconds', 'camera_id',
                  'track_id', 'class_id', 'class_name', 'crossing_direction', 'counting_line_id']
        writer = csv.DictWriter(out, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(self.events(seconds, class_name, direction))
        return out.getvalue()
