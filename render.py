import json
import os
import subprocess
import sys

print("[*] Installing rendering dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts", "moviepy==1.0.3"])

import asyncio
import edge_tts
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

# 1. Load Configuration
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

THEME = config["theme"]
TARGET_W, TARGET_H = config["resolution"]
FPS = config["fps"]
VOICE = "en-US-ChristopherNeural"  # Authoritative executive cadence

# 2. Asynchronous TTS Generation
async def generate_speech(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="+0%", pitch="-2Hz")
    await communicate.save(output_path)

def build_audio(scenes):
    print("[*] Synthesizing executive voiceover audio...")
    audio_clips = []
    os.makedirs("temp_audio", exist_ok=True)
    
    for scene in scenes:
        tts_path = f"temp_audio/vo_{scene['id']}.mp3"
        asyncio.run(generate_speech(scene["voiceover_text"], tts_path))
        
        voice_clip = AudioFileClip(tts_path)
        # Pad audio to match scene duration if speech is shorter
        duration = max(scene["duration"], voice_clip.duration + 0.3)
        scene["actual_duration"] = duration
        
        # Build silence padding clip if needed
        silence_duration = duration - voice_clip.duration
        if silence_duration > 0:
            silence_path = f"temp_audio/silence_{scene['id']}.mp3"
            subprocess.check_call([
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"anullsrc=r=44100:cl=stereo:d={silence_duration}",
                silence_path
            ])
            silence_clip = AudioFileClip(silence_path)
            composite_scene_audio = concatenate_audioclips([voice_clip, silence_clip])
        else:
            composite_scene_audio = voice_clip
            
        audio_clips.append(composite_scene_audio)
        
    return concatenate_audioclips(audio_clips)

# 3. Visual Scene Assembly
def build_video_clip(scene):
    duration = scene.get("actual_duration", scene["duration"])
    
    if scene["source_type"] == "local_file":
        clip = VideoFileClip(scene["file_path"]).without_audio()
        if clip.duration < duration:
            clip = clip.loop(duration=duration)
        else:
            clip = clip.subclip(0, duration)
            
        # Center-crop & resize to 1080x1920 (9:16)
        clip = clip.resize(height=TARGET_H)
        if clip.w < TARGET_W:
            clip = clip.resize(width=TARGET_W)
        x_center = (clip.w - TARGET_W) / 2
        y_center = (clip.h - TARGET_H) / 2
        clip = clip.crop(x1=x_center, y1=y_center, width=TARGET_W, height=TARGET_H)
        
    else:  # Generated outro card
        clip = ColorClip(size=(TARGET_W, TARGET_H), color=(11, 19, 43)).set_duration(duration)

    # Dark atmospheric contrast overlay
    dark_overlay = ColorClip(size=(TARGET_W, TARGET_H), color=(0, 0, 0)).set_opacity(0.42).set_duration(duration)

    # Accent Card Box
    box_w, box_h = 920, 240
    box_bg = ColorClip(size=(box_w, box_h), color=(11, 19, 43)).set_opacity(0.85).set_duration(duration)
    box_bg = box_bg.set_position(("center", 1320))

    # Cyan Accent Border Bar
    cyan_bar = ColorClip(size=(920, 8), color=(0, 240, 255)).set_duration(duration)
    cyan_bar = cyan_bar.set_position(("center", 1320))

    # Text Overlay
    txt_main = TextClip(
        scene["overlay_title"],
        fontsize=44,
        color="white",
        font="DejaVu-Sans-Bold",
        method="caption",
        size=(860, None)
    ).set_duration(duration).set_position(("center", 1360))

    elements = [clip, dark_overlay, box_bg, cyan_bar, txt_main]

    if "overlay_subtitle" in scene:
        txt_sub = TextClip(
            scene["overlay_subtitle"],
            fontsize=32,
            color="#00F0FF",
            font="DejaVu-Sans-Bold"
        ).set_duration(duration).set_position(("center", 1460))
        elements.append(txt_sub)

    return CompositeVideoClip(elements, size=(TARGET_W, TARGET_H)).set_duration(duration)

# 4. Pipeline Execution
def main():
    scenes = config["scenes"]
    
    # Generate Voiceover Audio Track
    full_audio = build_audio(scenes)
    
    print("[*] Processing scenes and geometric overlays...")
    video_clips = [build_video_clip(s) for s in scenes]
    master_video = concatenate_videoclips(video_clips, method="compose")
    master_video = master_video.set_audio(full_audio)
    
    output_filename = "guilt_driven_yes_master.mp4"
    print(f"[*] Rendering final reel to {output_filename}...")
    master_video.write_videofile(
        output_filename,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )
    print(f"[✓] Render complete: {output_filename}")

if __name__ == "__main__":
    main()
