import subprocess
import sys
import os
import urllib.request

# 1. Verify dependencies
print("[*] Verifying runtime dependencies...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", 
    "moviepy<2.0.0", "imageio-ffmpeg", "pillow", "numpy"
])

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip

WIDTH = 1080
HEIGHT = 1920
DURATION = 15

# 2. Download crisp TrueType fonts directly so there is zero reliance on system fonts
FONT_SANS = "Roboto-Bold.ttf"
FONT_MONO = "RobotoMono-Medium.ttf"

if not os.path.exists(FONT_SANS):
    urllib.request.urlretrieve(
        "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf",
        FONT_SANS
    )

if not os.path.exists(FONT_MONO):
    urllib.request.urlretrieve(
        "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Medium.ttf",
        FONT_MONO
    )

font_hook = ImageFont.truetype(FONT_SANS, 52)
font_badge = ImageFont.truetype(FONT_MONO, 28)
font_terminal_header = ImageFont.truetype(FONT_MONO, 32)
font_body = ImageFont.truetype(FONT_MONO, 34)
font_cta = ImageFont.truetype(FONT_SANS, 46)

def render_frame(phase=1):
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 14, 23)) # Deep cyber navy
    draw = ImageDraw.Draw(img)

    # Ambient Top Badge / Category Pill
    draw.rounded_rectangle([(80, 140), (430, 205)], radius=12, fill=(19, 31, 53), outline=(56, 189, 248), width=2)
    draw.text((105, 156), "AI WORKFLOW // TRIAGE", fill=(56, 189, 248), font=font_badge)

    # 1. Main Hook Banner
    draw.rounded_rectangle([(80, 240), (WIDTH - 80, 500)], radius=24, fill=(17, 24, 39), outline=(37, 99, 235), width=3)
    hook_lines = [
        "Stop sifting through 40 unread",
        "emails at 8:00 AM.",
        "Deploy a 1-Shot Triage Engine ⚡"
    ]
    y_hook = 280
    for line in hook_lines:
        color = (250, 204, 21) if "1-Shot" in line else (255, 255, 255)
        draw.text((120, y_hook), line, fill=color, font=font_hook)
        y_hook += 68

    # 2. Terminal Window
    if phase >= 2:
        # Window Header Tab
        draw.rounded_rectangle([(80, 560), (WIDTH - 80, 1340)], radius=24, fill=(13, 17, 28), outline=(56, 189, 248), width=2)
        draw.rectangle([(80, 560), (WIDTH - 80, 640)], fill=(22, 27, 46))
        
        # MacOS / Linux Dot Accents
        draw.ellipse([(120, 590), (140, 610)], fill=(239, 68, 68))
        draw.ellipse([(155, 590), (175, 610)], fill=(234, 179, 8))
        draw.ellipse([(190, 590), (210, 610)], fill=(34, 197, 94))
        draw.text((230, 588), "morning_triage_engine.md — 42 msgs", fill=(148, 163, 184), font=font_terminal_header)

        # Terminal Lines
        body_content = [
            ("STATUS: PARSING 42 INBOUND MESSAGES...", (148, 163, 184)),
            ("----------------------------------------", (71, 85, 105)),
            ("[P1] CRITICAL ESCALATIONS (< 9:00 AM)", (248, 113, 113)),
            ("  • API Latency spike -> Routed to SRE on-call", (255, 255, 255)),
            ("  • Staging CI/CD build break -> Assigned PR owner", (255, 255, 255)),
            ("", (0, 0, 0)),
            ("[P2] DELEGATE & SCHEDULE (POST-STANDUP)", (56, 189, 248)),
            ("  • Enterprise pilot SLA sync -> Operations lead", (226, 232, 240)),
            ("  • Vendor renewal invoice -> Auto-flagged to accounting", (226, 232, 240)),
            ("", (0, 0, 0)),
            ("[P3] CLEANED & ARCHIVED", (74, 222, 128)),
            ("  • 38 newsletters, notifications & noise swept.", (148, 163, 184)),
        ]

        y_body = 675
        for line, text_color in body_content:
            if line:
                draw.text((120, y_body), line, fill=text_color, font=font_body)
            y_body += 48

    # 3. Call To Action Footer Banner
    if phase >= 3:
        draw.rounded_rectangle([(80, 1420), (WIDTH - 80, 1620)], radius=24, fill=(19, 31, 53), outline=(250, 204, 21), width=3)
        draw.text((120, 1465), "STEAL THIS AUTOMATION:", fill=(148, 163, 184), font=font_badge)
        draw.text((120, 1515), "Comment 'TRIAGE' for the prompt 📥", fill=(250, 204, 21), font=font_cta)

    return np.array(img)

print("[*] Rendering timeline clips with typography...")

frame1 = render_frame(phase=1)
clip1 = ImageClip(frame1).set_duration(2.5)

frame2 = render_frame(phase=2)
clip2 = ImageClip(frame2).set_start(2.5).set_duration(6.5)

frame3 = render_frame(phase=3)
clip3 = ImageClip(frame3).set_start(9.0).set_duration(6.0)

final_reel = CompositeVideoClip([clip1, clip2, clip3], size=(WIDTH, HEIGHT))

final_reel.write_videofile(
    "output_reel.mp4",
    fps=30,
    codec="libx264",
    audio_codec="aac"
)

print("[✓] Clean video rendered to output_reel.mp4")
