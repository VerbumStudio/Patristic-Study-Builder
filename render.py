import subprocess
import sys

# 1. Force-install moviepy and dependencies directly in Python runtime
print("[*] Ensuring dependencies are installed...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", 
    "moviepy<2.0.0", "imageio-ffmpeg"
])

# 2. Now import moviepy safely
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip

print("[*] Dependencies loaded successfully. Starting video build...")

WIDTH = 1080
HEIGHT = 1920
DURATION = 15

# Background
background = ColorClip(size=(WIDTH, HEIGHT), color=(15, 17, 23), duration=DURATION)

# Hook
hook_text = (
    TextClip(
        "Stop sifting through 40 morning emails at 8 AM.",
        fontsize=48,
        color="white",
        font="DejaVu-Sans-Bold",
        size=(WIDTH - 160, None),
        method="caption"
    )
    .set_position(("center", 280))
    .set_duration(4)
)

# Terminal block
terminal_body = """SYSTEM: MORNING_TRIAGE_ENGINE.MD

INPUT: 42 Unread Emails / Standup Prep
STATUS: DEPLOYING 1-SHOT TRIAGE...

[P1] IMMEDIATE BLOCKERS (< 9:00 AM)
• Client latency escalation -> Route to On-Call
• Review staging deploy build failure

[P2] DELEGATE / POST-STANDUP
• Vendor invoice confirmation -> Ops lead
• Weekly metrics review deck sync

[P3] ARCHIVED / NON-ACTIONABLE
• 37 low-priority notifications cleaned."""

code_block = (
    TextClip(
        terminal_body,
        fontsize=34,
        color="#38BDF8",
        font="Courier",
        size=(WIDTH - 180, None),
        method="caption",
        align="West"
    )
    .set_position(("center", "center"))
    .set_start(3)
    .set_duration(DURATION - 3)
)

# CTA
cta_text = (
    TextClip(
        "Save this video for your morning standup ⚡",
        fontsize=40,
        color="#FACC15",
        font="DejaVu-Sans-Bold",
        size=(WIDTH - 160, None),
        method="caption"
    )
    .set_position(("center", HEIGHT - 340))
    .set_start(10)
    .set_duration(5)
)

final_reel = CompositeVideoClip(
    [background, hook_text, code_block, cta_text],
    size=(WIDTH, HEIGHT)
)

final_reel.write_videofile(
    "output_reel.mp4",
    fps=30,
    codec="libx264",
    audio_codec="aac"
)

print("[✓] Video rendered successfully as output_reel.mp4")
