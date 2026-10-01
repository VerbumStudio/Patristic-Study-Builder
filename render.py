import os
import sys
import json
import math
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import audit

# ==============================================================================
# CAMPAIGN: DAY 08 - EXECUTIVE BOUNDARY (SAVE & RETENTION OPTIMIZED)
# Resolution: 1080x1920 (9:16 Vertical) | Frame Rate: 30 FPS | Runtime: 20.0s
# Audio: Isolated Kinetic UI FX (Ping + Keystrokes) | Brand: @workflowsuperai
# ==============================================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 20.0
TOTAL_FRAMES = int(FPS * DURATION)  # 600 frames

# --- BRAND DESIGN SYSTEM ---
BG_COLOR = (10, 15, 29)          # Deep Slate/Navy #0A0F1D
CARD_BG = (18, 25, 46)           # Card Surface #12192E
CARD_HEADER_BG = (13, 19, 36)    # Dark Container Fill #0D1324
CARD_BORDER = (45, 60, 95)       # Stroke Outline #2D3C5F
CYAN_ACCENT = (0, 229, 255)      # Terminal Neon Cyan #00E5FF
CYAN_DIM = (0, 130, 150)         # Accent Dim Cyan
TEXT_WHITE = (248, 250, 252)     # High Contrast White #F8FAFC
TEXT_MUTED = (148, 163, 184)     # Secondary Muted Slate #94A3B8
ALERT_RED = (239, 68, 68)        # Stress Alert Red #EF4444
AMBER_WARN = (245, 158, 11)      # Tradeoff Amber #F59E0B
GREEN_SAFE = (16, 185, 129)      # Emerald Guardrail #10B981
PILL_BG = (0, 0, 0)              # Pure Black Pill BG

# --- TYPOGRAPHY HIERARCHY ---
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

font_pill = ImageFont.truetype(FONT_BOLD, 36)
font_title_lg = ImageFont.truetype(FONT_BOLD, 40)
font_h1 = ImageFont.truetype(FONT_BOLD, 34)
font_h2 = ImageFont.truetype(FONT_BOLD, 28)
font_body = ImageFont.truetype(FONT_REG, 25)
font_body_bold = ImageFont.truetype(FONT_BOLD, 25)
font_code = ImageFont.truetype(FONT_MONO, 22)
font_code_sm = ImageFont.truetype(FONT_MONO, 18)
font_table_hdr = ImageFont.truetype(FONT_BOLD, 22)
font_table_cell = ImageFont.truetype(FONT_REG, 20)
font_small = ImageFont.truetype(FONT_REG, 22)

# --- VIEWPORT GEOMETRY ---
CARD_LEFT = 48
CARD_RIGHT = 1032
CARD_WIDTH = CARD_RIGHT - CARD_LEFT  # 984 px

# Pre-flight Layout Verification
initial_config = {
    "pill_y": 380,
    "card_top": 460,
    "card_bottom": 1420,
    "lines": ['SAVE THIS TO PRESERVE YOUR SPRINT']
}
audit.run_audit(initial_config)

# ==============================================================================
# 1. AUDIO SYNTHESIS ENGINE (TACTILE UI FX ONLY - DESIGNED FOR BACKGROUND AUDIO)
# ==============================================================================
print("[1/3] Synthesizing isolated tactile UI sound effects...")
samplerate = 44100
total_samples = int(samplerate * DURATION)
audio = np.zeros(total_samples, dtype=np.float32)

# Crisp double-tone Slack/inbox alert ping at 0.0s (784Hz & 1046.5Hz)
for offset, freq in [(0.0, 784.0), (0.08, 1046.5)]:
    idx_start = int(offset * samplerate)
    dur = 0.65
    t_chime = np.linspace(0, dur, int(dur * samplerate), endpoint=False)
    wave_c = 0.45 * np.sin(2 * np.pi * freq * t_chime) * np.exp(-t_chime * 6.5)
    idx_end = min(total_samples, idx_start + len(wave_c))
    audio[idx_start:idx_end] += wave_c[:idx_end - idx_start]

