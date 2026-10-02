import subprocess
import sys

# 1. Ensure moviepy, pillow, and imageio-ffmpeg are installed
print("[*] Verifying Python libraries...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", 
    "moviepy<2.0.0", "imageio-ffmpeg", "pillow"
])

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip

print("[*] Dependencies loaded. Rendering frames with Pillow...")

WIDTH = 1080
HEIGHT = 1920
DURATION = 15

# Helper function to generate clean graphic cards without ImageMagick
def make_text_overlay(width, height, hook, body, cta, show_body=True, show_cta=False):
    img = Image.new("RGBA", (width, height), (15, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    # Use default bitmap font to prevent missing system font errors
    font = ImageFont.load_default()

    # Draw Hook Header
    draw.rectangle([(60, 180), (width - 60, 360)], fill=(30, 41, 59, 255), outline=(56, 189, 248, 255), width=2)
    draw.text((90, 240), hook, fill=(255, 255, 255, 255), font=font)

    # Draw Terminal Body Box
    if show_body:
        draw.rectangle([(60, 420), (width - 60, 1300)], fill=(10, 15, 30, 255), outline=(71, 85, 105, 255), width=2)
        draw.text((90, 460), body, fill=(56, 189, 248, 255), font=font)

    # Draw CTA Banner
    if show_cta:
        draw.rectangle([(60, 1360), (width - 60, 1500)], fill=(30, 41, 59, 255), outline=(250, 204, 21, 255), width=2)
        draw.text((90, 1410), cta, fill=(250, 204, 21, 255), font=font)

    return np.array(img)

HOOK_MSG = "Stop sifting through 40 morning emails at 8 AM.\nUse this 1-shot Triage Engine:"

BODY_MSG = """SYSTEM: MORNING_TRIAGE_ENGINE.MD

INPUT: 42 Unread Emails / Standup Prep
STATUS: DEPLOYING 1-SHOT TRIAGE...

[P1] IMMEDIATE BLOCKERS (< 9:00 AM)
* Client latency escalation -> Route to On-Call
* Review staging deploy build failure

[P2] DELEGATE / POST-STANDUP
* Vendor invoice confirmation -> Ops lead
* Weekly metrics review deck sync

[P3] ARCHIVED / NON-ACTIONABLE
* 37 low-priority notifications cleaned."""

CTA_MSG = "Save this video for your morning standup ⚡"

# Build Video Sequences
frame_phase1 = make_text_overlay(WIDTH, HEIGHT, HOOK_MSG, "", "", show_body=False, show_cta=False)
clip1 = ImageClip(frame_phase1).set_duration(3)

frame_phase2 = make_text_overlay(WIDTH, HEIGHT, HOOK_MSG, BODY_MSG, "", show_body=True, show_cta=False)
clip2 = ImageClip(frame_phase2).set_start(3).set_duration(7)

frame_phase3 = make_text_overlay(WIDTH, HEIGHT, HOOK_MSG, BODY_MSG, CTA_MSG, show_body=True, show_cta=True)
clip3 = ImageClip(frame_phase3).set_start(10).set_duration(5)

final_reel = CompositeVideoClip([clip1, clip2, clip3], size=(WIDTH, HEIGHT))

final_reel.write_videofile(
    "output_reel.mp4",
    fps=24,
    codec="libx264",
    audio_codec="aac"
)

print("[✓] SUCCESS: output_reel.mp4 generated completely without ImageMagick.")
