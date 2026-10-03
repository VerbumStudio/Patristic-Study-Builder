import asyncio
import os
import urllib.request
import PIL.Image

# Pillow ANTIALIAS compatibility patch
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

import edge_tts
from moviepy.audio.fx.all import audio_loop, volumex
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
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

DEFAULT_BGM_URL = "https://raw.githubusercontent.com/VerbumStudio/assets/main/cyber_pulse.mp3"
BACKUP_BGM_URL = "https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/f1XJ1B98e7Lp7E1p.mp3"

def ensure_background_music():
    """Fetches background music asset if missing."""
    if not os.path.exists(BGM_FILE):
        print("[*] Downloading background music track...")
        try:
            req = urllib.request.Request(DEFAULT_BGM_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response, open(BGM_FILE, 'wb') as out_file:
                out_file.write(response.read())
            print(f"[✓] Background music successfully downloaded to {BGM_FILE}")
        except Exception as e:
            print(f"[!] Primary URL failed ({e}), attempting fallback...")
            try:
                req = urllib.request.Request(BACKUP_BGM_URL, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as response, open(BGM_FILE, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"[✓] Fallback background music downloaded.")
            except Exception as e2:
                print(f"[!] Warning: Could not download music automatically ({e2}).")

async def generate_speech(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="+10%", pitch="-2Hz")
    await communicate.save(output_path)

def process_visual_clip(video_path: str, duration: float) -> VideoFileClip:
    clip = VideoFileClip(video_path).without_audio()
    clip = clip.loop(duration=duration) if clip.duration < duration else clip.subclip(0, duration)
    
    # Scale to frame height
    clip = clip.resize(height=TARGET_H)
    if clip.w < TARGET_W:
        clip = clip.resize(width=TARGET_W)
        
    # Overscale zoom to completely exclude corner watermarks
    clip = clip.resize(1.28)
    
    # Center crop width, push crop window down 80px to cut top logos
    x_center = (clip.w - TARGET_W) / 2
    y_center = min((clip.h - TARGET_H) / 2 + 80, clip.h - TARGET_H)
    
    return clip.crop(x1=x_center, y1=y_center, width=TARGET_W, height=TARGET_H)

def create_bordered_box(box_w, box_h, border_thick, duration, pos_y):
    """Creates a 4-sided neon cyan border enclosing the dark container."""
    cyan_bg = ColorClip(size=(box_w, box_h), color=(0, 240, 255)).set_duration(duration).set_position(("center", pos_y))
    inner_w = box_w - (border_thick * 2)
    inner_h = box_h - (border_thick * 2)
    dark_inner = ColorClip(size=(inner_w, inner_h), color=(11, 19, 43)).set_opacity(0.94).set_duration(duration).set_position(("center", pos_y + border_thick))
    return [cyan_bg, dark_inner]

def build_scene(scene_data):
    tts_path = f"temp_vo_{scene_data['id']}.mp3"
    asyncio.run(generate_speech(scene_data["text"], tts_path))
    
    audio = AudioFileClip(tts_path)
    scene_duration = audio.duration + 0.35
    elements = []

    if scene_data.get("is_outro", False):
        bg_video = process_visual_clip("scene4.mp4", scene_duration)
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
        base = process_visual_clip(scene_data["file"], scene_duration)
        dark_overlay = ColorClip(size=(TARGET_W, TARGET_H), color=(0, 0, 0)).set_opacity(0.22).set_duration(scene_duration)
        elements.extend([base, dark_overlay])

        # Scene 2 Screen Population Fix
        if scene_data["id"] == 2:
            screen_glow = ColorClip(size=(540, 360), color=(10, 35, 55)).set_opacity(0.55).set_duration(scene_duration).set_position((180, 480))
            screen_text = TextClip(
                "Draft: RE: Quick Question\n-------------------------\nHi Mark, sorry for the delay,\njust saw this now. I can jump on...",
                fontsize=20,
                color="#64D2FF",
                font="DejaVu-Sans-Mono",
                method="caption",
                size=(500, None)
            ).set_opacity(0.48).set_duration(scene_duration).set_position((200, 520))
            elements.extend([screen_glow, screen_text])

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

    composite = CompositeVideoClip(elements, size=(TARGET_W, TARGET_H))
    return composite.set_duration(scene_duration), audio

def main():
    ensure_background_music()

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
        print(f"[*] Assembling Scene {s['id']}...")
        v, a = build_scene(s)
        video_clips.append(v)
        audio_clips.append(a)

    print("[*] Concatenating timeline...")
    final_video = concatenate_videoclips(video_clips, method="compose")
    vocal_track = concatenate_audioclips(audio_clips)

    if os.path.exists(BGM_FILE):
        print(f"[*] Mixing {BGM_FILE} underneath voiceover...")
        try:
            bg_audio = AudioFileClip(BGM_FILE)
            bg_audio = audio_loop(bg_audio, duration=final_video.duration)
            bg_audio = volumex(bg_audio, 0.11)
            mixed_audio = CompositeAudioClip([vocal_track, bg_audio])
            final_video = final_video.set_audio(mixed_audio)
        except Exception as e:
            print(f"[!] Warning: Audio mix fallback triggered ({e}).")
            final_video = final_video.set_audio(vocal_track)
    else:
        final_video = final_video.set_audio(vocal_track)

    output = "guilt_driven_yes_master.mp4"
    final_video.write_videofile(output, fps=FPS, codec="libx264", audio_codec="aac", preset="ultrafast", threads=4)
    print(f"[✓] Render finished: {output}")

if __name__ == "__main__":
    main()
