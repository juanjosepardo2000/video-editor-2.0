import subprocess
import sys
import types
from pathlib import Path

import pytest

from src.backend.audio_mixer import parse_beatmap, parse_time
from src.backend.rough_cutter import build_cut_plan, cut, remap_words
from src.backend.transcriber import transcribe


def test_beatmap_parser_preserves_existing_sfx_contract(tmp_path: Path) -> None:
    beatmap = tmp_path / "beatmap.md"
    beatmap.write_text("""| # | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|
| 1 | 00:02.5 | 00:04.0 | hi | CAPTIONS | - | - | pop, hit:impact.wav | - |
""", encoding="utf-8")
    assert parse_beatmap(beatmap) == [
        {"time": 2.5, "type": "pop", "file": None},
        {"time": 2.5, "type": "hit", "file": "impact.wav"},
    ]


def test_cut_plan_uses_20ms_padding_and_remaps_after_silence() -> None:
    words = [{"word": "hello", "start": 0.10, "end": 0.30}, {"word": "world", "start": 1.00, "end": 1.20}]
    segments, kept = build_cut_plan(words, pad_ms=20)
    assert segments == [(0.08, 0.32), (0.98, 1.22)]
    assert remap_words(kept, segments)[1] == {"word": "world", "start": 0.26, "end": 0.46}


def test_padding_bounds_are_enforced() -> None:
    try:
        build_cut_plan([], pad_ms=19)
    except ValueError as error:
        assert "between 20 and 150" in str(error)
    else:
        raise AssertionError("invalid padding should fail")


def test_auto_mode_makes_a_cut_for_an_unambiguous_filler() -> None:
    words = [
        {"word": "hello", "start": 0.10, "end": 0.30},
        {"word": "um", "start": 0.31, "end": 0.38},
        {"word": "world", "start": 0.39, "end": 0.60},
    ]
    segments, kept = build_cut_plan(words)
    assert [word["word"] for word in kept] == ["hello", "world"]
    assert segments == [(0.08, 0.32), (0.37, 0.62)]


def test_auto_mode_keeps_only_the_last_exact_repeated_phrase() -> None:
    words = [
        {"word": "esto", "start": 0.0, "end": 0.1},
        {"word": "es", "start": 0.1, "end": 0.2},
        {"word": "una", "start": 0.2, "end": 0.3},
        {"word": "prueba", "start": 0.3, "end": 0.4},
        {"word": "esto", "start": 0.4, "end": 0.5},
        {"word": "es", "start": 0.5, "end": 0.6},
        {"word": "una", "start": 0.6, "end": 0.7},
        {"word": "prueba", "start": 0.7, "end": 0.8},
    ]
    _, kept = build_cut_plan(words)
    assert [word["word"] for word in kept] == ["esto", "es", "una", "prueba"]


def test_beatmap_rejects_invalid_seconds() -> None:
    with pytest.raises(ValueError, match="below 60"):
        parse_time("00:75.0")


def test_transcriber_defaults_to_spanish_and_preserves_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_whisperx = types.SimpleNamespace(
        load_audio=lambda _: "audio",
        load_model=lambda *args, **kwargs: types.SimpleNamespace(transcribe=lambda *a, **k: {"language": "es", "segments": [{}]}),
        load_align_model=lambda **_: ("align", "metadata"),
        align=lambda *args: {"segments": [{"words": [{"word": " hola ", "start": 0, "end": 0.5}]}]},
    )
    monkeypatch.setitem(sys.modules, "whisperx", fake_whisperx)
    monkeypatch.setattr("src.backend.transcriber.available_device", lambda _: "cpu")
    output = tmp_path / "transcript.json"
    assert transcribe("video.mp4", output) == {
        "video": "video.mp4", "language": "es", "words": [{"word": "hola", "start": 0.0, "end": 0.5}]
    }


