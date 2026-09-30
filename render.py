import os
import sys
import json
import math
import subprocess
import wave
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import audit

# ==============================================================================
# CAMPAIGN: PROMPT 1 - MEETING SUMMARY & ACTION ITEM MATRIX
# Resolution: 1080x1920 (9:16 Vertical) | Frame Rate: 30 FPS | Runtime: 21.0s
# Trigger: "MEETING" | Brand: @workflowsuperai
# ==============================================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 21.0
TOTAL_FRAMES = int(FPS * DURATION)  # 630 frames

# --- BRAND COLOR SYSTEM ---
BG_COLOR = (10, 15, 29)          # Deep Slate/Navy #0A0F1D
CARD_BG = (18, 25, 46)           # Mobile Card Surface #12192E
CARD_HEADER_BG = (13, 19, 36)    # Header Surface #0D1324
CARD_BORDER = (45, 60, 95)       # Outer Card Stroke #2D3C5F
CYAN_ACCENT = (0, 229, 255)      # Terminal Neon Cyan #00E5FF
CYAN_DIM = (0, 130, 150)         # Secondary Cyan
TEXT_WHITE = (248, 250, 252)     # High Contrast White #F8FAFC
TEXT_MUTED = (148, 163, 184)     # Secondary Label Muted #94A3B8
ALERT_RED = (239, 68, 68)        # Notification Red
AMBER_DEFER = (245, 158, 11)     # Defer Amber
SLATE_ARCHIVE = (100, 116, 139)  # Archive Slate
GREEN_DONE = (16, 185, 129)      # Emerald Check
PILL_BG = (0, 0, 0)              # Black Contrast Pill

# --- TYPOGRAPHY HIERARCHY ---
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

font_pill = ImageFont.truetype(FONT_BOLD, 36)
font_title_lg = ImageFont.truetype(FONT_BOLD, 44)
font_h1 = ImageFont.truetype(FONT_BOLD, 38)
font_h2 = ImageFont.truetype(FONT_BOLD, 32)
font_body = ImageFont.truetype(FONT_REG, 28)
font_body_bold = ImageFont.truetype(FONT_BOLD, 28)
font_code = ImageFont.truetype(FONT_MONO, 24)
font_code_sm = ImageFont.truetype(FONT_MONO, 20)
font_small = ImageFont.truetype(FONT_REG, 22)

# --- VIEWPORT GEOMETRY ---
CARD_LEFT = 48
CARD_RIGHT = 1032
CARD_WIDTH = CARD_RIGHT - CARD_LEFT  # 984 px

# ==============================================================================
# AUTONOMOUS QUALITY & VERIFIER GATE
# ==============================================================================
def self_heal_layout(initial_config):
    passed, errors = audit.run_layout_audit(initial_config)
    if passed:
        print("[VERIFIER] Initial layout clean. Proceeding directly to render.")
        return initial_config

    print(f"[VERIFIER] Layout violations detected ({len(errors)}). Initiating autonomous healing...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY not found; using fallback coordinates.")
        return initial_config

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    prompt_text = f"""
    Fix vertical coordinate errors for a 1080x1920 layout.
    Rules: pill_y >= 380, card_bottom <= 1550, (card_top - pill_y) >= 70
    Active errors: {errors}
    Respond strictly with three lines:
    pill_y: <int>
    card_top: <int>
    card_bottom: <int>
    """
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            result_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            for line in result_text.strip().split("\n"):
                if "pill_y:" in line:
                    initial_config["pill_y"] = int(line.split(":")[1].strip())
                elif "card_top:" in line:
                    initial_config["card_top"] = int(line.split(":")[1].strip())
                elif "card_bottom:" in line:
                    initial_config["card_bottom"] = int(line.split(":")[1].strip())
    except Exception as e:
        print(f"[VERIFIER] Healing request failed: {e}")

    return initial_config

end_card_config = {
    "pill_y": 380,
    "card_top": 460,
    "card_bottom": 1540,
    "lines": ['COMMENT "MEETING" FOR THE PROMPT']
}
verified_config = self_heal_layout(end_card_config)

