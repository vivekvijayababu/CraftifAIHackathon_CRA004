"""Recorded-run adapter checks use the committed genuine metadata snapshot."""
import importlib.util
import json
import sqlite3
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('pipegen_adapter',Path(__file__).parents[1]/'pipegen.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SNAPSHOT=Path(__file__).parents[2]/'evidence'/'pipegen'/'metadata.json'

@pytest.fixture
def run(tmp_path):
    if not SNAPSHOT.is_file(): pytest.skip('Genuine evidence snapshot not present')
    return m.RecordedRun(SNAPSHOT,tmp_path/'run.db')

def test_verified_run_counts_and_event_provenance(run):
    assert run.summary['sha256']=='51f80e7a468d185c628b6bc52168efb37aa43c20fcbcc28586e7286a6c223f30'
    assert run.summary['frame_count']==900
    assert run.summary['detection_observations']==7857
    assert run.summary['traffic_detection_observations']==6651
    assert run.summary['unique_track_ids']==130
    assert run.stats()['counts']==dict(car=20,bus=0,truck=0,motorcycle=3,bicycle=0,pedestrian=5)
    assert run.stats()['directions']==dict(left_to_right=24,right_to_left=4)
    assert len(run.events)==28
    assert run.events[0]['source_event_id']=='2:1'
    assert run.events[0]['track_id']=='2'
    assert run.events[0]['timestamp'] is None
    assert run.events[0]['class_id']==2

def test_replay_does_not_change_final_counts(run):
    assert run.packet(0)['stats']['total_crossings']==0
    assert run.packet(20)['stats']['total_crossings']==1
    assert run.packet(899)['stats']['total_crossings']==28
    assert run.packet(0)['relative_seconds']==0
    assert run.packet(1)['detections'][0]['bounding_box']['x']==1200.8/1280
    assert run.stats()['total_crossings']==28

def test_import_idempotent_and_readonly(run,tmp_path):
    database=tmp_path/'repeat.db'
    before=SNAPSHOT.read_bytes()
    m.RecordedRun(SNAPSHOT,database);m.RecordedRun(SNAPSHOT,database)
    with sqlite3.connect(database) as c:
        assert c.execute('SELECT count(*) FROM pipegen_runs').fetchone()[0]==1
        assert c.execute('SELECT count(*) FROM pipegen_events').fetchone()[0]==28
    assert SNAPSHOT.read_bytes()==before

def test_rejects_unverified_crossing_delta(tmp_path):
    if not SNAPSHOT.is_file(): pytest.skip('Genuine evidence snapshot not present')
    data=json.loads(SNAPSHOT.read_text());data['frames'][20]['fields']['car_l2r']=2
    bad=tmp_path/'bad.json';bad.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Crossing evidence mismatch'):
        m.RecordedRun(bad,tmp_path/'bad.db')

def test_recorded_api_and_synthetic_isolation(run,tmp_path,monkeypatch):
    spec=importlib.util.spec_from_file_location('recorded_api',Path(__file__).parents[1]/'app.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    monkeypatch.setattr(a,'recorded_run',run)
    monkeypatch.setattr(a,'DB_PATH',str(tmp_path/'api.db'))
    assert a.pipegen_summary()['available'] is True
    assert a.stats('real')['total_crossings']==28
    assert a.stats('synthetic')['total_crossings']==0
    assert len(a.events('real'))==28
    assert len(a.events('real',class_name='pedestrian'))==5
    assert len(a.events('real',direction='right_to_left'))==4
    assert a.pipegen_frame(seconds=0)['stats']['total_crossings']==0
    assert a.pipegen_frame(seconds=30)['stats']['total_crossings']==28
    assert a.get_lines()[0]['x1']==.5
    assert a.get_lines()[0]['y1']==100/720
    with pytest.raises(a.HTTPException) as exc:
        a.set_lines([],mode='real')
    assert exc.value.status_code==409
    exported=a.export('real',format='csv').body.decode()
    assert 'relative_seconds' in exported and 'left_to_right' in exported
