import subprocess
import sys
import os

print("[*] Installing rendering dependencies...")
subprocess.check_call([
    sys.executable, "-m", "pip", "install", 
    "playwright", "moviepy<2.0.0", "imageio-ffmpeg"
])
subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

from playwright.sync_api import sync_playwright
from moviepy.editor import ImageClip

print("[*] Capturing high-resolution DOM snapshot...")
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
    page = browser.new_page(viewport={"width": 1080, "height": 1920})
    
    file_path = os.path.abspath("template.html")
    page.goto(f"file://{file_path}", wait_until="networkidle")
    
    page.screenshot(path="frame.png")
    browser.close()

print("[*] Compiling MP4 reel...")
clip = ImageClip("frame.png").set_duration(15)
clip.write_videofile(
    "output_reel.mp4",
    fps=24,
    codec="libx264",
    audio_codec="aac"
)

print("[✓] High-production video successfully generated: output_reel.mp4")
