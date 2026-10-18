import importlib.util
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parents[2]

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'backend' / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def test_prefix_counts_pause_restart_and_unique_events(tmp_path):
    run = module('replay_recorded', 'pipegen.py').RecordedRun(ROOT/'evidence/pipegen/metadata.json', tmp_path/'run.db')
    replay = module('replay_index', 'replay.py').ReplayIndex(run)
    assert replay.packet(0)['stats']['total_crossings'] == 0
    assert replay.packet(0)['summary']['traffic_detection_observations'] == 0
    for event in run.events:
        before = replay.packet(max(0, event['relative_seconds']-0.000001))
        after = replay.packet(event['relative_seconds'])
        assert event['source_event_id'] not in {e['source_event_id'] for e in before['events']}
        assert event['source_event_id'] in {e['source_event_id'] for e in after['events']}
    mid = replay.packet(15)
    assert mid == replay.packet(15)  # paused playback never increments
    end = replay.packet(30)
    assert end['stats']['total_crossings'] == 28
    assert end['summary']['traffic_detection_observations'] == 6651
    assert end['summary']['detection_observations'] == 7857
    assert end['summary']['unique_track_ids'] == 130
    assert len({e['source_event_id'] for e in end['events']}) == 28
    assert replay.packet(0)['events'] == []  # restart/seek does not append
    assert replay.packet(30) == end
    assert run.stats()['total_crossings'] == 28  # stable mode unchanged
    with sqlite3.connect(tmp_path/'run.db') as db:
        assert db.execute('SELECT count(*) FROM pipegen_events').fetchone()[0] == 28

def test_prefix_observations_match_original_frames(tmp_path):
    from collections import Counter
    run = module('prefix_run', 'pipegen.py').RecordedRun(ROOT/'evidence/pipegen/metadata.json',tmp_path/'p.db')
    replay = module('prefix_replay','replay.py').ReplayIndex(run)
    for index in [0,1,20,450,899]:
        time = (run.frames[index]['pts_ns']-run.first_pts)/1e9
        packet = replay.packet(time)
        expected = Counter(o['label'] for f in run.frames[:index+1] for o in f['objects'])
        assert packet['frame_id'] == index
        assert packet['summary']['observations_by_label'] == dict(expected)
        assert len(packet['events']) == packet['stats']['total_crossings']

def test_replay_http_validation_exports_and_isolation(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    app = module('replay_api','app.py')
    monkeypatch.setattr(app,'DB_PATH',str(tmp_path/'api.db'))
    with TestClient(app.app) as client:
        assert client.get('/api/replay?seconds=-1').status_code == 422
        assert client.get('/api/replay?seconds=nan').status_code == 422
        assert client.get('/api/replay?seconds=inf').status_code == 422
        assert client.get('/api/replay?seconds=0').json()['stats']['total_crossings'] == 0
        assert client.get('/api/replay?seconds=30').json()['stats']['total_crossings'] == 28
        assert len(client.get('/api/replay/export?seconds=30&direction=right_to_left').json()) == 4
        assert len(client.get('/api/replay/export?seconds=15&class_name=pedestrian').json()) == 4
        assert 'source_event_id' in client.get('/api/replay/export?seconds=30&format=csv').text
        assert client.get('/api/stats?mode=real').json()['total_crossings'] == 28
        assert client.get('/api/stats?mode=synthetic').json()['total_crossings'] == 0
        monkeypatch.setattr(app,'recorded_run',None)
        assert client.get('/api/replay').status_code == 503
        assert client.get('/api/health').status_code == 200
