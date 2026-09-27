import math
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ==============================================================================
# CAMPAIGN "BOUNDARY" - AUTOMATED VIDEO ENGINE (REFACTORED)
# Resolution: 1080x1920 (9:16 Vertical) | Frame Rate: 30 FPS | Runtime: 21.0s
# Fixes: End-card collision separation, typewriter streaming, 15%+ viewport expansion
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
SLACK_RED = (224, 30, 90)        # Urgent Notification Red #E01E5A
GREEN_DONE = (16, 185, 129)      # Validation Emerald #10B981
PILL_BG = (0, 0, 0)              # Pure Black Contrast Pill #000000

# --- TYPOGRAPHY HIERARCHY ---
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

font_pill = ImageFont.truetype(FONT_BOLD, 38)
font_title_lg = ImageFont.truetype(FONT_BOLD, 48)
font_h1 = ImageFont.truetype(FONT_BOLD, 42)
font_h2 = ImageFont.truetype(FONT_BOLD, 36)
font_body = ImageFont.truetype(FONT_REG, 34)
font_body_bold = ImageFont.truetype(FONT_BOLD, 34)
font_code = ImageFont.truetype(FONT_MONO, 30)
font_code_sm = ImageFont.truetype(FONT_MONO, 24)
font_small = ImageFont.truetype(FONT_REG, 24)

# --- EXPANDED VIEWPORT GEOMETRY (Mobile Density Enhancement) ---
CARD_LEFT = 48
CARD_RIGHT = 1032
CARD_WIDTH = CARD_RIGHT - CARD_LEFT  # 984 px

# ==============================================================================
# 1. AUDIO ENGINE (SYNCHRONIZED COMMERCIAL-CLEARED ASSET)
# ==============================================================================
print("[1/3] Synthesizing synchronized audio track...")
samplerate = 44100
total_samples = int(samplerate * DURATION)
audio = np.zeros(total_samples, dtype=np.float32)

# A. Chime Alert at 0.0s (Dual-frequency notification)
for offset, freq in [(0.0, 659.25), (0.12, 880.0)]:
    idx_start = int(offset * samplerate)
    dur = 1.2
    t_chime = np.linspace(0, dur, int(dur * samplerate), endpoint=False)
    wave_c = 0.35 * np.sin(2 * np.pi * freq * t_chime) * np.exp(-t_chime * 4.0)
    idx_end = min(total_samples, idx_start + len(wave_c))
    audio[idx_start:idx_end] += wave_c[:idx_end - idx_start]

# B. Keystroke Clicks during prompt stream (3.2s - 4.6s)
for click_time in [3.2, 3.4, 3.65, 3.9, 4.15, 4.4, 4.6]:
    idx_c = int(click_time * samplerate)
    t_click = np.linspace(0, 0.04, int(0.04 * samplerate), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t_click)) * np.exp(-t_click * 120.0) * 0.16
    idx_end = min(total_samples, idx_c + len(noise))
    audio[idx_c:idx_end] += noise[:idx_end - idx_c]

# C. Lo-Fi Instrumental Beat (6.0s - 20.0s at 80 BPM)
beat_interval = 0.75
start_beat = 6.0
end_beat = 20.0

