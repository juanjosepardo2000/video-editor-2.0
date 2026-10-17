import json
import tempfile
import unittest
from pathlib import Path

from src.nle_bridge.capcut_exporter import export_project, load_words, parse_beatmap


HEADER = """# BeatMap

## Beats
| # | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|
"""


class CapCutExporterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="minthy-capcut-test-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name: str, content: str | bytes) -> Path:
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target

    def valid_beatmap(self) -> Path:
        return self.write("beatmap.md", HEADER +
            "| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTIONS | Hablante | - | - | hola |\n" +
            "| 2 | 00:02.0 | 00:04.0 | dato final | FULLSCREEN | Contador 25 | zoom-in | whoosh | dato |\n")

    def test_contract_rejects_legacy_table(self):
        legacy = self.write("legacy.md", "| Inicio | Fin | Texto |\n|---|---|---|\n| 0 | 1 | hola |\n")
        with self.assertRaisesRegex(ValueError, "contrato nuevo"):
            parse_beatmap(legacy)

    def test_transcript_has_priority_and_fallback_is_available(self):
        beats = parse_beatmap(self.valid_beatmap())
        transcript = self.write("transcript.json", json.dumps({"words": [
            {"word": "hola", "start": 0.1, "end": 0.5},
            {"word": "mundo", "start": 0.6, "end": 1.0},
        ]}))
        words, source = load_words(transcript, beats)
        self.assertEqual(source, "transcript")
        self.assertEqual([word.text for word in words], ["hola", "mundo"])
        fallback, fallback_source = load_words(None, beats)
        self.assertEqual(fallback_source, "uniform-fallback")
        self.assertEqual(len(fallback), 4)

    def test_export_has_tracks_keyframes_media_and_mirrors(self):
        beatmap = self.valid_beatmap()
        transcript = self.write("transcript.json", json.dumps({"words": [
            {"word": "hola", "start": 0.1, "end": 0.5},
            {"word": "mundo", "start": 0.6, "end": 1.0},
            {"word": "dato", "start": 2.1, "end": 2.5},
            {"word": "final", "start": 2.6, "end": 3.0},
        ]}))
        video = self.write("rough.mp4", b"fixture-video")
        overlay = self.write("overlay.mov", b"fixture-overlay")
        audio = self.write("voice.wav", b"fixture-audio")
        output = self.root / "project"
        export_project(video, overlay, audio, beatmap, transcript, output, "Test Project")

        draft = json.loads((output / "draft_info.json").read_text(encoding="utf-8"))
        report = json.loads((output / "validation-report.json").read_text(encoding="utf-8"))
        meta = json.loads((output / "draft_meta_info.json").read_text(encoding="utf-8"))
        self.assertTrue(report["valid"])
        self.assertEqual([track["type"] for track in draft["tracks"]], ["video", "video", "audio", "text"])
        self.assertEqual(len(draft["tracks"][0]["segments"]), 2)
        self.assertTrue(all(segment["common_keyframes"] for segment in draft["tracks"][0]["segments"]))
        self.assertEqual(len(draft["tracks"][3]["segments"]), 4)
        self.assertEqual(len(meta["draft_materials"][0]["value"]), 3)
        self.assertEqual((output / "draft_info.json").read_bytes(), (output / "draft_content.json").read_bytes())
        for material in [*draft["materials"]["videos"], *draft["materials"]["audios"]]:
            self.assertTrue((output / material["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
