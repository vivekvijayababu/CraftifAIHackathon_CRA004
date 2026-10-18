"""TrafficFlow HTTP adapter. Real metadata must be mapped and confirmed explicitly."""
import asyncio
import csv
import io
import json
import math
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

CLASSES = ['car', 'bus', 'truck', 'motorcycle', 'bicycle', 'pedestrian']
DEFAULT_MAP = {0:'car',1:'bus',2:'truck',3:'motorcycle',4:'bicycle',5:'pedestrian'}
Mode = Literal['real','synthetic']
app = FastAPI(title='TrafficFlow AI', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173','http://127.0.0.1:5173'], allow_methods=['*'], allow_headers=['*'])
DB_PATH = os.getenv('TRAFFICFLOW_DB', str(Path(__file__).parent / 'data' / 'trafficflow.sqlite3'))
states = {}
subscribers = set()
synthetic_running = True
last_real_ingest = 0.0
synthetic_tick = 0
synthetic_task = None

def db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript('''CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, mode TEXT NOT NULL, camera_id TEXT NOT NULL, timestamp TEXT NOT NULL, class_name TEXT NOT NULL, crossing_direction TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS config (kind TEXT, key TEXT, payload TEXT, PRIMARY KEY(kind,key));''')
    return c

class Line(BaseModel):
    model_config = {'allow_inf_nan': False}
    id: str = Field(min_length=1, max_length=100)
    name: str = 'Counting line'
    x1: float = Field(ge=0,le=1)
    y1: float = Field(ge=0,le=1)
    x2: float = Field(ge=0,le=1)
    y2: float = Field(ge=0,le=1)
    enabled: bool = True
    @model_validator(mode='after')
    def nonzero(self):
        if math.hypot(self.x2-self.x1,self.y2-self.y1)<.01:
            raise ValueError('Line must have distinct endpoints')
        return self

class Camera(BaseModel):
    id: str = 'intersection-01'
    name: str = 'Intersection 01'
    width: int = Field(default=1280,gt=0)
    height: int = Field(default=720,gt=0)
    status: str = 'awaiting_pipeline'
    video_url: str = ''

class Box(BaseModel):
    model_config = {'allow_inf_nan': False}
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)

class Detection(BaseModel):
    track_id: str = Field(min_length=1)
    class_id: int
    class_name: str | None = None
    confidence: float = Field(ge=0,le=1)
    bounding_box: Box

class InferenceTransform(BaseModel):
    """Map inference pixels to unrotated source pixels before normalization."""
    model_config = {'allow_inf_nan': False}
    scale_x: float = Field(gt=0)
    scale_y: float = Field(gt=0)
    padding_x: float = 0
    padding_y: float = 0
    crop_x: float = 0
    crop_y: float = 0

class Frame(BaseModel):
    mode: Mode = 'real'
    camera_id: str = 'intersection-01'
    frame_id: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    width: int = Field(default=1280,gt=0)
    height: int = Field(default=720,gt=0)
    coordinate_space: Literal['pixels','normalized','inference'] = 'pixels'
    inference_transform: InferenceTransform | None = None
    tracker_session_id: str = 'default'
    detections: list[Detection] = Field(max_length=1000)

def get_config(kind,key,default):
    with db() as c:
        row=c.execute('SELECT payload FROM config WHERE kind=? AND key=?',(kind,key)).fetchone()
    return json.loads(row[0]) if row else default

def put_config(kind,key,payload):
    with db() as c:
        c.execute('INSERT OR REPLACE INTO config VALUES (?,?,?)',(kind,key,json.dumps(payload)))

def lines(camera_id,mode):
    return get_config('lines',f'{mode}:{camera_id}',[dict(id='main',name='Main crossing',x1=.08,y1=.5,x2=.92,y2=.5,enabled=True)])

