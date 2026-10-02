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

# Scan repository for target images
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

print("[*] Recording fast-paced 15-second reel...")
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

    # 15.0-second timeline
    page.wait_for_timeout(15000)

    context.close()
    browser.close()

if os.path.exists(temp_html):
    os.remove(temp_html)

recorded_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".webm")]
if not recorded_files:
    raise RuntimeError("No recording produced.")

raw_video = recorded_files[0]
print("[*] Generating high-impact psychological SFX audio track...")

# Procedural SFX:
# 1. Opening urgent chime (0.1s)
# 2. Snappy mechanical keyboard clicks (2.8s - 5.2s)
# 3. Confirmation lock chime (5.5s)
# 4. Heavy sub-bass hits for Option A & Option B (5.8s, 7.0s)
# 5. Low-end bass drop for Payoff (10.5s)
sfx_command = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo:d=15",
    "-f", "lavfi", "-i", "sine=f=1174:d=0.22,volume=3.5",               # Alert chime
    "-f", "lavfi", "-i", "anoisesrc=d=2.4:c=white:r=44100,volume=3.2,bandpass=f=3200:w=1200", # Mechanical keys
    "-f", "lavfi", "-i", "sine=f=880:d=0.18,volume=3.0",                # Lock chime
    "-f", "lavfi", "-i", "sine=f=75:d=0.55,volume=4.5",                 # Sub-bass hit 1
    "-f", "lavfi", "-i", "sine=f=85:d=0.55,volume=4.5",                 # Sub-bass hit 2
    "-f", "lavfi", "-i", "sine=f=60:d=0.9,volume=5.5",                  # Heavy payoff sub-drop
    "-filter_complex",
    "[1]adelay=100|100[s0];"
    "[2]adelay=2800|2800[s1];"
    "[3]adelay=5500|5500[s2];"
    "[4]adelay=5800|5800[s3];"
    "[5]adelay=7000|7000[s4];"
    "[6]adelay=10500|10500[s5];"
    "[0][s0][s1][s2][s3][s4][s5]amix=inputs=7:duration=first:dropout_transition=0[aout]",
    "-map", "[aout]",
    "-c:a", "aac",
    "-b:a", "256k",
    "master_sfx.aac"
]
subprocess.check_call(sfx_command)

print("[*] Multiplexing video and audio tracks...")
subprocess.check_call([
    "ffmpeg", "-y",
    "-i", raw_video,
    "-i", "master_sfx.aac",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-shortest",
    "friday_triage_100226.mp4"
])

if os.path.exists("master_sfx.aac"):
    os.remove("master_sfx.aac")

print("[✓] Video successfully compiled: friday_triage_100226.mp4")
