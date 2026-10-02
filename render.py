import subprocess
import sys
import os
import shutil
import base64

print("[*] Checking rendering dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])

from playwright.sync_api import sync_playwright

output_dir = "recordings"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)

# Encode product hero image for high-fidelity rendering
img_path = os.path.join("assets", "executive_ai_os.png")
if os.path.exists(img_path):
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        img_src = f"data:image/png;base64,{img_b64}"
    print("[*] Successfully loaded product hero image.")
else:
    print(f"[!] Note: {img_path} not detected. Falling back to default.")
    img_src = ""

with open("template.html", "r", encoding="utf-8") as f:
    html_content = f.read()

rendered_html = html_content.replace("__PRODUCT_IMAGE_SRC__", img_src)
temp_html = os.path.abspath("temp_rendered.html")
with open(temp_html, "w", encoding="utf-8") as f:
    f.write(rendered_html)

print("[*] Recording tactical 20-second dynamic reel...")
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
    context = browser.new_context(
        viewport={"width": 1080, "height": 1920},
        record_video_dir=output_dir,
        record_video_size={"width": 1080, "height": 1920}
    )
    page = context.new_page()
    page.goto(f"file://{temp_html}", wait_until="networkidle")

    # Full 20-second retention cycle
    page.wait_for_timeout(20000)

    context.close()
    browser.close()

if os.path.exists(temp_html):
    os.remove(temp_html)

recorded_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".webm")]
if not recorded_files:
    raise RuntimeError("Rendering error: No recording produced.")

raw_video = recorded_files[0]
print("[*] Transcoding to production MP4 via FFmpeg...")
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
