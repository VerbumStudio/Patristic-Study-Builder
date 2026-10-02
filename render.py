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

# Scan repository root and subfolders for the product image
print("[*] Scanning repository for image assets...")
found_path = None
target_names = ["executive_ai_os.png", "ai_prompt_library.png"]

for root, _, files in os.walk("."):
    for file in files:
        if file.lower() in [t.lower() for t in target_names]:
            found_path = os.path.join(root, file)
            break
    if found_path:
        break

img_src = ""
if found_path and os.path.exists(found_path):
    print(f"[✓] Successfully located asset: {found_path}")
    with open(found_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(found_path)[1].lower().replace(".", "")
        if ext == "jpg": 
            ext = "jpeg"
        img_src = f"data:image/{ext};base64,{b64}"
else:
    print(f"[!] Target graphic not found. Available files: {os.listdir('.')}")

with open("template.html", "r", encoding="utf-8") as f:
    html_content = f.read()

rendered_html = html_content.replace("__HERO_ASSET__", img_src)
temp_html = os.path.abspath("temp_rendered.html")
with open(temp_html, "w", encoding="utf-8") as f:
    f.write(rendered_html)

print("[*] Recording dynamic 18-second reel...")
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
    context = browser.new_context(
        viewport={"width": 1080, "height": 1920},
        record_video_dir=output_dir,
        record_video_size={"width": 1080, "height": 1920}
    )
    page = context.new_page()
    page.goto(f"file://{temp_html}", wait_until="networkidle")

    # Full 18-second sequence
    page.wait_for_timeout(18000)

    context.close()
    browser.close()

if os.path.exists(temp_html):
    os.remove(temp_html)

recorded_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".webm")]
if not recorded_files:
    raise RuntimeError("No recording produced.")

raw_video = recorded_files[0]
print("[*] Transcoding final MP4...")
subprocess.check_call([
    "ffmpeg", "-y",
    "-i", raw_video,
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-an",
    "friday_triage_100226.mp4"
])

print("[✓] Video successfully compiled: friday_triage_100226.mp4")
