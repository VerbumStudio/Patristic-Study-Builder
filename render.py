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
# CAMPAIGN: DAY 02 - MEETING TO ACTION MATRIX
# Resolution: 1080x1920 (9:16 Vertical) | Frame Rate: 30 FPS | Runtime: 20.0s
# Trigger: "MEETING" | Brand: @workflowsuperai
# ==============================================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 20.0
TOTAL_FRAMES = int(FPS * DURATION)  # 600 frames

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
font_title_lg = ImageFont.truetype(FONT_BOLD, 42)
font_h1 = ImageFont.truetype(FONT_BOLD, 36)
font_h2 = ImageFont.truetype(FONT_BOLD, 30)
font_body = ImageFont.truetype(FONT_REG, 26)
font_body_bold = ImageFont.truetype(FONT_BOLD, 26)
font_code = ImageFont.truetype(FONT_MONO, 24)
font_code_sm = ImageFont.truetype(FONT_MONO, 19)
font_table_hdr = ImageFont.truetype(FONT_BOLD, 22)
font_table_cell = ImageFont.truetype(FONT_REG, 21)
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
    "lines": ['COMMENT "MEETING" FOR PROMPT']
}
audit.run_audit(initial_config)

# ==============================================================================
# 1. AUDIO SYNTHESIS ENGINE
# ==============================================================================
print("[1/3] Synthesizing synchronized high-retention audio track...")
samplerate = 44100
total_samples = int(samplerate * DURATION)
audio = np.zeros(total_samples, dtype=np.float32)

# Sharp kinetic opener chime at 0.0s
for offset, freq in [(0.0, 880.0), (0.09, 1318.5)]:
    idx_start = int(offset * samplerate)
    dur = 0.8
    t_chime = np.linspace(0, dur, int(dur * samplerate), endpoint=False)
    wave_c = 0.38 * np.sin(2 * np.pi * freq * t_chime) * np.exp(-t_chime * 6.0)
    idx_end = min(total_samples, idx_start + len(wave_c))
    audio[idx_start:idx_end] += wave_c[:idx_end - idx_start]

# Rapid mechanical keystrokes (1.2s - 2.8s)
for click_time in [1.2, 1.35, 1.5, 1.7, 1.9, 2.1, 2.3, 2.5, 2.7]:
    idx_c = int(click_time * samplerate)
    t_click = np.linspace(0, 0.035, int(0.035 * samplerate), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t_click)) * np.exp(-t_click * 140.0) * 0.18
    idx_end = min(total_samples, idx_c + len(noise))
    audio[idx_c:idx_end] += noise[:idx_end - idx_c]

# Lo-Fi Progression (4.0s - 19.5s)
beat_interval = 0.70
start_beat = 4.0
end_beat = 19.5
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
        chord_wave = 0.045 * (np.sin(2 * np.pi * n * t_note) + 0.3 * np.sin(2 * np.pi * (n * 2) * t_note)) * envelope
        idx_e = min(total_samples, idx_s + len(chord_wave))
        audio[idx_s:idx_e] += chord_wave[:idx_e - idx_s]

curr_t = start_beat
b_count = 0
while curr_t < end_beat:
    idx_b = int(curr_t * samplerate)
    if b_count % 2 == 0:
        t_k = np.linspace(0, 0.22, int(0.22 * samplerate), endpoint=False)
        freq_k = 130.0 * np.exp(-t_k * 28.0) + 42.0
        kick = 0.45 * np.sin(2 * np.pi * np.cumsum(freq_k) / samplerate) * np.exp(-t_k * 15.0)
        idx_e = min(total_samples, idx_b + len(kick))
        audio[idx_b:idx_e] += kick[:idx_e - idx_b]
    else:
        t_s = np.linspace(0, 0.18, int(0.18 * samplerate), endpoint=False)
        snare = (0.2 * np.sin(2 * np.pi * 190.0 * t_s) * np.exp(-t_s * 26.0) +
                 0.25 * np.random.uniform(-1, 1, len(t_s)) * np.exp(-t_s * 19.0))
        idx_e = min(total_samples, idx_b + len(snare))
        audio[idx_b:idx_e] += snare[:idx_e - idx_b]

    for hh_off in [0.0, beat_interval / 2.0]:
        hh_idx = int((curr_t + hh_off) * samplerate)
        t_hh = np.linspace(0, 0.04, int(0.04 * samplerate), endpoint=False)
        hh = 0.07 * np.random.uniform(-1, 1, len(t_hh)) * np.exp(-t_hh * 95.0)
        idx_e = min(total_samples, hh_idx + len(hh))
        if hh_idx < total_samples:
            audio[hh_idx:idx_e] += hh[:idx_e - hh_idx]

    curr_t += beat_interval
    b_count += 1