def test_ffmpeg_rough_cut_and_mix_with_temporary_ten_second_video(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise actual FFmpeg filters without committing media fixtures to the repository."""
    source, rough, mixed = tmp_path / "source.mp4", tmp_path / "rough.mp4", tmp_path / "mixed.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=160x90:r=25", "-f", "lavfi", "-i", "sine=frequency=440",
        "-t", "10", "-c:v", "libx264", "-c:a", "aac", str(source),
    ], check=True, capture_output=True)
    cut(str(source), [(0, 1), (8, 10)], str(rough))
    assert rough.is_file() and rough.stat().st_size > 0

    from src.backend import audio_mixer
    sfx_dir, music_dir = tmp_path / "sfx", tmp_path / "music"
    sfx_dir.mkdir(); music_dir.mkdir()
    for path, frequency in ((sfx_dir / "pop.wav", 880), (music_dir / "bed.wav", 220)):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency={frequency}", "-t", "1", str(path)], check=True, capture_output=True)
    beatmap = tmp_path / "beatmap.md"
    beatmap.write_text("""| # | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.5 | 00:01.0 | - | CAPTIONS | - | - | pop | - |
""", encoding="utf-8")
    monkeypatch.setattr(audio_mixer, "SFX_DIR", sfx_dir)
    monkeypatch.setattr(audio_mixer, "MUSIC_DIR", music_dir)
    audio_mixer.mix(str(rough), str(beatmap), str(mixed))
    assert mixed.is_file() and mixed.stat().st_size > 0


def test_mix_supports_the_same_sfx_used_twice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.backend import audio_mixer
    video, mixed = tmp_path / "v.mp4", tmp_path / "mixed.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=160x90:r=25", "-f", "lavfi", "-i", "sine=frequency=440",
                    "-t", "4", "-c:v", "libx264", "-c:a", "aac", str(video)], check=True, capture_output=True)
    sfx_dir, music_dir = tmp_path / "sfx", tmp_path / "music"
    sfx_dir.mkdir(); music_dir.mkdir()
    for path in (sfx_dir / "pop.wav", music_dir / "bed.wav"):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=500", "-t", "1", str(path)], check=True, capture_output=True)
    beatmap = tmp_path / "beatmap.md"
    beatmap.write_text("""| # | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|
| 1 | 00:00.5 | 00:01.0 | - | CAPTIONS | - | - | pop | - |
| 2 | 00:02.0 | 00:03.0 | - | CAPTIONS | - | - | pop | - |
""", encoding="utf-8")
    monkeypatch.setattr(audio_mixer, "SFX_DIR", sfx_dir)
    monkeypatch.setattr(audio_mixer, "MUSIC_DIR", music_dir)
    audio_mixer.mix(str(video), str(beatmap), str(mixed))
    assert mixed.is_file() and mixed.stat().st_size > 0


def test_sfx_fade_out_is_at_the_end_not_the_start() -> None:
    from src.backend.audio_mixer import sfx_fade_out
    assert sfx_fade_out(2.0) == (1.92, 0.08)
    assert sfx_fade_out(0.05) == (0.0, 0.05)


def test_sfx_remains_audible_in_the_mix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.backend import audio_mixer
    video, mixed = tmp_path / "v.mp4", tmp_path / "mixed.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=160x90:r=25", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "4", "-c:v", "libx264", "-c:a", "aac", str(video)], check=True, capture_output=True)
    sfx_dir, music_dir = tmp_path / "sfx", tmp_path / "music"
    sfx_dir.mkdir(); music_dir.mkdir()
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=800", "-t", "1.5", str(sfx_dir / "pop.wav")], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "1", str(music_dir / "bed.wav")], check=True, capture_output=True)
    beatmap = tmp_path / "beatmap.md"
    beatmap.write_text("""| # | Inicio | Fin | Speech | Escena | Visual | Texto en pantalla | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:01.0 | 00:02.0 | - | CAPTIONS | - | - | - | pop | - |
""", encoding="utf-8")
    monkeypatch.setattr(audio_mixer, "SFX_DIR", sfx_dir)
    monkeypatch.setattr(audio_mixer, "MUSIC_DIR", music_dir)
    audio_mixer.mix(str(video), str(beatmap), str(mixed))
    # Window 1.3 s to 2.3 s: after the old buggy 80 ms fade, a correct mix still carries the SFX.
    result = subprocess.run(["ffmpeg", "-hide_banner", "-ss", "1.3", "-t", "0.8", "-i", str(mixed), "-af", "volumedetect", "-f", "null", "-"],
                            capture_output=True, text=True)
    mean = float([line for line in result.stderr.splitlines() if "mean_volume" in line][0].split(":")[1].split()[0])
    assert mean > -40, f"SFX is almost silent in the mix (mean {mean} dB)"


def test_a_word_stretched_over_a_long_silence_does_not_keep_the_silence() -> None:
    words = [{"word": "hola", "start": 0.0, "end": 0.4}, {"word": "este", "start": 0.5, "end": 7.8},
             {"word": "adios", "start": 7.9, "end": 8.3}]
    segments, kept = build_cut_plan(words)
    total = sum(end - start for start, end in segments)
    assert total < 4.0, f"kept {total:.1f}s of speech; the stretched word kept the silence"


def test_music_selection_ignores_hidden_and_non_audio_files(tmp_path: Path) -> None:
    from src.backend.audio_mixer import _music_file
    music = tmp_path / "music"; music.mkdir()
    (music / ".DS_Store").write_bytes(b"x"); (music / ".gitkeep").write_bytes(b""); (music / "notes.txt").write_text("x")
    (music / "track.mp3").write_bytes(b"audio")
    beatmap = tmp_path / "beatmap.md"; beatmap.write_text("sin linea de musica", encoding="utf-8")
    assert _music_file(beatmap, music).name == "track.mp3"


def test_gain_to_target_clamps_and_handles_unknown_levels() -> None:
    from src.backend.audio_mixer import gain_to_target
    assert gain_to_target(-20.0, -40.0) == -20.0
    assert gain_to_target(None, -40.0) == 0.0
    assert gain_to_target(-5.0, -90.0) == -40.0


def test_beatmap_v2_with_broll_and_zone_columns_is_parsed_by_the_mixer_and_the_capcut_exporter() -> None:
    from src.nle_bridge.capcut_exporter import parse_beatmap as parse_for_capcut
    example = Path("pipeline/examples/beatmap.v2.example.md")
    events = parse_beatmap(example)
    assert [event["type"] for event in events] == ["pop", "whoosh", "pop", "hit"]
    beats = parse_for_capcut(example)
    assert len(beats) == 5 and beats[2].scene == "FULLSCREEN"
