import subprocess
import sys
import os
import shutil
import base64

print("[*] Installing rendering dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])

from playwright.sync_api import sync_playwright

output_dir = "recordings"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)

# Scan repository for target images (prioritizing executive_ai_os.png)
print("[*] Scanning repository for image assets...")
found_path = None
target_names = ["executive_ai_os.png", "ai_prompt_library.png"]

for target in target_names:
    for root, _, files in os.walk("."):
        for file in files:
            if file.lower() == target.lower():
                found_path = os.path.join(root, file)
                break
        if found_path:
            break
    if found_path:
        break

img_src = ""
if found_path and os.path.exists(found_path):
    print(f"[✓] Located asset: {found_path}")
    with open(found_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(found_path)[1].lower().replace(".", "")
        if ext == "jpg": 
            ext = "jpeg"
        img_src = f"data:image/{ext};base64,{b64}"
else:
    print(f"[!] Target graphic not found. Checked: {os.listdir('.')}")

with open("template.html", "r", encoding="utf-8") as f:
    html_content = f.read()

rendered_html = html_content.replace("__HERO_ASSET__", img_src)
temp_html = os.path.abspath("temp_rendered.html")
with open(temp_html, "w", encoding="utf-8") as f:
    f.write(rendered_html)

print("[*] Recording fast-paced 15-second marketing reel...")
with sync_playwright() as p:
    browser = p.chromium.launch(
        args=[
            "--no-sandbox", 
            "--disable-setuid-sandbox",
            "--background-color=#000000"
        ]
    )
    context = browser.new_context(
        viewport={"width": 1080, "height": 1920},
        record_video_dir=output_dir,
        record_video_size={"width": 1080, "height": 1920}
    )
    page = context.new_page()
    page.goto(f"file://{temp_html}", wait_until="networkidle")

    # Tight 15-second total timeline
    page.wait_for_timeout(15000)

    context.close()
    browser.close()

if os.path.exists(temp_html):
    os.remove(temp_html)

recorded_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".webm")]
if not recorded_files:
    raise RuntimeError("No recording produced.")

raw_video = recorded_files[0]
print("[*] Synthesizing elevated UI SFX and mastering audio...")

# High-volume procedural sound effects (Clicks, alerts, bass impact, whooshes)
audio_cmd = (
    "ffmpeg -y "
    "-f lavfi -i anullsrc=r=44100:cl=stereo:d=15 "
    # Louder, snappier mechanical clicks (2.8s-5.2s)
    "-f lavfi -i \"anoisesrc=d=2.4:c=white:r=44100,volume=2.2,bandpass=f=2800:w=1400\" "
    # Distinct tech alert chime (5.4s)
    "-f lavfi -i \"sine=f=1046:d=0.35,volume=1.8\" "
    # Punchy tech hit for Option A (5.8s)
    "-f lavfi -i \"sine=f=440:d=0.25,volume=1.6\" "
    # Sharp tech hit for Option B (7.0s)
    "-f lavfi -i \"sine=f=587:d=0.25,volume=1.6\" "
    # Deep bass drop for Final Payoff (10.5s)
    "-f lavfi -i \"sine=f=130:d=0.8,volume=2.4\" "
    "-filter_complex \""
    "[1]adelay=2800|2800[clicks];"
    "[2]adelay=5400|5400[alert];"
    "[3]adelay=5800|5800[hit_a];"
    "[4]adelay=7000|7000[hit_b];"
    "[5]adelay=10500|10500[bass_drop];"
    "[0][clicks][alert][hit_a][hit_b][bass_drop]amix=inputs=6:duration=first:dropout_transition=0[aout]\" "
    "-map \"[aout]\" -c:a aac -b:a 192k sfx_track.aac"
)
subprocess.check_call(audio_cmd, shell=True)

print("[*] Multiplexing audio and rendering final MP4...")
subprocess.check_call([
    "ffmpeg", "-y",
    "-i", raw_video,
    "-i", "sfx_track.aac",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-shortest",
    "friday_triage_100226.mp4"
])

if os.path.exists("sfx_track.aac"):
    os.remove("sfx_track.aac")

print("[✓] Reel successfully compiled: friday_triage_100226.mp4")
