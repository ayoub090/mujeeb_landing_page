"""Render Mujeeb's two landing-page showcase videos from local product frames.

The recording frames are generated from the development-only React studio.
Only the final MP4 assets are written to the public frontend directory.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / ".video-work" / "frames"
AUDIO = ROOT / ".video-work" / "audio"
RENDER = ROOT / ".video-work" / "render"
OUTPUT = ROOT / "frontend" / "public" / "videos"
FPS = 60
TRANSITION = 0.55


def run(*args: str) -> None:
    subprocess.run([str(arg) for arg in args], check=True)


def render_still(ffmpeg: str, image: Path, duration: float, output: Path, zoom_in: bool) -> None:
    frames = round(duration * FPS)
    zoom = "min(zoom+0.00038,1.035)" if zoom_in else "if(lte(zoom,1.001),1.035,max(1.001,zoom-0.00038))"
    video_filter = (
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,"
        f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s=1920x1080:fps={FPS},format=yuv420p"
    )
    run(
        ffmpeg, "-y", "-loop", "1", "-i", str(image),
        "-vf", video_filter, "-t", f"{duration:.3f}", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-movflags", "+faststart", str(output),
    )


def stitch(ffmpeg: str, clips: list[Path], durations: list[float], output: Path, total: float) -> None:
    args = [ffmpeg, "-y"]
    for clip in clips:
        args.extend(["-i", str(clip)])

    filters: list[str] = []
    elapsed = durations[0]
    previous = "[0:v]"
    for index in range(1, len(clips)):
        offset = elapsed - TRANSITION * index
        target = f"[x{index}]"
        filters.append(
            f"{previous}[{index}:v]xfade=transition=fade:duration={TRANSITION}:"
            f"offset={offset:.3f}{target}"
        )
        previous = target
        elapsed += durations[index]

    args.extend([
        "-filter_complex", ";".join(filters), "-map", previous,
        "-t", f"{total:.3f}", "-r", str(FPS), "-c:v", "libx264",
        "-preset", "medium", "-b:v", "8M", "-minrate", "8M", "-maxrate", "8M",
        "-bufsize", "16M", "-x264-params", "nal-hrd=cbr:force-cfr=1",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output),
    ])
    run(*args)


def add_voice(ffmpeg: str, visual: Path, voice: Path, output: Path, total: float) -> None:
    audio_filter = f"[1:a]adelay=900|900,volume=1.08,apad=pad_dur={total:.3f},afade=t=in:st=0.9:d=0.25[voice]"
    run(
        ffmpeg, "-y", "-i", str(visual), "-i", str(voice),
        "-filter_complex", audio_filter, "-map", "0:v:0", "-map", "[voice]",
        "-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-movflags", "+faststart", str(output),
    )


def render_video(
    ffmpeg: str,
    name: str,
    scene_names: list[str],
    durations: list[float],
    total: float,
    voice_name: str,
    public_name: str,
) -> None:
    clips: list[Path] = []
    for index, (scene, duration) in enumerate(zip(scene_names, durations, strict=True)):
        source = FRAMES / f"{scene}.png"
        if not source.exists():
            raise FileNotFoundError(source)
        clip = RENDER / f"{name}-{index:02d}.mp4"
        render_still(ffmpeg, source, duration, clip, zoom_in=index % 2 == 0)
        clips.append(clip)

    visual = RENDER / f"{name}-visual.mp4"
    stitch(ffmpeg, clips, durations, visual, total)
    add_voice(ffmpeg, visual, AUDIO / voice_name, OUTPUT / public_name, total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["onboarding", "workflow", "all"], default="all")
    args = parser.parse_args()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    RENDER.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    if args.only in {"onboarding", "all"}:
        render_video(
            ffmpeg,
            name="onboarding",
            scene_names=["onboarding-salla", "onboarding-qr", "onboarding-ready", "onboarding-end"],
            durations=[8.5, 9.5, 9.0, 9.65],
            total=35.0,
            voice_name="vo_onboarding_ar.mp3",
            public_name="video1_onboarding.mp4",
        )
    if args.only in {"workflow", "all"}:
        render_video(
            ffmpeg,
            name="workflow",
            scene_names=["workflow-incoming", "workflow-confirm", "workflow-location", "workflow-synced", "workflow-end"],
            durations=[9.0, 12.0, 12.0, 9.0, 8.2],
            total=48.0,
            voice_name="vo_workflow_ar.mp3",
            public_name="video2_workflow.mp4",
        )
    shutil.rmtree(RENDER, ignore_errors=True)


if __name__ == "__main__":
    main()
