import os
from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    ColorClip
)

# 1. Canvas Dimensions (9:16 Vertical Reel)
WIDTH = 1080
HEIGHT = 1920
DURATION = 15

# 2. Base Background (Dark aesthetic or looped b-roll clip)
# If using a raw b-roll mp4: background = VideoFileClip("assets/typing_broll.mp4").subclip(0, DURATION)
background = ColorClip(size=(WIDTH, HEIGHT), color=(15, 17, 23), duration=DURATION)

# 3. Hook Text Overlay (Top Pill, Seconds 0 to 4)
hook_text = (
    TextClip(
        "Stop sifting through 40 morning emails at 8 AM.",
        fontsize=48,
        color="white",
        font="Arial-Bold",
        size=(WIDTH - 160, None),
        method="caption"
    )
    .set_position(("center", 280))
    .set_duration(4)
)

# 4. Terminal Output Simulation (Seconds 3 to 15)
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
        color="#38BDF8",  # Cyan terminal glow
        font="Courier-Bold",
        size=(WIDTH - 180, None),
        method="caption",
        align="West"
    )
    .set_position(("center", "center"))
    .set_start(3)
    .set_duration(DURATION - 3)
)

# 5. Call To Action Footer (Seconds 10 to 15)
cta_text = (
    TextClip(
        "Save this video for your morning standup ⚡",
        fontsize=40,
        color="#FACC15",
        font="Arial-Bold",
        size=(WIDTH - 160, None),
        method="caption"
    )
    .set_position(("center", HEIGHT - 340))
    .set_start(10)
    .set_duration(5)
)

# 6. Composite & Render
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