# Rapid mechanical keyboard keystrokes (1.2s - 2.5s)
for click_time in [1.2, 1.32, 1.45, 1.6, 1.75, 1.9, 2.05, 2.2, 2.35]:
    idx_c = int(click_time * samplerate)
    t_click = np.linspace(0, 0.035, int(0.035 * samplerate), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t_click)) * np.exp(-t_click * 130.0) * 0.28
    idx_end = min(total_samples, idx_c + len(noise))
    audio[idx_c:idx_end] += noise[:idx_end - idx_c]

# Normalize tactile audio peaks cleanly
max_val = np.max(np.abs(audio))
if max_val > 0:
    audio_int16 = ((audio / max_val) * 0.95 * 32767).astype(np.int16)
else:
    audio_int16 = (audio * 32767).astype(np.int16)

audio_filename = "day08_boundary_audio.wav"
with wave.open(audio_filename, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio_int16.tobytes())

# ==============================================================================
# 2. RENDERING PRIMITIVES
# ==============================================================================
def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def draw_pill(draw, text, center_x, center_y, bg=PILL_BG, border_color=CYAN_ACCENT, text_color=TEXT_WHITE):
    bbox = font_pill.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    px, py = 32, 14
    x0, y0 = center_x - tw // 2 - px, center_y - th // 2 - py
    x1, y1 = center_x + tw // 2 + px, center_y + th // 2 + py
    draw_rounded_rect(draw, (x0, y0, x1, y1), radius=26, fill=bg, outline=border_color, width=3)
    draw.text((center_x - tw // 2, y0 + py - bbox[1]), text, font=font_pill, fill=text_color)

def draw_header(draw):
    draw.text((CARD_LEFT + 20, 68), "9:41", font=font_h2, fill=TEXT_MUTED)
    draw.text((CARD_RIGHT - 160, 72), "5G  100%", font=font_small, fill=TEXT_MUTED)
    draw.rounded_rectangle((CARD_LEFT, 130, CARD_RIGHT, 215), radius=16, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=2)
    draw.ellipse((CARD_LEFT + 30, 155, CARD_LEFT + 65, 190), fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 85, 152), "WORKFLOWSUPERAI // STRATEGIC COMMS", font=font_h2, fill=TEXT_WHITE)

def draw_watermark(draw):
    draw.text((CARD_LEFT + 20, 1840), "@workflowsuperai", font=font_h2, fill=CYAN_DIM)
    draw.text((CARD_RIGHT - 280, 1845), "AI EXECUTIVE PIPELINE", font=font_small, fill=TEXT_MUTED)

def draw_typewriter_lines(draw, lines, x, start_y, line_height, progress, frame, font, color,
                          cursor_color=CYAN_ACCENT, stream_window=0.55):
    total_chars = sum(len(line) for line in lines)
    if total_chars == 0:
        return
    chars_to_render = int(min(1.0, progress / stream_window) * total_chars)
    current_y = start_y
    blinking = (frame // 8) % 2 == 0
    remaining = chars_to_render
    for i, line in enumerate(lines):
        if remaining >= len(line):
            draw.text((x, current_y), line, font=font, fill=color)
            remaining -= len(line)
            current_y += line_height
            if i == len(lines) - 1 and progress < 0.95 and blinking:
                bbox = font.getbbox(line)
                draw.text((x + (bbox[2] - bbox[0]) + 6, current_y - line_height), "█", font=font, fill=cursor_color)
        elif remaining > 0:
            sub = line[:remaining]
            draw.text((x, current_y), sub, font=font, fill=color)
            if blinking:
                bbox = font.getbbox(sub)
                draw.text((x + (bbox[2] - bbox[0]) + 6, current_y), "█", font=font, fill=cursor_color)
            break
        else:
            break

# ==============================================================================
# 3. SCENE IMPLEMENTATIONS
# ==============================================================================

def render_scene_1(draw, progress, frame):
    """Scene 1 (0.0s - 1.2s): Immediate Acute Pain Hook"""
    offset_y = int(progress * 40)
    draw_pill(draw, "4:45 PM 'URGENT' SLACK?", 540, 390, border_color=ALERT_RED, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 760
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=ALERT_RED, width=3)
    
    draw.rounded_rectangle((CARD_LEFT + 30, card_y + 35, CARD_LEFT + 340, card_y + 85), radius=12, fill=(45, 15, 20))
    draw.text((CARD_LEFT + 45, card_y + 46), "UNPLANNED SCOPE INTRUSION", font=font_code_sm, fill=ALERT_RED)
    
    incoming_slacks = [
        "VP Product: 'Need updated enterprise decks tonight.'",
        "Lead Client: 'Can we squeeze in SSO before morning?'",
        "Dave: 'Launch blocks unless this is verified ASAP.'",
        "Sarah: 'Our sprint is completely booked though...'",
        "Executive: 'Just work late and push it through.'"
    ]
    sy = card_y + 115 - offset_y
    for s in incoming_slacks:
        if card_y + 100 <= sy <= card_y + card_h - 100:
            draw_rounded_rect(draw, (CARD_LEFT + 30, sy, CARD_RIGHT - 30, sy + 75), radius=12, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=1)
            draw.text((CARD_LEFT + 50, sy + 22), s, font=font_code_sm, fill=TEXT_MUTED)
        sy += 90

    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + card_h - 85, CARD_RIGHT - 30, card_y + card_h - 25), radius=12, fill=(65, 20, 25))
    draw.text((CARD_LEFT + 220, card_y + card_h - 65), "BURNOUT FRICTION: REACTIVE SUBMISSION", font=font_body_bold, fill=(255, 140, 140))