fade_len = int(1.2 * samplerate)
audio[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
audio_int16 = ((audio / np.max(np.abs(audio))) * 0.95 * 32767).astype(np.int16)
audio_filename = "day02_meeting_audio.wav"
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
    draw.text((CARD_LEFT + 85, 152), "WORKFLOWSUPERAI // CHIEF OF STAFF", font=font_h2, fill=TEXT_WHITE)

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
# 3. SCENE IMPLEMENTATIONS
# ==============================================================================

def render_scene_1(draw, progress, frame):
    offset_y = int(progress * 40)
    draw_pill(draw, "STOP WRITING MEETING RECAPS", 540, 390, border_color=ALERT_RED, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 760
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=ALERT_RED, width=3)
    
    draw.rounded_rectangle((CARD_LEFT + 30, card_y + 35, CARD_LEFT + 320, card_y + 85), radius=12, fill=(45, 15, 20))
    draw.text((CARD_LEFT + 45, card_y + 46), "45-MIN RAW TRANSCRIPT", font=font_code_sm, fill=ALERT_RED)
    
    lines = [
        "Dave: 'Did we cap Q4 cloud spend at $12k?'",
        "Sarah: 'I will audit EC2 instances next Thurs.'",
        "Mark: 'SOC2 signoff blocks the enterprise deal.'",
        "Dave: 'I will escalate to legal tomorrow morning.'",
        "Sarah: 'Who owns the Notion sprint updates?'",
        "Mark: 'Unassigned. We need to decide today.'"
    ]
    sy = card_y + 115 - offset_y
    for l in lines:
        if card_y + 100 <= sy <= card_y + card_h - 100:
            draw_rounded_rect(draw, (CARD_LEFT + 30, sy, CARD_RIGHT - 30, sy + 75), radius=12, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=1)
            draw.text((CARD_LEFT + 50, sy + 22), l, font=font_code_sm, fill=TEXT_MUTED)
        sy += 90

    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + card_h - 85, CARD_RIGHT - 30, card_y + card_h - 25), radius=12, fill=(65, 20, 25))
    draw.text((CARD_LEFT + 220, card_y + card_h - 65), "COGNITIVE OVERLOAD: 45 MINS WASTED", font=font_body_bold, fill=(255, 140, 140))


def render_scene_2(draw, progress, frame):
    draw_pill(draw, "1 PROMPT TURNS IT INTO A MATRIX", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw.rounded_rectangle((CARD_LEFT, card_y, CARD_RIGHT, card_y + 75), radius=28, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 35, card_y + 28, CARD_LEFT + 55, card_y + 48), fill=ALERT_RED)
    draw.ellipse((CARD_LEFT + 70, card_y + 28, CARD_LEFT + 90, card_y + 48), fill=AMBER_DEFER)
    draw.ellipse((CARD_LEFT + 105, card_y + 28, CARD_LEFT + 125, card_y + 48), fill=GREEN_DONE)
    draw.text((CARD_LEFT + 155, card_y + 22), "SYSTEM PROMPT : CHIEF_OF_STAFF.MD", font=font_code, fill=CYAN_ACCENT)
    
    prompt_lines = [
        "ACT AS: Executive Chief of Staff",
        "INPUT: Raw chaotic meeting transcript",
        "",
        "OPERATIONAL DIRECTIVE:",
        "1. Synthesize exactly 2 sentences of Consensus.",
        "2. Extract non-negotiable Decisions Made.",
        "3. Output a strict 4-Column Markdown Table:",
        "   | TASK | OWNER | PRIORITY | DEADLINE |",
        "",
        "RULES:",
        "- Eliminate all filler and conversational tangents.",
        "- Mark missing roles as [UNASSIGNED]."
    ]
    draw_typewriter_lines(draw, prompt_lines, CARD_LEFT + 40, card_y + 115, 52, progress, frame, font_code, TEXT_WHITE, stream_window=0.75)