@app.get('/health')
@app.get('/api/health')
def health():
    with db() as c: c.execute('SELECT 1')
    return dict(status='ok',database='ok',real_pipeline_connected=time.monotonic()-last_real_ingest<10,mapping_confirmed=os.getenv('PIPEGEN_MAPPING_CONFIRMED')=='true',synthetic_label='SYNTHETIC MODE — simulated development data')

@app.get('/api/cameras')
def cameras():
    return [get_config('camera','intersection-01',Camera().model_dump())]

@app.get('/api/cameras/{camera_id}')
def camera(camera_id: str):
    return get_config('camera',camera_id,Camera(id=camera_id).model_dump())

@app.put('/api/cameras/{camera_id}')
def update_camera(camera_id: str, value: Camera):
    value.id=camera_id
    put_config('camera',camera_id,value.model_dump())
    for key in list(states):
        if key[1]==camera_id: del states[key]
    return value

@app.get('/api/lines')
def get_lines(camera_id: str='intersection-01',mode:Mode='real'):
    return lines(camera_id,mode)

@app.put('/api/lines')
def set_lines(value: list[Line],camera_id:str='intersection-01',mode:Mode='real'):
    if len({line.id for line in value})!=len(value): raise HTTPException(422,'Line IDs must be unique')
    payload=[v.model_dump() for v in value]
    put_config('lines',f'{mode}:{camera_id}',payload)
    for key in list(states):
        if key[:2]==(mode,camera_id): del states[key]
    return payload

def normalize(d,frame,mapping):
    if d.class_id not in mapping: raise HTTPException(422,f'Unmapped class_id {d.class_id}')
    name=mapping[d.class_id]
    if name not in CLASSES or (d.class_name and d.class_name!=name): raise HTTPException(422,'Class name does not match configured mapping')
    b=d.bounding_box.model_dump()
    if frame.coordinate_space=='inference':
        t=frame.inference_transform
        if t is None: raise HTTPException(422,'Inference coordinates require a verified transform')
        b['x']=(b['x']-t.padding_x)/t.scale_x+t.crop_x
        b['y']=(b['y']-t.padding_y)/t.scale_y+t.crop_y
        b['width']/=t.scale_x; b['height']/=t.scale_y
    if frame.coordinate_space in ('pixels','inference'):
        for key in ['x','width']: b[key]/=frame.width
        for key in ['y','height']: b[key]/=frame.height
    if b['x']<0 or b['y']<0 or b['x']+b['width']>1.000001 or b['y']+b['height']>1.000001: raise HTTPException(422,'Bounding box outside frame; supply inference-space dimensions, remove letterbox padding first')
    return dict(track_id=d.track_id,class_id=d.class_id,class_name=name,confidence=d.confidence,bounding_box=b)

