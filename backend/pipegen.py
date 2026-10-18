"""Read-only adapter for genuine PipeGen recorded metadata; never runs crossing inference."""
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

TRAFFIC = {'person':'pedestrian','bicycle':'bicycle','car':'car','motorcycle':'motorcycle','bus':'bus','truck':'truck'}
CLASSES = ['car','bus','truck','motorcycle','bicycle','pedestrian']
class RecordedRun:
    def __init__(self, path, db_path):
        raw=Path(path).read_bytes()
        self.sha256=hashlib.sha256(raw).hexdigest()
        doc=json.loads(raw)
        self.frames=doc['frames']
        if not self.frames: raise ValueError('No PipeGen frames')
        self.first_pts=self.frames[0]['pts_ns']
        self.events=[]; observations=Counter(); tracks=defaultdict(set); all_ids=set(); previous=Counter()
        for frame in self.frames:
            for obj in frame['objects']:
                observations[obj['label']]+=1; tracks[obj['label']].add(obj['id']);all_ids.add(obj['id'])
            found=Counter()
            shape_counts=Counter()
            for shape in frame.get('shapes',[]):
                parts=shape.get('label','').rsplit(' ',1)
                if shape.get('kind')=='polyline' and len(parts)==2 and parts[0] in TRAFFIC and parts[1] in ('left_to_right','right_to_left'):
                    shape_counts[tuple(parts)]+=1
            for n in range(frame['fields']['num_events']):
                fields=frame['fields'];prefix=f'event_{n}_'
                label=fields[prefix+'label'];direction=fields[prefix+'direction']
                if label not in TRAFFIC or direction not in ('left_to_right','right_to_left'): raise ValueError('Unknown event label/direction')
                found[(label,direction)]+=1
                track_id=fields[prefix+'track_id']
                observed={o['class_id'] for o in frame['objects'] if o['id']==track_id and o['label']==label}
                class_id=next(iter(observed)) if len(observed)==1 else None
                self.events.append(dict(id=len(self.events)+1,event_id=fields[prefix+'id'],source_event_id=fields[prefix+'id'],mode='real',source='pipegen_recorded_run',camera_id='intersection-01',frame_id=frame['frame'],pts_ns=frame['pts_ns'],relative_seconds=(frame['pts_ns']-self.first_pts)/1e9,timestamp=None,track_id=str(track_id),class_id=class_id,class_name=TRAFFIC[label],label=label,confidence=None,counting_line_id='counting_line',crossing_direction=direction,crossing_event_type='line_crossing',point=[fields[prefix+'ix'],fields[prefix+'iy']],provenance='PipeGen fields.event_N_*; class ID joined only from matching object in same frame'))
            if shape_counts!=found: raise ValueError(f'Crossing shape mismatch at frame {frame["frame"]}')
            current=Counter({(label,direction):frame['fields'][label+'_'+suffix] for label in TRAFFIC for direction,suffix in [('left_to_right','l2r'),('right_to_left','r2l')]})
            delta=Counter({key:current[key]-previous[key] for key in current if current[key]!=previous[key]})
            if delta!=found or frame['fields']['num_events']!=sum(found.values()) or frame['fields']['total_crossings']!=sum(current.values()):
                raise ValueError(f'Crossing evidence mismatch at frame {frame["frame"]}')
            previous=current
        self.summary=dict(available=True,sha256=self.sha256,frame_count=len(self.frames),duration_seconds=(self.frames[-1]['pts_ns']-self.first_pts)/1e9,first_pts_ns=self.first_pts,last_pts_ns=self.frames[-1]['pts_ns'],detection_observations=sum(observations.values()),traffic_detection_observations=sum(observations[k] for k in TRAFFIC),unique_track_ids=len(all_ids),observations_by_label=dict(observations),unique_tracks_by_label={k:len(v) for k,v in tracks.items()},class_id_labels={str(o['class_id']):o['label'] for f in self.frames for o in f['objects']},**self.stats(),gaps=['No UTC/capture timestamp: presentation timestamps and relative seconds only.','Crossing events have no confidence; class ID is joined from matching track and label in the same frame when present.','Unique tracks per class may overlap if a tracker ID changes classification; observations are not unique vehicles.'],events=self.events)
        Path(db_path).parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(db_path) as c:
            c.executescript('CREATE TABLE IF NOT EXISTS pipegen_runs (sha256 TEXT PRIMARY KEY,summary TEXT NOT NULL); CREATE TABLE IF NOT EXISTS pipegen_events (run_sha256 TEXT,event_index INTEGER,payload TEXT NOT NULL,PRIMARY KEY(run_sha256,event_index));')
            c.execute('INSERT OR IGNORE INTO pipegen_runs VALUES (?,?)',(self.sha256,json.dumps(self.summary)))
            c.executemany('INSERT OR IGNORE INTO pipegen_events VALUES (?,?,?)',[(self.sha256,e['id'],json.dumps(e)) for e in self.events])
    def stats(self, index=None):
        frame=self.frames[-1] if index is None else self.frames[index]
        fields=frame['fields'];counts={name:0 for name in CLASSES};directions={'left_to_right':0,'right_to_left':0}
        for label,name in TRAFFIC.items():
            for direction,suffix in [('left_to_right','l2r'),('right_to_left','r2l')]:
                value=fields[label+'_'+suffix];counts[name]+=value;directions[direction]+=value
        buckets=Counter(int(e['relative_seconds']) for e in self.events if e['frame_id']<=frame['frame'])
        return dict(mode='real',source='pipegen_recorded_run',counts=counts,directions=directions,total_crossings=fields['total_crossings'],activity=[dict(timestamp=f'{k}s',relative_seconds=k,count=v) for k,v in sorted(buckets.items())])
    def packet(self,index):
        index=max(0,min(index,len(self.frames)-1));f=self.frames[index];detections=[]
        for o in f['objects']:
            b=o['bbox'];detections.append(dict(track_id=str(o['id']),class_id=o['class_id'],class_name=TRAFFIC.get(o['label'],o['label']),label=o['label'],confidence=o['confidence'],tracker_confidence=o.get('tracker_confidence'),bounding_box=dict(x=b['left']/f['width'],y=b['top']/f['height'],width=b['width']/f['width'],height=b['height']/f['height'])))
        return dict(type='frame',mode='real',source='pipegen_recorded_run',camera_id='intersection-01',frame_id=f['frame'],pts_ns=f['pts_ns'],relative_seconds=(f['pts_ns']-self.first_pts)/1e9,timestamp=None,width=f['width'],height=f['height'],detections=detections,shapes=f['shapes'],events=[e for e in self.events if e['frame_id']==f['frame']],stats=self.stats(index))