def render_scene_3(draw, progress, frame):
    draw_pill(draw, "STEP 1: EXECUTIVE CONSENSUS", 540, 390, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    
    card_y = 470
    card_h = 880
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw.text((CARD_LEFT + 40, card_y + 40), "EXECUTIVE SUMMARY (SYNTHESIZED)", font=font_h2, fill=CYAN_ACCENT)
    draw_rounded_rect(draw, (CARD_LEFT + 35, card_y + 90, CARD_RIGHT - 35, card_y + 310), radius=16, fill=(15, 35, 55), outline=CYAN_ACCENT, width=2)
    summary_text = [
        "Leadership reached consensus to cap Q4 cloud spend",
        "at $12,000/mo while prioritizing immediate SOC2",
        "compliance to prevent enterprise client deal delays."
    ]
    sy = card_y + 125
    for line in summary_text:
        draw.text((CARD_LEFT + 60, sy), line, font=font_body, fill=TEXT_WHITE)
        sy += 50

    draw.text((CARD_LEFT + 40, card_y + 360), "FIRM DECISIONS LOCKED", font=font_h2, fill=GREEN_DONE)
    draw_rounded_rect(draw, (CARD_LEFT + 35, card_y + 410, CARD_RIGHT - 35, card_y + 760), radius=16, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=1)
    decisions = [
        ("✔ AWS Cloud Cap:", "Hard limit locked at $12k/month"),
        ("✔ Legal Escalation:", "SOC2 audit marked Tier-1 priority"),
        ("✔ EC2 Resource Audit:", "Sarah leading infrastructure review")
    ]
    dy = card_y + 445
    for title, desc in decisions:
        draw.text((CARD_LEFT + 60, dy), title, font=font_body_bold, fill=TEXT_WHITE)
        draw.text((CARD_LEFT + 60, dy + 40), desc, font=font_body, fill=TEXT_MUTED)
        dy += 95


def render_scene_4(draw, progress, frame):
    draw_pill(draw, "STEP 2: DELEGATION MATRIX (GRID)", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
    
    draw.text((CARD_LEFT + 40, card_y + 35), "ACTION ITEM MATRIX (MARKDOWN GRID)", font=font_h2, fill=CYAN_ACCENT)
    
    tbl_x = CARD_LEFT + 30
    tbl_y = card_y + 90
    tbl_w = CARD_WIDTH - 60
    tbl_h = 620
    
    draw_rounded_rect(draw, (tbl_x, tbl_y, tbl_x + tbl_w, tbl_y + tbl_h), radius=14, fill=CARD_HEADER_BG, outline=CYAN_ACCENT, width=2)
    
    c0 = tbl_x
    c1 = tbl_x + 420
    c2 = tbl_x + 580
    c3 = tbl_x + 750
    c4 = tbl_x + tbl_w
    
    draw.rectangle((c0, tbl_y, c4, tbl_y + 75), fill=(24, 45, 78))
    draw.line((c0, tbl_y + 75, c4, tbl_y + 75), fill=CYAN_ACCENT, width=2)
    draw.text((c0 + 20, tbl_y + 24), "TASK DESCRIPTION", font=font_table_hdr, fill=CYAN_ACCENT)
    draw.text((c1 + 20, tbl_y + 24), "OWNER", font=font_table_hdr, fill=CYAN_ACCENT)
    draw.text((c2 + 20, tbl_y + 24), "PRIORITY", font=font_table_hdr, fill=CYAN_ACCENT)
    draw.text((c3 + 20, tbl_y + 24), "DEADLINE", font=font_table_hdr, fill=CYAN_ACCENT)
    
    for div_x in [c1, c2, c3]:
        draw.line((div_x, tbl_y, div_x, tbl_y + tbl_h), fill=CARD_BORDER, width=1)
        
    rows = [
        ("Audit EC2 instances", "Sarah", "MEDIUM", "Next Thurs", TEXT_MUTED),
        ("Escalate SOC2 legal review", "Dave", "HIGH", "Tomorrow", ALERT_RED),
        ("Finalize security file", "Mark", "HIGH", "Monday", ALERT_RED),
        ("Sprint Notion updates", "[UNASSIGNED]", "LOW", "Pending", AMBER_DEFER)
    ]
    
    row_y = tbl_y + 75
    row_h = 135
    for task, owner, pri, due, pri_col in rows:
        draw.line((c0, row_y + row_h, c4, row_y + row_h), fill=CARD_BORDER, width=1)
        draw.text((c0 + 20, row_y + 40), task, font=font_table_cell, fill=TEXT_WHITE)
        draw.text((c1 + 20, row_y + 40), owner, font=font_table_cell, fill=TEXT_WHITE if "[" not in owner else AMBER_DEFER)
        draw.text((c2 + 20, row_y + 40), pri, font=font_table_hdr, fill=pri_col)
        draw.text((c3 + 20, row_y + 40), due, font=font_table_cell, fill=TEXT_MUTED)
        row_y += row_h

    badge_y = card_y + 750
    draw_rounded_rect(draw, (CARD_LEFT + 35, badge_y, CARD_RIGHT - 35, badge_y + 110), radius=16, fill=(15, 35, 55), outline=GREEN_DONE, width=2)
    draw.text((CARD_LEFT + 70, badge_y + 25), "STATUS: 100% ACCOUNTABILITY & CLARITY", font=font_body_bold, fill=GREEN_DONE)
    draw.text((CARD_LEFT + 70, badge_y + 65), "Zero ambiguous follow-ups • Ready to deploy in email", font=font_small, fill=TEXT_WHITE)


def render_scene_5(draw, progress, frame):
    draw_pill(draw, "45 MINS -> 10 SECONDS", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 45, CARD_RIGHT - 30, card_y + 355), radius=20, fill=(35, 15, 20), outline=ALERT_RED, width=2)
    draw.text((CARD_LEFT + 60, card_y + 75), "BEFORE: 45 MINUTES LOST", font=font_h2, fill=ALERT_RED)
    draw.text((CARD_LEFT + 60, card_y + 140), "• Sifting through transcripts and messy scratch notes", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 200), "• Ambiguous verbal commitments slip through cracks", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 260), "• High mental fatigue after back-to-back calls", font=font_body, fill=TEXT_WHITE)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 395, CARD_RIGHT - 30, card_y + 705), radius=20, fill=(15, 35, 55), outline=GREEN_DONE, width=2)
    draw.text((CARD_LEFT + 60, card_y + 425), "AFTER: 10 SECONDS WITH AI", font=font_h2, fill=GREEN_DONE)
    draw.text((CARD_LEFT + 60, card_y + 490), "✔ Exact 2-sentence executive consensus ready for Slack", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 550), "✔ 4-column delegation grid with dates and owners", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 60, card_y + 610), "✔ Missing roles automatically flagged for review", font=font_body, fill=TEXT_WHITE)
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, card_y + 745, CARD_RIGHT - 30, card_y + 865), radius=18, fill=CARD_HEADER_BG, outline=CYAN_ACCENT, width=2)
    draw.text((CARD_LEFT + 155, card_y + 790), "RECLAIM 5+ HOURS EVERY SINGLE WEEK", font=font_h2, fill=CYAN_ACCENT)