# ==============================================================================
# 1. AUDIO SYNTHESIS ENGINE
# ==============================================================================
print("[1/3] Synthesizing synchronized audio track...")
samplerate = 44100
total_samples = int(samplerate * DURATION)
audio = np.zeros(total_samples, dtype=np.float32)

# Dual-frequency chime at 0.0s
for offset, freq in [(0.0, 784.0), (0.12, 1046.5)]:
    idx_start = int(offset * samplerate)
    dur = 1.0
    t_chime = np.linspace(0, dur, int(dur * samplerate), endpoint=False)
    wave_c = 0.35 * np.sin(2 * np.pi * freq * t_chime) * np.exp(-t_chime * 5.0)
    idx_end = min(total_samples, idx_start + len(wave_c))
    audio[idx_start:idx_end] += wave_c[:idx_end - idx_start]

# Keystroke clicks (3.0s - 4.5s)
for click_time in [3.0, 3.2, 3.45, 3.7, 3.95, 4.2, 4.45]:
    idx_c = int(click_time * samplerate)
    t_click = np.linspace(0, 0.04, int(0.04 * samplerate), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t_click)) * np.exp(-t_click * 120.0) * 0.16
    idx_end = min(total_samples, idx_c + len(noise))
    audio[idx_c:idx_end] += noise[:idx_end - idx_c]

# Lo-Fi Beat (6.0s - 20.0s)
beat_interval = 0.75
start_beat = 6.0
end_beat = 20.0
chords = [
    [349.23, 440.00, 523.25, 659.25],
    [329.63, 392.00, 493.88, 587.33],
    [293.66, 349.23, 440.00, 523.25],
    [261.63, 329.63, 392.00, 493.88]
]
chord_len = beat_interval * 4
for c_idx in range(6):
    c_start = start_beat + c_idx * chord_len
    if c_start >= end_beat:
        break
    for n in chords[c_idx % len(chords)]:
        idx_s = int(c_start * samplerate)
        c_dur = min(chord_len, DURATION - c_start)
        if c_dur <= 0:
            break
        t_note = np.linspace(0, c_dur, int(c_dur * samplerate), endpoint=False)
        envelope = np.minimum(t_note * 4.0, 1.0) * np.exp(-t_note * 0.45)
        chord_wave = 0.04 * (np.sin(2 * np.pi * n * t_note) + 0.3 * np.sin(2 * np.pi * (n * 2) * t_note)) * envelope
        idx_e = min(total_samples, idx_s + len(chord_wave))
        audio[idx_s:idx_e] += chord_wave[:idx_e - idx_s]

curr_t = start_beat
b_count = 0
while curr_t < end_beat:
    idx_b = int(curr_t * samplerate)
    if b_count % 2 == 0:
        t_k = np.linspace(0, 0.25, int(0.25 * samplerate), endpoint=False)
        freq_k = 120.0 * np.exp(-t_k * 25.0) + 40.0
        kick = 0.45 * np.sin(2 * np.pi * np.cumsum(freq_k) / samplerate) * np.exp(-t_k * 14.0)
        idx_e = min(total_samples, idx_b + len(kick))
        audio[idx_b:idx_e] += kick[:idx_e - idx_b]
    else:
        t_s = np.linspace(0, 0.2, int(0.2 * samplerate), endpoint=False)
        snare = (0.2 * np.sin(2 * np.pi * 180.0 * t_s) * np.exp(-t_s * 25.0) +
                 0.25 * np.random.uniform(-1, 1, len(t_s)) * np.exp(-t_s * 18.0))
        idx_e = min(total_samples, idx_b + len(snare))
        audio[idx_b:idx_e] += snare[:idx_e - idx_b]

    for hh_off in [0.0, beat_interval / 2.0]:
        hh_idx = int((curr_t + hh_off) * samplerate)
        t_hh = np.linspace(0, 0.05, int(0.05 * samplerate), endpoint=False)
        hh = 0.08 * np.random.uniform(-1, 1, len(t_hh)) * np.exp(-t_hh * 90.0)
        idx_e = min(total_samples, hh_idx + len(hh))
        if hh_idx < total_samples:
            audio[hh_idx:idx_e] += hh[:idx_e - hh_idx]

    curr_t += beat_interval
    b_count += 1