def render_scene_2(draw, progress, frame):
    """Scene 2 (1.2s - 4.5s): FULLY RENDERED SYSTEM PROMPT (EXPLICIT BOOKMARK BAIT)"""
    draw_pill(draw, "BOOKMARK & COPY THIS PROMPT", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    
    draw.rounded_rectangle((CARD_LEFT, card_y, CARD_RIGHT, card_y + 75), radius=28, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 35, card_y + 28, CARD_LEFT + 55, card_y + 48), fill=ALERT_RED)
    draw.ellipse((CARD_LEFT + 70, card_y + 28, CARD_LEFT + 90, card_y + 48), fill=AMBER_WARN)
    draw.ellipse((CARD_LEFT + 105, card_y + 28, CARD_LEFT + 125, card_y + 48), fill=GREEN_SAFE)
    draw.text((CARD_LEFT + 155, card_y + 22), "SYSTEM PROMPT : DE_ESCALATION_ENGINE.MD", font=font_code, fill=CYAN_ACCENT)
    
    prompt_lines = [
        "ACT AS: Executive Negotiation Strategist",
        "GOAL: De-escalate reactive scope creep without friction.",
        "",
        "INPUT: Demanding / urgent message sent after hours.",
        "",
        "OPERATIONAL DIRECTIVE:",
        "1. Validate business intent without accepting guilt.",
        "2. Surface exact opportunity cost to current sprint.",
        "3. Output a 3-Option Strategic Tradeoff Grid:",
        "   - OPTION A: Deliver tonight (Drop sprint item).",
        "   - OPTION B: Defer to 9 AM (Sprint protected).",
        "   - OPTION C: Route to emergency on-call team.",
        "",
        "CONSTRAINTS: Professional, neutral, zero apologies."
    ]
    draw_typewriter_lines(draw, prompt_lines, CARD_LEFT + 40, card_y + 100, 48, progress, frame, font_code, TEXT_WHITE, stream_window=0.55)