def render_scene_6(draw, progress, frame):
    pill_y = 380
    card_y = 460
    card_h = 950
    
    draw_pill(draw, 'COMMENT "MEETING" FOR PROMPT', 540, pill_y, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=32, fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    
    draw.text((CARD_LEFT + 340, card_y + 40), "@workflowsuperai", font=font_h2, fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 95, card_y + 105), "GET THE CHIEF OF STAFF PROMPT", font=font_title_lg, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 220, card_y + 175), "+ FREE 7-PROMPT AI LIBRARY", font=font_h2, fill=TEXT_MUTED)
    
    term_top = card_y + 240
    term_h = 175
    draw_rounded_rect(draw, (CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + term_h), radius=20, fill=(10, 15, 29), outline=CYAN_ACCENT, width=2)
    draw.rounded_rectangle((CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + 50), radius=20, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 65, term_top + 18, CARD_LEFT + 80, term_top + 33), fill=ALERT_RED)
    draw.ellipse((CARD_LEFT + 95, term_top + 18, CARD_LEFT + 110, term_top + 33), fill=AMBER_DEFER)
    draw.ellipse((CARD_LEFT + 125, term_top + 18, CARD_LEFT + 140, term_top + 33), fill=GREEN_DONE)
    draw.text((CARD_LEFT + 165, term_top + 14), "TERMINAL // INBOUND TRIGGER", font=font_code_sm, fill=TEXT_MUTED)
    
    draw.text((CARD_LEFT + 80, term_top + 85), "> comment", font=font_h1, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 380, term_top + 85), '"MEETING"', font=font_h1, fill=CYAN_ACCENT)
    if (frame // 8) % 2 == 0:
        draw.rectangle((CARD_LEFT + 700, term_top + 90, CARD_LEFT + 725, term_top + 130), fill=CYAN_ACCENT)

    features = [
        "✔ 100% Free Executive Workflow Prompt",
        "✔ Instant Delivery to DMs or Inboxes",
        "✔ Production-Ready for ChatGPT & Claude"
    ]
    fy = card_y + 450
    for feat in features:
        draw.text((CARD_LEFT + 120, fy), feat, font=font_body, fill=TEXT_WHITE)
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
output_mp4 = "day02_meeting_matrix_20s.mp4"
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