chords = [
    [293.66, 349.23, 440.00, 523.25],  # Dm7
    [392.00, 493.88, 587.33, 698.46],  # G7
    [261.63, 329.63, 392.00, 493.88],  # Cmaj7
    [220.00, 261.63, 329.63, 392.00]   # Am7
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

# Rhythm Section (Kick, Snare, Hi-Hat)
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

# D. Metallic Click on Validation Badge (14.0s)
idx_m = int(14.0 * samplerate)
t_m = np.linspace(0, 0.15, int(0.15 * samplerate), endpoint=False)
m_click = 0.32 * np.sin(2 * np.pi * 2200.0 * t_m) * np.exp(-t_m * 40.0)
idx_e = min(total_samples, idx_m + len(m_click))
audio[idx_m:idx_e] += m_click[:idx_e - idx_m]

# E. Outro Fade (19.5s - 21.0s)
fade_len = int(1.5 * samplerate)
audio[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

audio_int16 = ((audio / np.max(np.abs(audio))) * 0.95 * 32767).astype(np.int16)
audio_filename = "campaign_boundary_audio.wav"
with wave.open(audio_filename, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio_int16.tobytes())
print("   -> Audio synthesized successfully.")

# ==============================================================================
# 2. RENDERING PRIMITIVES & DYNAMIC PACING HELPERS
# ==============================================================================
def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def draw_pill(draw, text, center_x, center_y, bg=PILL_BG, border_color=CYAN_ACCENT, text_color=TEXT_WHITE):
    bbox = font_pill.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    px, py = 38, 20
    x0 = center_x - tw // 2 - px
    y0 = center_y - th // 2 - py
    x1 = center_x + tw // 2 + px
    y1 = center_y + th // 2 + py
    draw_rounded_rect(draw, (x0, y0, x1, y1), radius=28, fill=bg, outline=border_color, width=3)
    draw.text((center_x - tw // 2, y0 + py - bbox[1]), text, font=font_pill, fill=text_color)

def draw_header(draw):
    draw.text((CARD_LEFT + 20, 68), "9:41", font=font_h2, fill=TEXT_MUTED)
    draw.text((CARD_RIGHT - 160, 72), "5G  100%", font=font_small, fill=TEXT_MUTED)
    draw.rounded_rectangle((CARD_LEFT, 130, CARD_RIGHT, 215), radius=16, fill=CARD_HEADER_BG, outline=CARD_BORDER, width=2)
    draw.ellipse((CARD_LEFT + 30, 155, CARD_LEFT + 65, 190), fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 85, 152), "WORKFLOWSUPERAI // PROMPT ENGINE", font=font_h2, fill=TEXT_WHITE)

def draw_watermark(draw):
    draw.text((CARD_LEFT + 20, 1840), "@workflowsuperai", font=font_h2, fill=CYAN_DIM)
    draw.text((CARD_RIGHT - 280, 1845), "AI EXECUTIVE PIPELINE", font=font_small, fill=TEXT_MUTED)

def draw_typewriter_lines(draw, lines, x, start_y, line_height, progress, frame, font, color,
                           cursor_color=CYAN_ACCENT, stream_window=0.75):
    """Progressive typewriter reveal synchronized with frame progress."""
    total_chars = sum(len(line) for line in lines)
    if total_chars == 0:
        return
    type_ratio = min(1.0, progress / stream_window)
    chars_to_render = int(type_ratio * total_chars)
    
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
    """Scene 1 (0:00 - 0:03): Hook & Incoming Slack Alert"""
    shake_x = int(math.sin(frame * 1.6) * 9 * max(0, 1.0 - progress * 2.2))
    shake_y = int(math.cos(frame * 1.6) * 6 * max(0, 1.0 - progress * 2.2))
    
    draw_pill(draw, "FRIDAY 6:30 PM SLACK PING?", 540 + shake_x, 390 + shake_y,
              border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    
    card_y = 520 + shake_y
    card_h = 580
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=SLACK_RED, width=3)
    
    # Slack App Header
    draw_rounded_rect(draw, (CARD_LEFT + 36, card_y + 38, CARD_LEFT + 116, card_y + 118), radius=16, fill=SLACK_RED)
    draw.text((CARD_LEFT + 54, card_y + 44), "#", font=font_title_lg, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 140, card_y + 45), "Slack  •  now", font=font_body, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 140, card_y + 85), "Dave (Team Lead)  in  #revenue-exec", font=font_h2, fill=TEXT_WHITE)
    
    # Message Body
    msg_lines = [
        '"Hey team, really need you to pull',
        'together the updated regional revenue',
        'deck over the weekend so leadership can',
        'review first thing Monday. Can you jump',
        'on this tonight?"'
    ]
    y_text = card_y + 160
    for line in msg_lines:
        draw.text((CARD_LEFT + 40, y_text), line, font=font_body, fill=(241, 245, 249))
        y_text += 58

    # Alert Chip
    draw_rounded_rect(draw, (CARD_LEFT + 40, card_y + 490, CARD_LEFT + 460, card_y + 545), radius=14, fill=(65, 20, 32))
    draw.text((CARD_LEFT + 60, card_y + 502), "URGENT • UNPLANNED OVERTIME", font=font_small, fill=(255, 120, 140))


def render_scene_2(draw, progress, frame):
    """Scene 2 (0:03 - 0:06): Dynamic Typewriter Stream of System Prompt"""
    draw_pill(draw, "STOP APOLOGIZING AT WORK", 540, 390, bg=(45, 12, 18), border_color=(239, 68, 68), text_color=TEXT_WHITE)
    
    card_y = 480
    card_h = 920
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Header tab
    draw.rounded_rectangle((CARD_LEFT, card_y, CARD_RIGHT, card_y + 75), radius=28, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 35, card_y + 28, CARD_LEFT + 55, card_y + 48), fill=(239, 68, 68))
    draw.ellipse((CARD_LEFT + 70, card_y + 28, CARD_LEFT + 90, card_y + 48), fill=(245, 158, 11))
    draw.ellipse((CARD_LEFT + 105, card_y + 28, CARD_LEFT + 125, card_y + 48), fill=(16, 185, 129))
    draw.text((CARD_LEFT + 155, card_y + 22), "SYSTEM PROMPT : BOUNDARY_ENGINE.MD", font=font_code, fill=CYAN_ACCENT)
    
    prompt_lines = [
        "ACT AS: Executive Communications Specialist",
        "OBJECTIVE: Draft firm, respectful boundary",
        "",
        "MANDATORY CONSTRAINTS:",
        "1. Length: Strictly under 75 words",
        "2. ZERO APOLOGIES (No 'sorry', 'unfortunately')",
        "3. ZERO passive-aggressive filler",
        "4. Include EXACTLY ONE closed-loop alternative",
        "",
        "TARGET INPUT: [Urgent Friday 6:30 PM Deck]",
        "RESUMPTION: [Monday morning at 8:30 AM CST]"
    ]
    
    draw_typewriter_lines(
        draw=draw,
        lines=prompt_lines,
        x=CARD_LEFT + 40,
        start_y=card_y + 110,
        line_height=56,
        progress=progress,
        frame=frame,
        font=font_code,
        color=TEXT_WHITE,
        stream_window=0.70
    )