def process(frame):
    global last_real_ingest
    if frame.mode=='real' and os.getenv('PIPEGEN_MAPPING_CONFIRMED')!='true': raise HTTPException(409,'Confirm genuine PipeGen class mapping via PIPEGEN_CLASS_MAP and PIPEGEN_MAPPING_CONFIRMED=true')
    try: mapping=DEFAULT_MAP if frame.mode=='synthetic' else {int(k):v for k,v in json.loads(os.getenv('PIPEGEN_CLASS_MAP','{}')).items()}
    except (ValueError,TypeError,AttributeError): raise HTTPException(503,'Invalid PIPEGEN_CLASS_MAP')
    if len({d.track_id for d in frame.detections})!=len(frame.detections): raise HTTPException(422,'Duplicate track IDs in one frame')
    detections=[normalize(d,frame,mapping) for d in frame.detections]
    if frame.mode=='real': last_real_ingest=time.monotonic()
    emitted=[]
    now=time.monotonic()
    for key in list(states):
        if now-states[key]['seen']>120: del states[key]
    for d in detections:
        b=d['bounding_box']; p=(b['x']+b['width']/2,b['y']+b['height']/2)
        for line in lines(frame.camera_id,frame.mode):
            if not line['enabled']: continue
            dx=line['x2']-line['x1']; dy=line['y2']-line['y1']; length=math.hypot(dx,dy)
            dist=(dx*(p[1]-line['y1'])-dy*(p[0]-line['x1']))/length
            side=1 if dist>.015 else -1 if dist<-.015 else 0
            key=(frame.mode,frame.camera_id,frame.tracker_session_id,d['track_id'],line['id'])
            state=states.get(key)
            if state and frame.frame_id<=state['frame']: continue
            if not state:
                states[key]=dict(side=side,point=p,frame=frame.frame_id,last=-999,seen=now)
                continue
            state.update(frame=frame.frame_id,seen=now)
            if not side: continue
            if state['side'] and side!=state['side']:
                # Require the motion segment to intersect the finite counting segment.
                old=state['point']; olddist=(dx*(old[1]-line['y1'])-dy*(old[0]-line['x1']))/length
                t=olddist/(olddist-dist)
                hit=(old[0]+t*(p[0]-old[0]),old[1]+t*(p[1]-old[1]))
                along=((hit[0]-line['x1'])*dx+(hit[1]-line['y1'])*dy)/(length*length)
                if 0<=along<=1 and frame.timestamp.timestamp()-state['last']>=1:
                    event=dict(mode=frame.mode,timestamp=frame.timestamp.isoformat(),camera_id=frame.camera_id,frame_id=frame.frame_id,tracker_session_id=frame.tracker_session_id,**d,counting_line_id=line['id'],crossing_direction='A→B' if side>0 else 'B→A',crossing_event_type='line_crossing')
                    with db() as c:
                        cur=c.execute('INSERT INTO events(mode,camera_id,timestamp,class_name,crossing_direction,payload) VALUES (?,?,?,?,?,?)',(frame.mode,frame.camera_id,event['timestamp'],d['class_name'],event['crossing_direction'],json.dumps(event)))
                        event['id']=cur.lastrowid
                    emitted.append(event); state['last']=frame.timestamp.timestamp()
            state.update(side=side,point=p)
    return dict(type='frame',mode=frame.mode,camera_id=frame.camera_id,timestamp=frame.timestamp.isoformat(),width=frame.width,height=frame.height,detections=detections,events=emitted,stats=stats(frame.mode,frame.camera_id))

@app.post('/api/ingest')
async def ingest(frame:Frame):
    packet=process(frame)
    for ws,mode,camera_id in list(subscribers):
        if mode==frame.mode and camera_id==frame.camera_id:
            try: await ws.send_json(packet)
            except Exception: subscribers.discard((ws,mode,camera_id))
    return packet

@app.get('/api/events')
def events(mode:Mode='real',camera_id:str='intersection-01',class_name:str|None=None,direction:str|None=None,limit:int=200,since:str|None=None):
    sql='SELECT id,payload FROM events WHERE mode=? AND camera_id=?'; args=[mode,camera_id]
    for field,value in [('class_name',class_name),('crossing_direction',direction)]:
        if value: sql+=f' AND {field}=?'; args.append(value)
    if since: sql+=' AND timestamp>=?'; args.append(since)
    sql+=' ORDER BY id DESC LIMIT ?'; args.append(max(1,min(limit,10000)))
    with db() as c: rows=c.execute(sql,args).fetchall()
    return [dict(json.loads(row['payload']),id=row['id']) for row in rows]

@app.get('/api/stats')
def stats(mode:Mode='real',camera_id:str='intersection-01'):
    with db() as c:
        rows=c.execute('SELECT class_name,crossing_direction,timestamp FROM events WHERE mode=? AND camera_id=?',(mode,camera_id)).fetchall()
    counts={name:0 for name in CLASSES}; directions={'A→B':0,'B→A':0}; activity={}
    for r in rows:
        counts[r['class_name']]+=1; directions[r['crossing_direction']]+=1
        bucket=r['timestamp'][:16]; activity[bucket]=activity.get(bucket,0)+1
    return dict(mode=mode,total_crossings=len(rows),counts=counts,directions=directions,activity=[dict(timestamp=k,count=v) for k,v in sorted(activity.items())[-60:]])

