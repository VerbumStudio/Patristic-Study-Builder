import math
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Canvas specifications
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 21.0
TOTAL_FRAMES = int(FPS * DURATION)  # 630 frames

# Color Palette
BG_COLOR = (10, 15, 29)          # Deep Slate/Navy #0A0F1D
CARD_BG = (20, 28, 51)           # #141C33
CARD_BORDER = (42, 54, 86)       # #2A3656
CYAN_ACCENT = (0, 229, 255)      # #00E5FF
CYAN_DIM = (0, 120, 140)
TEXT_WHITE = (248, 250, 252)     # #F8FAFC
TEXT_MUTED = (148, 163, 184)     # #94A3B8
SLACK_RED = (224, 30, 90)        # #E01E5A
GREEN_DONE = (16, 185, 129)      # #10B981
PILL_BG = (0, 0, 0)              # Pure Black #000000

# Fonts (Update paths to match your local system)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

font_pill = ImageFont.truetype(FONT_BOLD, 36)
font_h1 = ImageFont.truetype(FONT_BOLD, 46)
font_h2 = ImageFont.truetype(FONT_BOLD, 34)
font_body = ImageFont.truetype(FONT_REG, 30)
font_body_bold = ImageFont.truetype(FONT_BOLD, 30)
font_code = ImageFont.truetype(FONT_MONO, 26)
font_small = ImageFont.truetype(FONT_REG, 22)

# --- 1. AUDIO SYNTHESIS ---
samplerate = 44100
total_samples = int(samplerate * DURATION)
audio = np.zeros(total_samples, dtype=np.float32)

# Chime at 0.0s
for offset, freq in [(0.0, 659.25), (0.12, 880.0)]:
    idx_start = int(offset * samplerate)
    dur = 1.2
    t_chime = np.linspace(0, dur, int(dur * samplerate), endpoint=False)
    wave_c = 0.35 * np.sin(2 * np.pi * freq * t_chime) * np.exp(-t_chime * 4.0)
    idx_end = min(total_samples, idx_start + len(wave_c))
    audio[idx_start:idx_end] += wave_c[:idx_end - idx_start]

# Keystroke clicks (3.2s - 4.5s)
for click_time in [3.2, 3.45, 3.7, 4.0, 4.25, 4.5]:
    idx_c = int(click_time * samplerate)
    t_click = np.linspace(0, 0.04, int(0.04 * samplerate), endpoint=False)
    noise = np.random.uniform(-1, 1, len(t_click)) * np.exp(-t_click * 120.0) * 0.15
    idx_end = min(total_samples, idx_c + len(noise))
    audio[idx_c:idx_end] += noise[:idx_end - idx_c]

# Lo-Fi Beat (6.0s - 20.0s at 80 BPM)
beat_interval = 0.75
start_beat = 6.0
end_beat = 20.0

