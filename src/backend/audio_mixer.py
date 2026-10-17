"""Inyecta SFX y regula el volumen de la música de fondo."""
from pathlib import Path

SFX_DIR = Path("assets/sfx")
MUSIC_DIR = Path("assets/music")
MUSIC_DB_RANGE = (-23, -20)  # dB relativos a la voz


def mix(video_path: str, beatmap_path: str = "pipeline/beatmap.md", output_path: str = "pipeline/mixed.mp4") -> None:
    """Mezcla voz + música (-20/-23 dB) + SFX según el beatmap."""
    # TODO: parsear beatmap, aplicar volume/amix/adelay con ffmpeg-python.
    raise NotImplementedError


if __name__ == "__main__":
    print("audio_mixer: stub — implementar mix()")
