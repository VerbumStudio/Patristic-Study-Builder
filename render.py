import subprocess
import sys
import os
import shutil

print("[*] Installing rendering dependencies...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", 
    "playwright"
])
subprocess.check_call([
    sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"
])

from playwright.sync_api import sync_playwright

output_dir = "recordings"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)

print("[*] Launching Chromium screen recorder...")
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
    context = browser.new_context(
        viewport={"width": 1080, "height": 1920},
        record_video_dir=output_dir,
        record_video_size={"width": 1080, "height": 1920}
    )
    page = context.new_page()

    file_path = os.path.abspath("template.html")
    page.goto(f"file://{file_path}", wait_until="networkidle")

    # Record 8 seconds of active animation
    print("[*] Recording dynamic scene...")
    page.wait_for_timeout(8000)

    context.close()
    browser.close()

# Locate recorded webm
recorded_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".webm")]
if not recorded_files:
    raise RuntimeError("Recording failed: no video file produced.")

raw_video = recorded_files[0]
print(f"[*] Raw recording ready: {raw_video}")

# Convert webm to final standard production MP4
print("[*] Encoding friday_triage_100226.mp4 via FFmpeg...")
subprocess.check_call([
    "ffmpeg", "-y",
    "-i", raw_video,
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "friday_triage_100226.mp4"
])

print("[✓] High-production video successfully generated: friday_triage_100226.mp4")
