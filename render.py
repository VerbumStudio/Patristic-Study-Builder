import asyncio
import os
import subprocess
import PIL.Image

# Pillow ANTIALIAS compatibility patch
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

import edge_tts
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

TARGET_W, TARGET_H = 1080, 1920
FPS = 30
VOICE = "en-US-ChristopherNeural"
OUTRO_IMAGE = "ai_prompt_library.png"
BGM_FILE = "background_music.mp3"

async def generate_speech(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="+10%", pitch="-2Hz")
    await communicate.save(output_path)

def process_visual_clip(video_path: str, duration: float, scene_id: int = 1) -> VideoFileClip:
    clip = VideoFileClip(video_path).without_audio()
    clip = clip.loop(duration=duration) if clip.duration < duration else clip.subclip(0, duration)

    clip = clip.resize(height=TARGET_H)
    if clip.w < TARGET_W:
        clip = clip.resize(width=TARGET_W)

    # 1.35x overscale to eliminate all corner watermarks
    clip = clip.resize(1.35)

    x_center = (clip.w - TARGET_W) / 2
    y_center = min((clip.h - TARGET_H) / 2 + 120, clip.h - TARGET_H)

    # Scene 3: Frame the city skyline and crop out head
    if scene_id == 3:
        x_center = min(x_center + 240, clip.w - TARGET_W)
        y_center = clip.h - TARGET_H

    return clip.crop(x1=x_center, y1=y_center, width=TARGET_W, height=TARGET_H)

def create_bordered_box(box_w, box_h, border_thick, duration, pos_y):
    cyan_bg = ColorClip(size=(box_w, box_h), color=(0, 240, 255)).set_duration(duration).set_position(("center", pos_y))
    inner_w = box_w - (border_thick * 2)
    inner_h = box_h - (border_thick * 2)
    dark_inner = ColorClip(size=(inner_w, inner_h), color=(11, 19, 43)).set_opacity(0.94).set_duration(duration).set_position(("center", pos_y + border_thick))
    return [cyan_bg, dark_inner]

def build_scene(scene_data):
    tts_path = f"temp_vo_{scene_data['id']}.mp3"
    asyncio.run(generate_speech(scene_data["text"], tts_path))

    audio = AudioFileClip(tts_path)
    scene_duration = audio.duration + 0.50
    elements = []

    if scene_data.get("is_outro", False):
        bg_video = process_visual_clip("scene4.mp4", scene_duration, scene_id=5)
        dark_wash = ColorClip(size=(TARGET_W, TARGET_H), color=(5, 10, 25)).set_opacity(0.80).set_duration(scene_duration)
        elements.extend([bg_video, dark_wash])

        if os.path.exists(OUTRO_IMAGE):
            img = ImageClip(OUTRO_IMAGE).set_duration(scene_duration)
            if img.w > 1000:
                img = img.resize(width=1000)
            if img.h > 1050:
                img = img.resize(height=1050)
            img = img.set_position(("center", 180))
            elements.append(img)
    else:
        base = process_visual_clip(scene_data["file"], scene_duration, scene_id=scene_data["id"])
        dark_overlay = ColorClip(size=(TARGET_W, TARGET_H), color=(0, 0, 0)).set_opacity(0.20).set_duration(scene_duration)
        elements.extend([base, dark_overlay])

    BOX_W, BOX_H = 960, 260
    POS_Y = 1320
    BORDER_T = 4

    border_elements = create_bordered_box(BOX_W, BOX_H, BORDER_T, scene_duration, POS_Y)
    elements.extend(border_elements)

    headline = TextClip(
        scene_data["headline"],
        fontsize=40,
        color="#00F0FF",
        font="DejaVu-Sans-Bold",
        method="caption",
        size=(880, None)
    ).set_duration(scene_duration).set_position(("center", POS_Y + 28))

    body = TextClip(
        scene_data["body"],
        fontsize=28,
        color="white",
        font="DejaVu-Sans",
        method="caption",
        size=(880, None)
    ).set_duration(scene_duration).set_position(("center", POS_Y + 105))

    elements.extend([headline, body])

    composite = CompositeVideoClip(elements, size=(TARGET_W, TARGET_H)).set_duration(scene_duration)
    return composite, audio

def main():
    scenes = [
        {
            "id": 1,
            "file": "scene1.mp4",
            "headline": "8:45 PM. \"QUICK QUESTION.\"",
            "body": "A late client ping hits your phone.\nThe off-hours anxiety cycle begins.",
            "text": "It's 8:45 on a Friday. A late client ping hits your phone.",
            "is_outro": False
        },
        {
            "id": 2,
            "file": "scene2.mp4",
            "headline": "THE GUILT-DRIVEN \"YES\"",
            "body": "Spending 10 minutes drafting an apology\njust for being off the clock.",
            "text": "You spend ten minutes drafting an apology just for being off the clock.",
            "is_outro": False
        },
        {
            "id": 3,
            "file": "scene3.mp4",
            "headline": "EXECUTIVE BOUNDARY DEFENSE",
            "body": "Stop trading peace for approval.\nFrame boundaries as commercial trade-offs.",
            "text": "Stop trading peace for approval. High-level operators don't apologize for boundaries—they frame them as commercial trade-offs.",
            "is_outro": False
        },
        {
            "id": 4,
            "file": "scene4.mp4",
            "headline": "OPTION A  vs.  OPTION B",
            "body": "Standard delivery Monday morning.\nOr emergency sprint at 1.5x. Zero guilt.",
            "text": "Option A: Standard delivery Monday morning. Option B: Emergency sprint at 1.5x. Zero guilt. Total authority.",
            "is_outro": False
        },
        {
            "id": 5,
            "file": None,
            "headline": "BEACONS.AI/WORKFLOWSUPERAI",
            "body": "System 1: Executive Boundary Defense\nInstant Download | Prompt Vault in Bio",
            "text": "Deploy the boundary protocol. Grab the prompt vault in the bio.",
            "is_outro": True
        },
    ]

    video_clips, audio_clips = [], []
    for s in scenes:
        print(f"[*] Building Scene {s['id']}...")
        v, a = build_scene(s)
        video_clips.append(v)
        audio_clips.append(a)

    print("[*] Concatenating timeline...")
    final_video = concatenate_videoclips(video_clips, method="compose", padding=-0.35)
    vocal_track = concatenate_audioclips(audio_clips)

    temp_stage_video = "temp_stage_video.mp4"
    final_video = final_video.set_audio(vocal_track)
    final_video.write_videofile(
        temp_stage_video,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )

    output = "guilt_driven_yes_master.mp4"
    if os.path.exists(BGM_FILE) and os.path.getsize(BGM_FILE) > 500:
        print(f"[*] Mixing synthesized BGM stem ({BGM_FILE}) via FFmpeg...")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", temp_stage_video,
            "-stream_loop", "-1", "-i", BGM_FILE,
            "-filter_complex", "[1:a]volume=0.30[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[!] FFmpeg mix error:\n{result.stderr}")
            os.rename(temp_stage_video, output)
        else:
            print("[✓] Dark tech synth track mixed successfully into final reel!")
            if os.path.exists(temp_stage_video):
                os.remove(temp_stage_video)
    else:
        print("[!] No BGM file generated, retaining voiceover.")
        os.rename(temp_stage_video, output)

    print(f"[✓] Render finished: {output}")

if __name__ == "__main__":
    main()