def render_scene_3(draw, progress, frame):
    """Scene 3 (4.5s - 8.5s): Raw Hostile Request + Balanced Friction Dashboard"""
    draw_pill(draw, "STEP 1: INGEST HOSTILE REQUEST", 540, 390, border_color=ALERT_RED, text_color=ALERT_RED)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw.text((CARD_LEFT + 40, card_y + 35), "INCOMING PRESSURE MESSAGE (4:48 PM)", font=font_h2, fill=ALERT_RED)
    draw_rounded_rect(draw, (CARD_LEFT + 35, card_y + 80, CARD_RIGHT - 35, card_y + 320), radius=16, fill=(35, 15, 20), outline=ALERT_RED, width=2)
    incoming_msg = [
        '"Hey, we need the enterprise security analysis',
        'completely audited before tomorrow morning.',
        'Client executive is demanding it. Drop whatever',
        'you are doing and send it over tonight."'
    ]
    sy = card_y + 115
    for line in incoming_msg:
        draw.text((CARD_LEFT + 60, sy), line, font=font_body, fill=TEXT_WHITE)
        sy += 48

    draw.text((CARD_LEFT + 40, card_y + 350), "AUTOMATED PSYCHOLOGICAL TRIAGE", font=font_h2, fill=CYAN_ACCENT)
    draw_rounded_rect(draw, (CARD_LEFT + 35, card_y + 395, CARD_RIGHT - 35, card_y + 685), radius=16, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=1)
    evals = [
        ("✔ Strategic Leverage:", "High emotional urgency detected"),
        ("✔ Cost of Compliance:", "Derails Q4 sprint deliverables"),
        ("✔ Negotiation Goal:", "Transfer decision back to sender")
    ]
    dy = card_y + 425
    for title, desc in evals:
        draw.text((CARD_LEFT + 60, dy), title, font=font_body_bold, fill=TEXT_WHITE)
        draw.text((CARD_LEFT + 60, dy + 38), desc, font=font_body, fill=TEXT_MUTED)
        dy += 85

    badge_y = card_y + 720
    draw_rounded_rect(draw, (CARD_LEFT + 35, badge_y, CARD_RIGHT - 35, badge_y + 155), radius=16, fill=(20, 28, 48), outline=CYAN_ACCENT, width=2)
    draw.text((CARD_LEFT + 60, badge_y + 25), "COGNITIVE IMPACT & BURNOUT INDEX", font=font_h2, fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 60, badge_y + 70), "• Reactive Anxiety: HIGH", font=font_body_bold, fill=ALERT_RED)
    draw.text((CARD_LEFT + 450, badge_y + 70), "• Sprint Delay: +48 HRS", font=font_body_bold, fill=AMBER_WARN)
    draw.text((CARD_LEFT + 60, badge_y + 112), "• Strategy: Enforce explicit tradeoff before accepting", font=font_small, fill=TEXT_WHITE)