@app.get('/api/export')
def export(mode:Mode='real',camera_id:str='intersection-01',format:Literal['json','csv']='json',class_name:str|None=None,direction:str|None=None):
    data=events(mode,camera_id,class_name,direction,10000)
    if format=='json': return data
    out=io.StringIO(); fields=['id','timestamp','camera_id','track_id','class_id','class_name','confidence','counting_line_id','crossing_direction','crossing_event_type','mode']
    writer=csv.DictWriter(out,fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(data)
    return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="trafficflow-events.csv"'})

@app.post('/api/synthetic/reset')
def reset():
    with db() as c: c.execute("DELETE FROM events WHERE mode='synthetic'")
    for key in list(states):
        if key[0]=='synthetic': del states[key]
    return {'status':'reset','mode':'synthetic'}

@app.websocket('/ws')
async def websocket(ws:WebSocket,mode:Mode='real',camera_id:str='intersection-01'):
    await ws.accept(); entry=(ws,mode,camera_id); subscribers.add(entry)
    if mode=='real': await ws.send_json(dict(type='heartbeat',mode='real',status='awaiting_pipeline',stats=stats(mode,camera_id)))
    # One shared generator per process prevents duplicate counts across viewers.
    global synthetic_task
    if mode=='synthetic' and (synthetic_task is None or synthetic_task.done()):
        synthetic_task=asyncio.create_task(synthetic_broadcast())
    try:
        while True:
            await ws.receive_text()
    except (WebSocketDisconnect,RuntimeError): pass
    finally: subscribers.discard(entry)


async def synthetic_broadcast():
    global synthetic_tick
    while any(mode=='synthetic' for _,mode,_ in subscribers):
        if synthetic_running:
            for camera_id in {cam for _,mode,cam in subscribers if mode=='synthetic'}:
                detections=[]
                for i,name in enumerate(CLASSES):
                    phase=(synthetic_tick*.006+i*.155)%1; cycle=int(synthetic_tick*.006+i*.155)
                    y=.03+phase*.88 if i%2==0 else .91-phase*.88
                    detections.append(dict(track_id=f'demo-{i}-{cycle}',class_id=i,class_name=name,confidence=.95,bounding_box=dict(x=.13+i*.125,y=y,width=.045 if i==5 else .065,height=.06)))
                packet=process(Frame(mode='synthetic',camera_id=camera_id,tracker_session_id='shared-demo',frame_id=synthetic_tick,coordinate_space='normalized',detections=detections))
                for entry in list(subscribers):
                    ws,mode,cam=entry
                    if mode=='synthetic' and cam==camera_id:
                        try: await ws.send_json(packet)
                        except Exception: subscribers.discard(entry)
            synthetic_tick+=1
        await asyncio.sleep(.15)

@app.post('/api/synthetic/start')
def start_synthetic():
    global synthetic_running
    synthetic_running=True
    return {'mode':'synthetic','running':True}

@app.post('/api/synthetic/stop')
def stop_synthetic():
    global synthetic_running
    synthetic_running=False
    return {'mode':'synthetic','running':False}

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

@app.get('/media/traffic.mp4')
@app.get('/media/sample.mp4')
def sample_video():
    path=Path(os.getenv('TRAFFICFLOW_VIDEO',str(Path(__file__).parents[1]/'media'/'intersection-pexels-30654965-30s-720p.mp4')))
    if not path.is_file(): raise HTTPException(404,'Sample video unavailable')
    return FileResponse(path,media_type='video/mp4')

# Mount last: API and WebSocket routes take precedence.
frontend_dist=Path(__file__).parents[1]/'frontend'/'dist'
if frontend_dist.is_dir(): app.mount('/',StaticFiles(directory=frontend_dist,html=True),name='dashboard')
