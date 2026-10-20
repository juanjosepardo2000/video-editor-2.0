import json
import subprocess
from types import SimpleNamespace

import pytest

from src.backend.face_tracker import dimensions, expanded_box, smooth, track


def test_expansion_clips_to_frame():
    box = expanded_box(SimpleNamespace(xmin=-.02, ymin=.2, width=.4, height=.3), .9)
    assert box['x'] == 0
    assert box['y'] == pytest.approx(.17)
    assert box['w'] == pytest.approx(.42)
    assert box['h'] == pytest.approx(.36)
    assert expanded_box(SimpleNamespace(xmin=2, ymin=2, width=.1, height=.1), .8) is None


def test_smoothing_keeps_current_face_and_no_phantom_faces():
    old = [dict(x=.1, y=.1, w=.2, h=.2, conf=.9)]
    current = [dict(x=.2, y=.1, w=.2, h=.2, conf=.8)]
    result = smooth(current, old)
    assert result[0]['x'] <= current[0]['x']
    assert result[0]['x'] + result[0]['w'] >= current[0]['x'] + current[0]['w']
    assert smooth([], old) == []
    assert len(smooth(current * 2, old)) == 2


def test_rotated_dimensions(monkeypatch):
    stream = {'streams': [{'width': 1280, 'height': 720, 'side_data_list': [{'rotation': 90}]}]}
    monkeypatch.setattr(subprocess, 'check_output', lambda *a, **k: json.dumps(stream).encode())
    assert dimensions('video.mp4') == (720, 1280)


def test_real_decoder_empty_frames(tmp_path):
    pytest.importorskip('cv2')
    video = tmp_path / 'empty.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=black:s=96x160:r=20',
                    '-t', '1', '-c:v', 'libx264', str(video)], check=True)
    output = tmp_path / 'faces.json'
    data = track(str(video), output)
    assert (data['width'], data['height'], data['fps']) == (96, 160, 10)
    assert len(data['frames']) == 10
    assert all(frame['boxes'] == [] for frame in data['frames'])
    assert json.loads(output.read_text(encoding='utf-8')) == data


def test_decoder_applies_rotation_metadata(tmp_path):
    pytest.importorskip('cv2')
    original, rotated = tmp_path / 'wide.mp4', tmp_path / 'rotated.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=black:s=160x96:r=10',
                    '-t', '1', '-c:v', 'libx264', str(original)], check=True)
    help_text = subprocess.run(['ffmpeg', '-h', 'full'], capture_output=True, text=True, check=True).stdout
    if '-display_rotation' in help_text:
        rotation_args = ['-display_rotation', '90', '-i', str(original), '-c', 'copy']
    else:
        rotation_args = ['-i', str(original), '-c', 'copy', '-metadata:s:v:0', 'rotate=90']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *rotation_args, str(rotated)], check=True)
    data = track(str(rotated), tmp_path / 'faces.json')
    assert (data['width'], data['height']) == (96, 160)
    assert len(data['frames']) == 10