fade_len = int(1.5 * samplerate)
audio[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
audio_int16 = ((audio / np.max(np.abs(audio))) * 0.95 * 32767).astype(np.int16)
audio_filename = "campaign_meeting_audio.wav"
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
    px, py = 34, 16
    x0, y0 = center_x - tw // 2 - px, center_y - th // 2 - py
    x1, y1 = center_x + tw // 2 + px, center_y + th // 2 + py
    draw_rounded_rect(draw, (x0, y0, x1, y1), radius=28, fill=bg, outline=border_color, width=3)
    draw.text((center_x - tw // 2, y0 + py - bbox[1]), text, font=font_pill, fill=text_color)

def draw_header(draw):
    draw.text((CARD_LEFT + 20, 68), "9:41", font=font_h2, fill=TEXT_MUTED)
    draw.text((CARD_RIGHT - 160, 72), "5G  100%", font=font_small, fill=TEXT_MUTED)
    draw.rounded_rectangle((CARD_LEFT, 130, CARD_RIGHT, 215), radius=16, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=2)
    draw.ellipse((CARD_LEFT + 30, 155, CARD_LEFT + 65, 190), fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 85, 152), "WORKFLOWSUPERAI // EXECUTIVE MATRIX", font=font_h2, fill=TEXT_WHITE)

def draw_watermark(draw):
    draw.text((CARD_LEFT + 20, 1840), "@workflowsuperai", font=font_h2, fill=CYAN_DIM)
    draw.text((CARD_RIGHT - 280, 1845), "AI EXECUTIVE PIPELINE", font=font_small, fill=TEXT_MUTED)

def draw_typewriter_lines(draw, lines, x, start_y, line_height, progress, frame, font, color,
                          cursor_color=CYAN_ACCENT, stream_window=0.75):
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
            if i == len(lines) - 1 and blinking:
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
# 3. SCENE IMPLEMENTATIONS (PROMPT 1)
# ==============================================================================

def render_scene_1(draw, progress, frame):
    """Scene 1: Hook - Meeting Transcript Chaos"""
    shake_x = int(math.sin(frame * 1.6) * 8 * max(0, 1.0 - progress * 2.2))
    shake_y = int(math.cos(frame * 1.6) * 5 * max(0, 1.0 - progress * 2.2))
    draw_pill(draw, "SPENDING 45 MINS ON MEETING RECAPS?", 540 + shake_x, 390 + shake_y,
              border_color=ALERT_RED, text_color=TEXT_WHITE)
    
    card_y = 500 + shake_y
    card_h = 720
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=ALERT_RED, width=3)
    draw.text((CARD_LEFT + 50, card_y + 45), "Raw Call Transcript (1,450 Words)", font=font_body_bold, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 50, card_y + 85), "Zoom Audio Sync • Disorganized Chunks", font=font_small, fill=TEXT_MUTED)
    
    snippets = [
        "Dave: 'Did we finalize Q4 cloud budget? AWS spending capped at $12k.'",
        "Sarah: 'I need to audit EC2 instances by next Thursday so we don't bleed.'",
        "Mark: 'Security audit blocked until legal signs off on SOC2 by Monday.'",
        "Dave: 'Okay, high priority. I will ping legal first thing tomorrow.'"
    ]
    my = card_y + 150
    for snippet in snippets:
        draw_rounded_rect(draw, (CARD_LEFT + 30, my, CARD_RIGHT - 30, my + 105), radius=14, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=1)
        draw.text((CARD_LEFT + 50, my + 35), snippet, font=font_small, fill=TEXT_MUTED)
        my += 125

    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 640, CARD_LEFT + 530, card_y + 695), radius=12, fill=(65, 20, 25))
    draw.text((CARD_LEFT + 50, card_y + 655), "MANUAL ADMIN FRICTION DETECTED", font=font_small, fill=(255, 140, 140))