def render_scene_3(draw, progress, frame):
    """Scene 3 (0:06 - 0:10): Generating Pulse & Streaming Compilation"""
    draw_pill(draw, "PASTE THIS PROMPT INSTEAD", 540, 420, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    
    card_y = 520
    card_h = 760
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Active Action Button
    btn_y = card_y + 50
    draw_rounded_rect(draw, (CARD_LEFT + 40, btn_y, CARD_RIGHT - 40, btn_y + 95), radius=20, fill=CYAN_ACCENT)
    draw.text((CARD_LEFT + 240, btn_y + 26), "⚡ GENERATING EXECUTIVE DRAFT...", font=font_h2, fill=(10, 15, 29))
    
    # Progress Bar Container
    bar_y = btn_y + 140
    draw_rounded_rect(draw, (CARD_LEFT + 40, bar_y, CARD_RIGHT - 40, bar_y + 24), radius=12, fill=(30, 41, 59))
    fill_w = int((CARD_LEFT + 40) + (CARD_WIDTH - 80) * progress)
    draw_rounded_rect(draw, (CARD_LEFT + 40, bar_y, fill_w, bar_y + 24), radius=12, fill=CYAN_ACCENT)
    
    # Streaming Diagnostics
    diag_box_y = bar_y + 70
    draw_rounded_rect(draw, (CARD_LEFT + 40, diag_box_y, CARD_RIGHT - 40, diag_box_y + 320), radius=20, fill=CARD_HEADER_BG)
    
    log_lines = [
        "> Initializing executive reasoning model...",
        "> Scanning input for off-hours scope creep...",
        "> Enforcing Zero-Apology constraint [CLEARED]",
        "> Filtering passive-aggressive filler [CLEARED]",
        "> Injecting Monday closed-loop alternative [READY]"
    ]
    dy = diag_box_y + 35
    visible_logs = min(len(log_lines), int(progress * 6) + 1)
    for i in range(visible_logs):
        color = GREEN_DONE if "[CLEARED]" in log_lines[i] or "[READY]" in log_lines[i] else TEXT_MUTED
        draw.text((CARD_LEFT + 70, dy), log_lines[i], font=font_code, fill=color)
        dy += 54


def render_scene_4(draw, progress, frame):
    """Scene 4 (0:10 - 0:14): Dynamic Streaming of Boundary Statement"""
    draw_pill(draw, "ZERO APOLOGIES. FIRM BOUNDARY.", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 960
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Email Header Bar
    draw.text((CARD_LEFT + 40, card_y + 40), "To: Dave (Team Lead)", font=font_body, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 40, card_y + 90), "Subject: Re: Regional Revenue Deck Update", font=font_body_bold, fill=TEXT_WHITE)
    draw.line((CARD_LEFT + 40, card_y + 148, CARD_RIGHT - 40, card_y + 148), fill=CARD_BORDER, width=2)
    
    # Salutation
    draw.text((CARD_LEFT + 40, card_y + 180), "Hi Dave,", font=font_body, fill=TEXT_WHITE)
    
    # Boundary Statement Stream
    boundary_lines = [
        "I am offline for the weekend and",
        "will not be available to work on",
        "the revenue deck before Monday."
    ]
    
    box_top = card_y + 250
    box_h = 280
    stream_complete = progress >= 0.55
    bg_box = (15, 34, 62) if stream_complete else (14, 20, 38)
    border_col = CYAN_ACCENT if stream_complete else CARD_BORDER
    
    draw_rounded_rect(draw, (CARD_LEFT + 30, box_top, CARD_RIGHT - 30, box_top + box_h),
                      radius=22, fill=bg_box, outline=border_col, width=3 if stream_complete else 1)
    
    draw_typewriter_lines(
        draw=draw,
        lines=boundary_lines,
        x=CARD_LEFT + 60,
        start_y=box_top + 45,
        line_height=64,
        progress=progress,
        frame=frame,
        font=font_h2,
        color=CYAN_ACCENT,
        stream_window=0.55
    )
    
    if stream_complete:
        badge_y = box_top + box_h + 40
        draw_rounded_rect(draw, (CARD_LEFT + 40, badge_y, CARD_LEFT + 560, badge_y + 60), radius=14, fill=(28, 54, 110))
        draw.text((CARD_LEFT + 65, badge_y + 14), "NO APOLOGIES • NO PERSONAL EXCUSES", font=font_small, fill=TEXT_WHITE)


def render_scene_5(draw, progress, frame):
    """Scene 5 (0:14 - 0:17): Dynamic Stream of Alternative Proposal & Word Counter Tick"""
    draw_pill(draw, "OFFER 1 CLOSED-LOOP ALTERNATIVE", 540, 390, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    
    card_y = 470
    card_h = 980
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h), radius=28, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Dimmed Boundary line
    draw.text((CARD_LEFT + 40, card_y + 36), "I am offline for the weekend...", font=font_body, fill=TEXT_MUTED)
    draw.line((CARD_LEFT + 40, card_y + 88, CARD_RIGHT - 40, card_y + 88), fill=CARD_BORDER, width=2)
    
    # Active Alternative Box
    box_top = card_y + 120
    box_h = 340
    draw_rounded_rect(draw, (CARD_LEFT + 30, box_top, CARD_RIGHT - 30, box_top + box_h),
                      radius=22, fill=(16, 42, 42), outline=GREEN_DONE, width=3)
    
    alt_lines = [
        "I can prioritize this first thing",
        "Monday morning at 8:30 AM and",
        "deliver the completed deck for",
        "review by 10:30 AM."
    ]
    
    draw_typewriter_lines(
        draw=draw,
        lines=alt_lines,
        x=CARD_LEFT + 60,
        start_y=box_top + 45,
        line_height=64,
        progress=progress,
        frame=frame,
        font=font_h2,
        color=TEXT_WHITE,
        stream_window=0.50
    )
    
    # Sign-off
    draw.text((CARD_LEFT + 40, box_top + box_h + 40), "Best regards,", font=font_body, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 40, box_top + box_h + 90), "Alex", font=font_body_bold, fill=TEXT_WHITE)
    
    # Dynamic Word Count Counter Widget
    widget_y = box_top + box_h + 170
    draw_rounded_rect(draw, (CARD_LEFT + 30, widget_y, CARD_RIGHT - 30, widget_y + 180),
                      radius=22, fill=CARD_HEADER_BG, outline=CYAN_ACCENT, width=2)
    
    curr_count = min(46, int(1 + progress * 70))
    draw.text((CARD_LEFT + 60, widget_y + 36), f"TOTAL EMAIL LENGTH : {curr_count} WORDS", font=font_h2, fill=GREEN_DONE)
    draw.text((CARD_LEFT + 60, widget_y + 98), "✔ STRICTLY UNDER 75 WORDS  •  100% COMPLIANT", font=font_code, fill=TEXT_MUTED)


