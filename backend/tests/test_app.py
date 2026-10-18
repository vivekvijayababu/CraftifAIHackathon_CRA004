import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

spec=importlib.util.spec_from_file_location('traffic_app',Path(__file__).parents[1]/'app.py')
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(a,'DB_PATH',str(tmp_path/'test.db')); a.states.clear()
    with TestClient(a.app) as connection:
        yield connection

def frame(y,frame_id=0,track='one',mode='synthetic',**extra):
    return dict(mode=mode,camera_id='intersection-01',frame_id=frame_id,timestamp=(datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(seconds=frame_id)).isoformat(),coordinate_space='normalized',detections=[dict(track_id=track,class_id=0,confidence=.9,bounding_box=dict(x=.4,y=y,width=.1,height=.05))],**extra)

def test_health_and_validation(client):
    assert client.get('/health').json()['database']=='ok'
    assert client.post('/api/ingest',json=frame(.2,mode='real')).status_code==409
    bad=frame(.2); bad['detections'][0]['class_id']=99
    assert client.post('/api/ingest',json=bad).status_code==422
    bad=frame(.98)
    assert client.post('/api/ingest',json=bad).status_code==422

def test_crossing_debounce_direction_history_isolation(client):
    for n,y in enumerate([.3,.47,.48,.51,.6,.61]):
        assert client.post('/api/ingest',json=frame(y,n)).status_code==200
    assert client.get('/api/stats?mode=synthetic').json()['total_crossings']==1
    assert client.post('/api/ingest',json=frame(.6,5)).json()['events']==[]
    assert client.post('/api/ingest',json=frame(.3,7)).json()['events'][0]['crossing_direction']=='B→A'
    assert client.get('/api/stats?mode=real').json()['total_crossings']==0
    assert len(client.get('/api/events?mode=synthetic&class_name=car').json())==2
    assert len(client.get('/api/events?mode=synthetic&class_name=bus').json())==0
    assert 'line_crossing' in client.get('/api/export?mode=synthetic&format=csv').text

def test_track_changes_and_finite_segment(client):
    client.post('/api/ingest',json=frame(.2))
    client.post('/api/ingest',json=frame(.7,1,track='new'))
    assert client.get('/api/stats?mode=synthetic').json()['total_crossings']==0
    for i,y in enumerate([.2,.7]):
        f=frame(y,i,track='outside'); f['detections'][0]['bounding_box']['x']=.94; f['detections'][0]['bounding_box']['width']=.02
        client.post('/api/ingest',json=f)
    assert client.get('/api/stats?mode=synthetic').json()['total_crossings']==0

def test_persistence_scaling_and_mapping(client,monkeypatch):
    line=[dict(id='custom',name='custom',x1=0,y1=.5,x2=1,y2=.5)]
    assert client.put('/api/lines?mode=real',json=line).status_code==200
    assert client.get('/api/lines?mode=real').json()[0]['id']=='custom'
    assert client.get('/api/lines?mode=synthetic').json()[0]['id']=='main'
    monkeypatch.setenv('PIPEGEN_MAPPING_CONFIRMED','true'); monkeypatch.setenv('PIPEGEN_CLASS_MAP','{"12":"pedestrian"}')
    for n,y in enumerate([100,500]):
        f=frame(.2,n,mode='real'); f.update(width=1000,height=1000,coordinate_space='pixels')
        f['detections'][0].update(class_id=12,bounding_box=dict(x=400,y=y,width=100,height=100))
        result=client.post('/api/ingest',json=f)
        assert result.status_code==200
        assert result.json()['detections'][0]['bounding_box']['width']==.1
    assert client.get('/api/stats').json()['counts']['pedestrian']==1
    a.states.clear()
    assert len(client.get('/api/events').json())==1

def test_websockets_and_reset(client):
    with client.websocket_connect('/ws?mode=synthetic') as ws:
        data=ws.receive_json(); assert data['mode']=='synthetic'; assert len(data['detections'])==6
    with client.websocket_connect('/ws?mode=real') as ws:
        assert ws.receive_json()['status']=='awaiting_pipeline'
    assert client.post('/api/synthetic/reset').json()['mode']=='synthetic'

def test_invalid_lines_and_camera(client):
    assert client.put('/api/lines',json=[dict(id='bad',x1=.5,y1=.5,x2=.5,y2=.5)]).status_code==422
    assert client.put('/api/cameras/intersection-01',json=dict(name='North',width=1920,height=1080)).status_code==200
    assert client.get('/api/cameras').json()[0]['width']==1920

def test_duplicate_ids_and_tracker_session_reset(client):
    f=frame(.2); f['detections'].append(f['detections'][0].copy())
    assert client.post('/api/ingest',json=f).status_code==422
    client.post('/api/ingest',json=frame(.2,tracker_session_id='before'))
    client.post('/api/ingest',json=frame(.7,1,tracker_session_id='after'))
    assert client.get('/api/stats?mode=synthetic').json()['total_crossings']==0

def test_hysteresis_and_short_debounce(client):
    client.post('/api/ingest',json=frame(.2,0))
    for n,y in enumerate([.47,.48,.47,.48],1):
        assert client.post('/api/ingest',json=frame(y,n)).json()['events']==[]
    crossing=frame(.7,5)
    assert len(client.post('/api/ingest',json=crossing).json()['events'])==1
    return_frame=frame(.2,6); return_frame['timestamp']=crossing['timestamp']
    assert client.post('/api/ingest',json=return_frame).json()['events']==[]

def test_shared_websocket_tracks(client):
    with client.websocket_connect('/ws?mode=synthetic') as first:
        a1=first.receive_json()
        with client.websocket_connect('/ws?mode=synthetic') as second:
            b=second.receive_json()
            assert a1['detections'][0]['track_id']==b['detections'][0]['track_id']
    assert client.post('/api/synthetic/stop').json()['running'] is False
    assert client.post('/api/synthetic/start').json()['running'] is True

def test_inference_transform_and_duplicate_tracks(client):
    f=frame(.2)
    f.update(coordinate_space='inference',width=1280,height=720,inference_transform=dict(scale_x=.5,scale_y=.5,padding_x=0,padding_y=140))
    f['detections'][0]['bounding_box']=dict(x=64,y=176,width=64,height=36)
    r=client.post('/api/ingest',json=f)
    assert r.status_code==200
    assert r.json()['detections'][0]['bounding_box']==dict(x=.1,y=.1,width=.1,height=.1)
    f['inference_transform']=None
    assert client.post('/api/ingest',json=f).status_code==422
    f=frame(.2); f['detections']*=2
    assert client.post('/api/ingest',json=f).status_code==422

def test_session_reset_and_close_jitter(client):
    f=frame(.3); f['tracker_session_id']='session-1'; client.post('/api/ingest',json=f)
    f=frame(.6,1); f['tracker_session_id']='session-2'
    assert client.post('/api/ingest',json=f).json()['events']==[]
    for n,y in enumerate([.46,.475,.48,.47],2):
        client.post('/api/ingest',json=frame(y,n,track='jitter'))
    assert client.get('/api/stats?mode=synthetic').json()['total_crossings']==0

def test_camera_source_configuration(client):
    body=dict(name='Intersection',video_url='/media/sample.mp4',width=1280,height=720)
    assert client.put('/api/cameras/intersection-01',json=body).status_code==200
    assert client.get('/api/cameras/intersection-01').json()['video_url']=='/media/sample.mp4'
