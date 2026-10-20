"""Detect faces at 10 fps in the displayed orientation of a video."""
import argparse
import json
import math
import subprocess
from pathlib import Path
from types import SimpleNamespace

FPS = 10


def dimensions(video: str) -> tuple[int, int]:
    info = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json", video
    ]))
    stream = info["streams"][0]
    rotation = next((item["rotation"] for item in stream.get("side_data_list", []) if "rotation" in item),
                    stream.get("tags", {}).get("rotate", 0))
    width, height = int(stream["width"]), int(stream["height"])
    if round(float(rotation)) % 180 == 90:
        width, height = height, width
    return width, height


def expanded_box(box, confidence: float) -> dict | None:
    """Add 10% of the face size on each side, clipped to the image."""
    x1, y1 = max(0., box.xmin - box.width * .1), max(0., box.ymin - box.height * .1)
    x2, y2 = min(1., box.xmin + box.width * 1.1), min(1., box.ymin + box.height * 1.1)
    if x2 <= x1 or y2 <= y1:
        return None
    return dict(x=x1, y=y1, w=x2-x1, h=y2-y1, conf=max(0., min(1., float(confidence))))


def smooth(boxes: list[dict], previous: list[dict]) -> list[dict]:
    """Match nearby faces one-to-one; never invent detections for missing faces."""
    remaining = previous.copy()
    result = []
    for box in boxes:
        cx, cy = box['x'] + box['w']/2, box['y'] + box['h']/2
        if remaining:
            closest = min(remaining, key=lambda b: (cx-b['x']-b['w']/2)**2 + (cy-b['y']-b['h']/2)**2)
            distance = ((cx-closest['x']-closest['w']/2)**2 + (cy-closest['y']-closest['h']/2)**2)**.5
            if distance < max(box['w'], box['h'], closest['w'], closest['h']):
                remaining.remove(closest)
                # Keep the current detection covered even while smoothing its position.
                x = min(box['x'], .5 * (box['x'] + closest['x']))
                y = min(box['y'], .5 * (box['y'] + closest['y']))
                right = max(box['x'] + box['w'], .5 * (box['x'] + box['w'] + closest['x'] + closest['w']))
                bottom = max(box['y'] + box['h'], .5 * (box['y'] + box['h'] + closest['y'] + closest['h']))
                box = dict(x=x, y=y, w=right-x, h=bottom-y, conf=box['conf'])
        result.append(box)
    return result


def track(video: str, output: Path) -> dict:
    import cv2
    import numpy as np

    width, height = dimensions(video)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if detector.empty():
        raise RuntimeError('OpenCV face detector could not be loaded')
    # FFmpeg autorotates by default before filters, so pixels and dimensions agree.
    process = subprocess.Popen(['ffmpeg', '-v', 'error', '-nostdin', '-i', video, '-vf', 'fps=10',
                                '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    frames, previous = [], []
    try:
        size = width * height * 3
        while True:
            data = process.stdout.read(size)
            if not data:
                break
            if len(data) != size:
                raise RuntimeError('Incomplete decoded frame')
            image = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            rects, _, weights = detector.detectMultiScale3(gray, scaleFactor=1.1, minNeighbors=5,
                                                             minSize=(30, 30), outputRejectLevels=True)
            boxes = []
            for (x, y, w, h), weight in zip(rects, weights):
                box = SimpleNamespace(xmin=x/width, ymin=y/height, width=w/width, height=h/height)
                # Haar weights are uncalibrated scores, mapped to [0, 1], not probabilities.
                score = 1 / (1 + math.exp(-max(-30, min(30, float(weight)))))
                detected = expanded_box(box, score)
                if detected is not None:
                    boxes.append(detected)
            boxes = smooth(boxes, previous)
            frames.append({'t': len(frames)/FPS, 'boxes': boxes})
            previous = boxes
        if process.wait() != 0:
            raise RuntimeError('FFmpeg failed to decode the video')
        if not frames:
            raise RuntimeError('Video contains no decodable frames')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
    result = {'fps': FPS, 'width': width, 'height': height, 'source': str(video), 'frames': frames}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video')
    parser.add_argument('--out', type=Path, default=Path('pipeline/face_boxes.json'))
    args = parser.parse_args()
    track(args.video, args.out)


if __name__ == '__main__':
    main()