def render_scene_6(draw, progress, frame):
    """Scene 6 (0:17 - 0:21): Overhauled End-Card (Zero Element Collisions)"""
    # 1. Top Call-To-Action Pill (Safe-Zone at Y = 380, cleanly above card)
    draw_pill(draw, 'COMMENT "BOUNDARY" FOR THE PROMPT', 540, 380, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    
    # 2. Main End-Card Container (Starts at Y = 460 with 80px breathing room from pill)
    card_y = 460
    card_h = 1080
    draw_rounded_rect(draw, (CARD_LEFT, card_y, CARD_RIGHT, card_y + card_h),
                      radius=32, fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    
    # A. Brand Identifier Header
    draw.text((CARD_LEFT + 340, card_y + 50), "@workflowsuperai", font=font_h2, fill=CYAN_ACCENT)
    
    # B. Main Titles
    draw.text((CARD_LEFT + 120, card_y + 130), "GET THE FULL SYSTEM PROMPT", font=font_title_lg, fill=TEXT_WHITE)
    draw.text((CARD_LEFT + 210, card_y + 205), "+ FREE 7-PROMPT AI LIBRARY", font=font_h2, fill=TEXT_MUTED)
    
    # C. Terminal Command Box (Positioned cleanly below title)
    term_top = card_y + 270
    term_h = 200
    draw_rounded_rect(draw, (CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + term_h),
                      radius=20, fill=(10, 15, 29), outline=CYAN_ACCENT, width=2)
    
    draw.rounded_rectangle((CARD_LEFT + 40, term_top, CARD_RIGHT - 40, term_top + 55),
                           radius=20, fill=CARD_HEADER_BG)
    draw.ellipse((CARD_LEFT + 65, term_top + 20, CARD_LEFT + 80, term_top + 35), fill=(239, 68, 68))
    draw.ellipse((CARD_LEFT + 95, term_top + 20, CARD_LEFT + 110, term_top + 35), fill=(245, 158, 11))
    draw.ellipse((CARD_LEFT + 125, term_top + 20, CARD_LEFT + 140, term_top + 35), fill=(16, 185, 129))
    draw.text((CARD_LEFT + 165, term_top + 16), "TERMINAL // INBOUND TRIGGER", font=font_code_sm, fill=TEXT_MUTED)
    
    draw.text((CARD_LEFT + 80, term_top + 95), "> comment", font=font_h1, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 380, term_top + 95), '"BOUNDARY"', font=font_h1, fill=CYAN_ACCENT)
    
    if (frame // 8) % 2 == 0:
        draw.rectangle((CARD_LEFT + 720, term_top + 100, CARD_LEFT + 745, term_top + 145), fill=CYAN_ACCENT)
        
    # D. Feature Value Props
    features = [
        "✔ 100% Free Executive Prompt Template",
        "✔ Instant Automated Delivery to DMs",
        "✔ Compatible with ChatGPT & Claude"
    ]
    fy = card_y + 510
    for feat in features:
        draw.text((CARD_LEFT + 140, fy), feat, font=font_body, fill=TEXT_WHITE)
        fy += 62
        
    # E. Dedicated Link Routing Box (Zero collision)
    link_box_y = card_y + 720
    link_box_h = 280
    draw_rounded_rect(draw, (CARD_LEFT + 40, link_box_y, CARD_RIGHT - 40, link_box_y + link_box_h),
                      radius=22, fill=(15, 23, 42), outline=CARD_BORDER, width=2)
    
    draw.text((CARD_LEFT + 220, link_box_y + 40), "OR ACCESS DIRECTLY VIA BEACONS:", font=font_code, fill=TEXT_MUTED)
    draw.text((CARD_LEFT + 175, link_box_y + 100), "🔗 beacons.ai/workflowsuperai", font=font_h1, fill=CYAN_ACCENT)
    
    draw_rounded_rect(draw, (CARD_LEFT + 180, link_box_y + 190, CARD_RIGHT - 180, link_box_y + 250),
                      radius=16, fill=(28, 54, 110))
    draw.text((CARD_LEFT + 220, link_box_y + 204), "FREE 7-PROMPT AI LIBRARY IN BIO", font=font_h2, fill=TEXT_WHITE)

# ==============================================================================
# 4. COMPILATION PIPELINE (DIRECT FFMPEG STREAM)
# ==============================================================================
output_mp4 = "campaign_boundary_21s.mp4"
print(f"[2/3] Streaming {TOTAL_FRAMES} frames to FFmpeg compiler...")

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",                     # Standard input pipe
    "-i", audio_filename,          # Audio track
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
    
    # Common Chrome
    draw_header(draw)
    draw_watermark(draw)
    
    # Scene Routing
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
        render_scene_6(draw, (t_sec - 17.0) / 4.0, frame_idx)
        
    proc.stdin.write(img.tobytes())

proc.stdin.close()
proc.wait()
print(f"[3/3] Video build successfully exported: {output_mp4}")