def render_scene_4(draw, progress, frame):
    """Scene 4 (8.5s - 13.0s): Strategic Tradeoff Markdown Grid Output"""
    draw_pill(draw, "STEP 2: 3-TIER TRADEOFF MATRIX", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    
    draw.text((CARD_LEFT + 40, card_y + 35), "EXECUTIVE BOUNDARY SCRIPT (OPTIONS)", font=font_h2, fill=CYAN_ACCENT)
    
    tbl_x = CARD_LEFT + 30
    tbl_y = card_y + 90
    tbl_w = CARD_WIDTH - 60
    tbl_h = 620
    
    draw_rounded_rect(draw, (tbl_x, tbl_y, tbl_x + tbl_w, tbl_y + tbl_h), radius=14, fill=CARD_HEADER_BG, outline=CYAN_ACCENT, width=2)
    
    c0 = tbl_x
    c1 = tbl_x + 220
    c2 = tbl_x + 580
    c3 = tbl_x + tbl_w
    
    draw.rectangle((c0, tbl_y, c3, tbl_y + 75), fill=(24, 45, 78))
    draw.line((c0, tbl_y + 75, c3, tbl_y + 75), fill=CYAN_ACCENT, width=2)
    draw.text((c0 + 20, tbl_y + 24), "OPTION", font=font_table_hdr, fill=CYAN_ACCENT)
    draw.text((c1 + 20, tbl_y + 24), "PROPOSED ACTION", font=font_table_hdr, fill=CYAN_ACCENT)
    draw.text((c2 + 20, tbl_y + 24), "STRATEGIC TRADEOFF", font=font_table_hdr, fill=CYAN_ACCENT)
    
    for div_x in [c1, c2]:
        draw.line((div_x, tbl_y, div_x, tbl_y + tbl_h), fill=CARD_BORDER, width=1)
        
    rows = [
        ("A: Urgent Exec", "Deliver security file by 9 PM", "Delays Q4 AWS Migration by 2 Days", ALERT_RED),
        ("B: Protected", "Deliver tomorrow at 9:00 AM", "Zero impact to active production sprint", GREEN_SAFE),
        ("C: Delegate", "Route to Level-2 On-Call", "Requires standard overtime auth", AMBER_WARN)
    ]
    
    row_y = tbl_y + 75
    row_h = 180
    for opt, act, trade, col in rows:
        draw.line((c0, row_y + row_h, c3, row_y + row_h), fill=CARD_BORDER, width=1)
        draw.text((c0 + 20, row_y + 60), opt, font=font_table_hdr, fill=col)
        draw.text((c1 + 20, row_y + 60), act, font=font_table_cell, fill=TEXT_WHITE)
        draw.text((c2 + 20, row_y + 60), trade, font=font_table_cell, fill=TEXT_MUTED)
        row_y += row_h

    badge_y = card_y + 750
    draw_rounded_rect(draw, (CARD_LEFT + 35, badge_y, CARD_RIGHT - 35, badge_y + 110), radius=16, fill=(15, 35, 55), outline=GREEN_SAFE, width=2)
    draw.text((CARD_LEFT + 70, badge_y + 25), "LEVERAGE: SENDER CHOOSES THE SACRIFICE", font=font_body_bold, fill=GREEN_SAFE)
    draw.text((CARD_LEFT + 70, badge_y + 65), "Zero emotional confrontation • Professional boundaries preserved", font=font_small, fill=TEXT_WHITE)


def render_scene_5(draw, progress, frame):
    """Scene 5 (13.0s - 16.5s): Transformation Contrast"""
    draw_pill(draw, "EMOTIONAL SPIRAL -> CALM CONTROL", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 45, CARD_RIGHT - 30, card_y + 355), radius=20, fill=(35, 15, 20), outline=ALERT_RED, width=2)
    draw.text((CARD_LEFT + 60, card_y + 75), "DEFAULT: REACTIVE ANXIETY (40 MINS)", font=font_h2, fill=ALERT_RED)
    draw.text((CARD_LEFT + 60, card_y + 140), "• Typing and deleting passive-aggressive replies", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 200), "• Ruining your personal evening under resentment", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 260), "• Setting a precedent that your boundaries do not exist", font=font_body, fill=TEXT_WHITE)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 395, CARD_RIGHT - 30, card_y + 705), radius=20, fill=(15, 35, 55), outline=GREEN_SAFE, width=2)
    draw.text((CARD_LEFT + 60, card_y + 425), "SYSTEM: STRATEGIC DE-ESCALATION (8 SEC)", font=font_h2, fill=GREEN_SAFE)
    draw.text((CARD_LEFT + 60, card_y + 490), "✔ Puts decision directly back on requester with clear costs", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 550), "✔ Protects team sprint focus and avoids after-hours churn", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 610), "✔ Projects calm, executive authority and zero panic", font=font_body, fill=TEXT_WHITE)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 745, CARD_RIGHT - 30, card_y + 865), radius=18, fill=CARD_HEADER_BG, outline=CYAN_ACCENT, width=2)
    draw.text((CARD_LEFT + 135, card_y + 790), "COMMUNICATE WITH EXECUTIVE AUTHORITY", font=font_h2, fill=CYAN_ACCENT)