def render_scene_2(draw, progress, frame):
    """Scene 2: System Prompt Deployment"""
    draw_pill(draw, "USE THIS CHIEF OF STAFF PROMPT", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 480
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rounded_rectangle((CARD_LEFT, card_y, CARD_RIGHT, card_y + 75), radius=28, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 35, card_y + 28, CARD_LEFT + 55, card_y + 48), fill=ALERT_RED)
    draw.ellipse((CARD_LEFT + 70, card_y + 28, CARD_LEFT + 90, card_y + 48), fill=AMBER_DEFER)
    draw.ellipse((CARD_LEFT + 105, card_y + 28, CARD_LEFT + 125, card_y + 48), fill=GREEN_DONE)
    draw.text((CARD_LEFT + 155, card_y + 22), "SYSTEM PROMPT : CHIEF_OF_STAFF.MD", font=font_code, fill=CYAN_ACCENT)
    
    prompt_lines = [
        "ACT AS: Executive Chief of Staff",
        "OBJECTIVE: Convert chaotic raw transcript into matrix",
        "",
        "OUTPUT STRUCTURE:",
        "1. Executive Summary (2-3 concise sentences)",
        "2. Key Decisions Made (Firm consensus only)",
        "3. Action Item Matrix: [Task | Owner | Priority | Deadline]",
        "",
        "CONSTRAINTS:",
        "- Eliminate conversational fluff & informal banter",
        "- Flag unassigned roles as '[Unassigned - Needs Review]'"
    ]
    draw_typewriter_lines(draw, prompt_lines, CARD_LEFT + 40, card_y + 115, 54, progress, frame, font_code, TEXT_WHITE, stream_window=0.70)