chords = [
    [293.66, 349.23, 440.00, 523.25], # Dm7
    [392.00, 493.88, 587.33, 698.46], # G7
    [261.63, 329.63, 392.00, 493.88], # Cmaj7
    [220.00, 261.63, 329.63, 392.00]  # Am7
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

current_t = start_beat
beat_count = 0
while current_t < end_beat:
    idx_b = int(current_t * samplerate)
    if beat_count % 2 == 0:
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

    for hh_offset in [0.0, beat_interval / 2.0]:
        hh_idx = int((current_t + hh_offset) * samplerate)
        t_hh = np.linspace(0, 0.05, int(0.05 * samplerate), endpoint=False)
        hh = 0.08 * np.random.uniform(-1, 1, len(t_hh)) * np.exp(-t_hh * 90.0)
        idx_e = min(total_samples, hh_idx + len(hh))
        if hh_idx < total_samples:
            audio[hh_idx:idx_e] += hh[:idx_e - hh_idx]

    current_t += beat_interval
    beat_count += 1

# Metallic click at 14.0s
idx_m = int(14.0 * samplerate)
t_m = np.linspace(0, 0.15, int(0.15 * samplerate), endpoint=False)
m_click = 0.3 * np.sin(2 * np.pi * 2200.0 * t_m) * np.exp(-t_m * 40.0)
idx_e = min(total_samples, idx_m + len(m_click))
audio[idx_m:idx_e] += m_click[:idx_e - idx_m]

# Fade out
fade_samples = int(1.5 * samplerate)
audio[-fade_samples:] *= np.linspace(1.0, 0.0, fade_samples)

audio_int16 = ((audio / np.max(np.abs(audio))) * 0.95 * 32767).astype(np.int16)
audio_filename = "campaign_boundary_audio.wav"
with wave.open(audio_filename, "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(samplerate)
    wf.writeframes(audio_int16.tobytes())

# --- 2. RENDERING HELPERS ---
def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def draw_pill(draw, text, center_x, center_y, bg=PILL_BG, border_color=CYAN_ACCENT, text_color=TEXT_WHITE):
    bbox = font_pill.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    px, py = 36, 18
    x0, y0 = center_x - tw // 2 - px, center_y - th // 2 - py
    x1, y1 = center_x + tw // 2 + px, center_y + th // 2 + py
    draw_rounded_rect(draw, (x0, y0, x1, y1), radius=28, fill=bg, outline=border_color, width=3)
    draw.text((center_x - tw // 2, y0 + py - bbox[1]), text, font=font_pill, fill=text_color)

def draw_header(draw):
    draw.text((80, 70), "9:41", font=font_h2, fill=TEXT_MUTED)
    draw.text((860, 70), "5G  100%", font=font_small, fill=TEXT_MUTED)
    draw.rounded_rectangle((80, 140, 1000, 220), radius=16, fill=(15, 23, 42), outline=CARD_BORDER, width=2)
    draw.ellipse((110, 165, 145, 200), fill=CYAN_ACCENT)
    draw.text((165, 162), "WORKFLOWSUPERAI // TERMINAL", font=font_h2, fill=TEXT_WHITE)

def draw_watermark(draw):
    draw.text((80, 1830), "@workflowsuperai", font=font_h2, fill=CYAN_DIM)
    draw.text((720, 1835), "AI WORKFLOWS", font=font_small, fill=TEXT_MUTED)

# --- 3. SCENES ---
def render_scene_1(draw, progress, frame):
    shake_x = int(math.sin(frame * 1.5) * 8 * max(0, 1.0 - progress * 2))
    shake_y = int(math.cos(frame * 1.5) * 5 * max(0, 1.0 - progress * 2))
    draw_pill(draw, "FRIDAY 6:30 PM SLACK PING?", 540 + shake_x, 420 + shake_y, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    
    card_y = 660 + shake_y
    draw_rounded_rect(draw, (80, card_y, 1000, card_y + 440), radius=28, fill=CARD_BG, outline=SLACK_RED, width=3)
    draw_rounded_rect(draw, (120, card_y + 40, 190, card_y + 110), radius=14, fill=SLACK_RED)
    draw.text((135, card_y + 46), "#", font=font_h1, fill=TEXT_WHITE)
    draw.text((215, card_y + 45), "Slack  •  now", font=font_body, fill=TEXT_MUTED)
    draw.text((215, card_y + 82), "Dave (Team Lead)  in  #general", font=font_h2, fill=TEXT_WHITE)
    
    msg = ['"Hey, really need you to pull together', 'the updated regional revenue deck over',
           'the weekend so leadership can review', 'first thing Monday. Can you do this tonight?"']
    y_t = card_y + 160
    for l in msg:
        draw.text((120, y_t), l, font=font_body, fill=(241, 245, 249))
        y_t += 52

def render_scene_2(draw, progress, frame):
    draw_pill(draw, "STOP APOLOGIZING AT WORK", 540, 420, bg=(40, 10, 15), border_color=(239, 68, 68), text_color=TEXT_WHITE)
    box_y = 560
    draw_rounded_rect(draw, (80, box_y, 1000, box_y + 680), radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.rounded_rectangle((80, box_y, 1000, box_y + 70), radius=24, fill=(15, 23, 42))
    draw.text((240, box_y + 20), "SYSTEM PROMPT : BOUNDARY_DRAFTER.MD", font=font_code, fill=CYAN_ACCENT)
    
    prompt = ["ACT AS: Executive Communications Specialist", "OBJECTIVE: Draft firm, professional boundary",
              "", "STRICT CONSTRAINTS:", "• Under 75 words total", "• ZERO APOLOGIES (No 'sorry', 'unfortunately')",
              "• ZERO passive-aggressive filler", "• Offer EXACTLY ONE closed-loop alternative"]
    y_p = box_y + 95
    for i in range(min(len(prompt), int(progress * 15) + 3)):
        color = CYAN_ACCENT if "ZERO" in prompt[i] or "STRICT" in prompt[i] else TEXT_WHITE
        draw.text((120, y_p), prompt[i], font=font_code, fill=color)
        y_p += 48

def render_scene_3(draw, progress, frame):
    draw_pill(draw, "PASTE THIS PROMPT INSTEAD", 540, 460, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    box_y = 600
    draw_rounded_rect(draw, (80, box_y, 1000, box_y + 540), radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw_rounded_rect(draw, (120, box_y + 50, 960, box_y + 140), radius=20, fill=CYAN_ACCENT)
    draw.text((340, box_y + 74), "⚡ GENERATING RESPONSE...", font=font_h2, fill=(10, 15, 29))
    draw_rounded_rect(draw, (120, box_y + 180, 960, box_y + 200), radius=10, fill=(30, 41, 59))
    draw_rounded_rect(draw, (120, box_y + 180, int(120 + 840 * progress), box_y + 200), radius=10, fill=CYAN_ACCENT)

def render_scene_4(draw, progress, frame):
    draw_pill(draw, "ZERO APOLOGIES. FIRM BOUNDARY.", 540, 420, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    card_y = 560
    draw_rounded_rect(draw, (80, card_y, 1000, card_y + 760), radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((120, card_y + 40), "To: Dave (Team Lead)", font=font_body, fill=TEXT_MUTED)
    draw.text((120, card_y + 85), "Subject: Re: Regional Revenue Deck", font=font_body_bold, fill=TEXT_WHITE)
    draw_rounded_rect(draw, (110, card_y + 240, 970, card_y + 450), radius=18, fill=(15, 30, 55), outline=CYAN_ACCENT, width=3)
    b_lines = ["I am offline for the weekend and", "will not be available to work on", "the revenue deck before Monday."]
    by = card_y + 270
    for bl in b_lines:
        draw.text((140, by), bl, font=font_h2, fill=CYAN_ACCENT)
        by += 55

def render_scene_5(draw, progress, frame):
    draw_pill(draw, "OFFER 1 CLOSED-LOOP ALTERNATIVE", 540, 420, border_color=CYAN_ACCENT, text_color=TEXT_WHITE)
    card_y = 540
    draw_rounded_rect(draw, (80, card_y, 1000, card_y + 800), radius=24, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw_rounded_rect(draw, (110, card_y + 120, 970, card_y + 360), radius=18, fill=(16, 40, 40), outline=GREEN_DONE, width=3)
    alt = ["I can prioritize this first thing", "Monday morning at 8:30 AM and", "deliver the completed deck for", "review by 10:30 AM."]
    ay = card_y + 145
    for a in alt:
        draw.text((140, ay), a, font=font_h2, fill=TEXT_WHITE)
        ay += 50
    badge_y = card_y + 540
    draw_rounded_rect(draw, (120, badge_y, 960, badge_y + 160), radius=20, fill=(15, 23, 42), outline=CYAN_ACCENT, width=2)
    draw.text((160, badge_y + 35), "TOTAL EMAIL LENGTH : 46 WORDS", font=font_h2, fill=GREEN_DONE)
    draw.text((160, badge_y + 90), "✔ STRICTLY UNDER 75 WORDS  •  100% COMPLIANT", font=font_code, fill=TEXT_MUTED)

def render_scene_6(draw, progress, frame):
    card_y = 480
    draw_rounded_rect(draw, (80, card_y, 1000, card_y + 940), radius=32, fill=CARD_BG, outline=CYAN_ACCENT, width=3)
    draw.text((360, card_y + 70), "@workflowsuperai", font=font_h2, fill=CYAN_ACCENT)
    draw.text((190, card_y + 170), "GET THE FULL SYSTEM PROMPT", font=font_h1, fill=TEXT_WHITE)
    term_y = card_y + 340
    draw_rounded_rect(draw, (130, term_y, 950, term_y + 130), radius=20, fill=(10, 15, 29), outline=CYAN_ACCENT, width=3)
    draw.text((165, term_y + 40), "> comment", font=font_h1, fill=TEXT_MUTED)
    draw.text((450, term_y + 40), "BOUNDARY", font=font_h1, fill=CYAN_ACCENT)
    draw_pill(draw, 'COMMENT "BOUNDARY" FOR THE PROMPT', 540, 820, border_color=CYAN_ACCENT, text_color=CYAN_ACCENT)
    draw.text((240, card_y + 720), "Instant Automated DM Delivery", font=font_h2, fill=TEXT_WHITE)
    draw.text((280, card_y + 780), "beacons.ai/workflowsuperai", font=font_code, fill=CYAN_ACCENT)

# --- 4. COMPILE ---
output_mp4 = "campaign_boundary_21s.mp4"
ffmpeg_cmd = [
    "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(FPS),
    "-i", "-", "-i", audio_filename, "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "fast", "-crf", "19", "-c:a", "aac", "-b:a", "192k", "-shortest", output_mp4
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
        render_scene_6(draw, (t_sec - 17.0) / 4.0, frame_idx)
        
    proc.stdin.write(img.tobytes())

proc.stdin.close()
proc.wait()