def render_scene_6(draw, progress, frame):
    """Scene 6 (16.5s - 20.0s): Mobile Safe-Zone Optimized End-Card with Pure Save/Bookmark Action"""
    pill_y = 380
    card_y = 460
    card_h = 950
    
    draw_pill(draw, "SAVE THIS TO PRESERVE YOUR SPRINT", 540, pill_y, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=32, fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    
    draw.text((CARD_LEFT + 340, card_y + 40), "@workflowsuperai", font=font_h2, fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 70, card_y + 105), "GET THE DE-ESCALATION PROMPT", font=font_title_lg, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 220, card_y + 175), "+ FREE 7-PROMPT AI LIBRARY", font=font_h2, fill=TEXT_MUTED)
    
    term_top = card_y + 240
    term_h = 175
    draw_rounded_rect(draw, (CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + term_h), radius=20, fill=(10, 15, 29), outline=CYAN_ACCENT, width=2)
    draw.rounded_rectangle((CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + 50), radius=20, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 65, term_top + 18, CARD_LEFT + 80, term_top + 33), fill=ALERT_RED)
    draw.ellipse((CARD_LEFT + 95, term_top + 18, CARD_LEFT + 110, term_top + 33), fill=AMBER_WARN)
    draw.ellipse((CARD_LEFT + 125, term_top + 18, CARD_LEFT + 140, term_top + 33), fill=GREEN_SAFE)
    draw.text((CARD_LEFT + 165, term_top + 14), "TERMINAL // WORKFLOW SAVE STATE", font=font_code_sm, fill=TEXT_MUTED)
    
    draw.text((CARD_LEFT + 80, term_top + 85), "> bookmark:", font=font_h1, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 320, term_top + 85), 'SCRIPT SAVED TO LIST', font=font_h1, fill=CYAN_ACCENT)
    if (frame // 8) % 2 == 0:
        draw.rectangle((CARD_LEFT + 805, term_top + 90, CARD_LEFT + 830, term_top + 130), fill=CYAN_ACCENT)

    features = [
        "✔ Bookmark this video to preserve the negotiation matrix",
        "✔ Copy prompt directly into Claude 3.5 or ChatGPT",
        "✔ Free raw markdown template available in bio"
    ]
    fy = card_y + 450
    for feat in features:
        draw.text((CARD_LEFT + 80, fy), feat, font=font_body, fill=TEXT_WHITE)
        fy += 56
        
    link_box_y = card_y + 650
    link_box_h = 240
    draw_rounded_rect(draw, (CARD_LEFT + 40, link_box_y, CARD_RIGHT - 40, link_box_y + link_box_h), radius=22, fill=(15, 23, 42), outline=CARD_BORDER, width=2)
    draw.text((CARD_LEFT + 220, link_box_y + 35), "OR ACCESS DIRECTLY VIA BEACONS:", font=font_code, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 175, link_box_y + 90), "🔗 beacons.ai/workflowsuperai", font=font_h1, fill=CYAN_ACCENT)
    
    draw_rounded_rect(draw, (CARD_LEFT + 160, link_box_y + 165, CARD_RIGHT - 160, link_box_y + 220), radius=14, fill=(28, 54, 110))
    draw.text((CARD_LEFT + 200, link_box_y + 178), "FREE 7-PROMPT AI LIBRARY IN BIO", font=font_h2, fill=TEXT_WHITE)

# ==============================================================================
# 4. COMPILATION PIPELINE
# ==============================================================================
output_mp4 = "day08_executive_boundary_20s.mp4"
print(f"[2/3] Streaming {TOTAL_FRAMES} frames to FFmpeg compiler...")

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",
    "-i", audio_filename,
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "fast",
    "-crf", "19",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    output_mp4
]

proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

for frame_idx in range(TOTAL_FRAMES):
    t_sec = frame_idx / FPS
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw_header(draw)
    draw_watermark(draw)
    
    if t_sec < 1.2:
        render_scene_1(draw, t_sec / 1.2, frame_idx)
    elif t_sec < 4.5:
        render_scene_2(draw, (t_sec - 1.2) / 3.3, frame_idx)
    elif t_sec < 8.5:
        render_scene_3(draw, (t_sec - 4.5) / 4.0, frame_idx)
    elif t_sec < 13.0:
        render_scene_4(draw, (t_sec - 8.5) / 4.5, frame_idx)
    elif t_sec < 16.5:
        render_scene_5(draw, (t_sec - 13.0) / 3.5, frame_idx)
    else:
        render_scene_6(draw, (t_sec - 16.5) / 3.5, frame_idx)
        
    proc.stdin.write(img.tobytes())

proc.stdin.close()
proc.wait()
print(f"[3/3] Video build successfully exported: {output_mp4}")