def render_scene_3(draw, progress, frame):
    """Scene 3: Generating Executive Summary"""
    draw_pill(draw, "STEP 1: EXECUTIVE CONSENSUS", 540, 410, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    
    card_y = 490
    card_h = 860
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw.text((CARD_LEFT + 50, card_y + 45), "EXECUTIVE SUMMARY GENERATED", font=font_h2, fill=CYAN_ACCENT)
    draw_rounded_rect(draw, (CARD_LEFT + 40, card_y + 110, CARD_RIGHT - 40, card_y + 360), radius=18, fill=(15, 35, 55), outline=CYAN_ACCENT, width=2)
    summary_text = [
        "The leadership team aligned on capping Q4 AWS cloud",
        "expenditure at $12,000/mo. Infrastructure audits are",
        "delegated to Sarah, while SOC2 legal approvals represent",
        "the single critical path blocker for upcoming client deals."
    ]
    sy = card_y + 140
    for line in summary_text:
        draw.text((CARD_LEFT + 65, sy), line, font=font_body, fill=TEXT_WHITE)
        sy += 48

    draw.text((CARD_LEFT + 50, card_y + 400), "FIRM STRATEGIC DECISIONS", font=font_h2, fill=GREEN_DONE)
    draw_rounded_rect(draw, (CARD_LEFT + 40, card_y + 460, CARD_RIGHT - 40, card_y + 780), radius=18, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=1)
    decisions = [
        "✔ Q4 Cloud Budget officially capped at $12k/month",
        "✔ Legal review escalated to Tier-1 High Priority",
        "✔ EC2 resource audit required before monthly renewal"
    ]
    dy = card_y + 500
    for dec in decisions:
        draw.text((CARD_LEFT + 65, dy), dec, font=font_body_bold, fill=TEXT_WHITE)
        dy += 85


def render_scene_4(draw, progress, frame):
    """Scene 4: Action Matrix Snaps into Place"""
    draw_pill(draw, "STEP 2: STRUCTURED ACTION MATRIX", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 960
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((CARD_LEFT + 45, card_y + 45), "DELEGATION MATRIX (MARKDOWN)", font=font_h2, fill=CYAN_ACCENT)
    
    rows = [
        ("Task Description", "Owner", "Priority", "Deadline"),
        ("Audit AWS EC2 instances", "Sarah", "MEDIUM", "Next Thurs"),
        ("Escalate SOC2 legal review", "Dave", "HIGH", "Tomorrow"),
        ("Finalize security audit file", "Mark", "HIGH", "Monday")
    ]
    ry = card_y + 120
    for i, (task, owner, priority, deadline) in enumerate(rows):
        is_header = (i == 0)
        row_bg = CARD_HEADER_BG if is_header else ((20, 32, 58) if i % 2 == 1 else CARD_BG)
        border_c = CYAN_ACCENT if is_header else CARD_BORDER
        draw_rounded_rect(draw, (CARD_LEFT + 30, ry, CARD_RIGHT - 30, ry + 120), radius=14, fill=row_bg, outline=border_c, width=2 if is_header else 1)
        
        draw.text((CARD_LEFT + 55, ry + 25), task, font=font_body_bold if is_header else font_body, fill=CYAN_ACCENT if is_header else TEXT_WHITE)
        meta = f"Owner: {owner}   |   Pri: {priority}   |   Due: {deadline}" if not is_header else "Metadata Tracking"
        draw.text((CARD_LEFT + 55, ry + 70), meta, font=font_small, fill=TEXT_MUTED if is_header else (CYAN_ACCENT if priority == "HIGH" else TEXT_MUTED))
        ry += 140

    badge_y = ry + 40
    draw_rounded_rect(draw, (CARD_LEFT + 40, badge_y, CARD_RIGHT - 40, badge_y + 80), radius=16, fill=(15, 35, 55), outline=GREEN_DONE, width=2)
    draw.text((CARD_LEFT + 80, badge_y + 25), "STATUS: 100% ACCOUNTABILITY & ZERO GUESSWORK", font=font_body_bold, fill=GREEN_DONE)


def render_scene_5(draw, progress, frame):
    """Scene 5: Transformation Contrast"""
    draw_pill(draw, "FROM CHAOS TO EXECUTIVE BRIEF", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 960
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 50, CARD_RIGHT - 30, card_y + 360), radius=20, fill=(35, 15, 20), outline=ALERT_RED, width=2)
    draw.text((CARD_LEFT + 60, card_y + 80), "BEFORE: 45 MINUTES LOST", font=font_h2, fill=ALERT_RED)
    draw.text((CARD_LEFT + 60, card_y + 140), "• Sifting through transcripts and Slack threads", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 200), "• Ambiguous verbal commitments ignored", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 260), "• High cognitive drain after every meeting", font=font_body, fill=TEXT_WHITE)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 400, CARD_RIGHT - 30, card_y + 710), radius=20, fill=(15, 35, 55), outline=GREEN_DONE, width=2)
    draw.text((CARD_LEFT + 60, card_y + 430), "AFTER: 10 SECONDS VIA AI", font=font_h2, fill=GREEN_DONE)
    draw.text((CARD_LEFT + 60, card_y + 490), "✔ Exact 2-sentence executive consensus", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 550), "✔ 4-column delegation matrix ready for email", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 610), "✔ Tasks assigned with zero follow-up friction", font=font_body, fill=TEXT_WHITE)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 750, CARD_RIGHT - 30, card_y + 880), radius=18, fill=CARD_HEADER_BG, outline=CYAN_ACCENT, width=2)
    draw.text((CARD_LEFT + 180, card_y + 800), "RECLAIM 5+ HOURS EVERY SINGLE WEEK", font=font_h2, fill=CYAN_ACCENT)


def render_scene_6(draw, progress, frame, pill_y=380, card_y=460):
    """Scene 6: Clear End Card Lead-In"""
    draw_pill(draw, 'COMMENT "MEETING" FOR PROMPT', 540, pill_y, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    
    card_h = 1080
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=32, fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    
    draw.text((CARD_LEFT + 340, card_y + 50), "@workflowsuperai", font=font_h2, fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 120, card_y + 130), "GET THE FULL CHIEF OF STAFF PROMPT", font=font_title_lg, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 210, card_y + 205), "+ FREE 7-PROMPT AI LIBRARY", font=font_h2, fill=TEXT_MUTED)
    
    term_top = card_y + 270
    term_h = 200
    draw_rounded_rect(draw, (CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + term_h), radius=20, fill=(10, 15, 29), outline=CYAN_ACCENT, width=2)
    draw.rounded_rectangle((CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + 55), radius=20, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 65, term_top + 20, CARD_LEFT + 80, term_top + 35), fill=ALERT_RED)
    draw.ellipse((CARD_LEFT + 95, term_top + 20, CARD_LEFT + 110, term_top + 35), fill=AMBER_DEFER)
    draw.ellipse((CARD_LEFT + 125, term_top + 20, CARD_LEFT + 140, term_top + 35), fill=GREEN_DONE)
    draw.text((CARD_LEFT + 165, term_top + 16), "TERMINAL // INBOUND TRIGGER", font=font_code_sm, fill=TEXT_MUTED)
    
    draw.text((CARD_LEFT + 80, term_top + 95), "> comment", font=font_h1, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 380, term_top + 95), '"MEETING"', font=font_h1, fill=CYAN_ACCENT)
    
    if (frame // 8) % 2 == 0:
        draw.rectangle((CARD_LEFT + 700, term_top + 100, CARD_LEFT + 725, term_top + 145), fill=CYAN_ACCENT)
        
    features = [
        "✔ 100% Free Executive Prompt Library",
        "✔ Instant Delivery to DMs or Inboxes",
        "✔ Production-Ready for ChatGPT & Claude"
    ]
    fy = card_y + 510
    for feat in features:
        draw.text((CARD_LEFT + 140, fy), feat, font=font_body, fill=TEXT_WHITE)
        fy += 62
        
    link_box_y = card_y + 720
    link_box_h = 280
    draw_rounded_rect(draw, (CARD_LEFT + 40, link_box_y, CARD_RIGHT - 40, link_box_y + link_box_h), radius=22, fill=(15, 23, 42), outline=CARD_BORDER, width=2)
    draw.text((CARD_LEFT + 220, link_box_y + 40), "OR ACCESS DIRECTLY VIA BEACONS:", font=font_code, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 175, link_box_y + 100), "🔗 beacons.ai/workflowsuperai", font=font_h1, fill=CYAN_ACCENT)
    
    draw_rounded_rect(draw, (CARD_LEFT + 180, link_box_y + 190, CARD_RIGHT - 180, link_box_y + 250), radius=16, fill=(28, 54, 110))
    draw.text((CARD_LEFT + 220, link_box_y + 204), "FREE 7-PROMPT AI LIBRARY IN BIO", font=font_h2, fill=TEXT_WHITE)

# ==============================================================================
# 4. COMPILATION PIPELINE
# ==============================================================================
output_mp4 = "campaign_meeting_21s.mp4"
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
    
    if t_sec < 3.0:
        render_scene_1(draw, t_sec / 3.0, frame_idx)
    elif t_sec < 6.0:
        render_scene_2(draw, (t_sec - 3.0) / 3.0, frame_idx)
    elif t_sec < 10.0:
        render_scene_3(draw, (t_sec - 6.0) / 4.0, frame_idx)
    elif t_sec < 14.0:
        render_scene_4(draw, (t_sec - 10.0) / 4.0, frame_idx)
    elif t_sec < 17.0:
        render_scene_5(draw, (t_sec - 14.0) / 3.0, frame_idx)
    else:
        render_scene_6(
            draw,
            (t_sec - 17.0) / 4.0,
            frame_idx,
            pill_y=verified_config.get("pill_y", 380),
            card_y=verified_config.get("card_top", 460)
        )
        
    proc.stdin.write(img.tobytes())

proc.stdin.close()
proc.wait()
print(f"[3/3] Video build successfully exported: {output_mp4}")
