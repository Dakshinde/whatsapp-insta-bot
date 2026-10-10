import io
import logging
import os
import re
import tempfile
import threading
from pathlib import Path
import yt_dlp
from flask import Flask, send_file
from neonize import extract_text
from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, QREv
import qrcode

# ---------------- CONFIGURATION ----------------
SESSION_FILE = "whatsapp_session.db"
MAX_VIDEO_SIZE = 16 * 1024 * 1024  # 16 MiB safety limit
MAX_HEIGHT = 360

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

client = NewClient(SESSION_FILE)
INSTAGRAM_URL_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[A-Za-z0-9_-]+/?", re.IGNORECASE)

# Global variable to hold the latest QR code bytes for web display
latest_qr_image = None

# ---------------- FLASK WEB SERVER & QR ROUTE ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "WhatsApp Bot is running! Go to <a href='/qr'>/qr</a> to scan the login code if needed."

@app.route("/qr")
def show_qr():
    global latest_qr_image
    if latest_qr_image is None:
        return "No QR code needed right now (either already connected or waiting for event)."
    return send_file(io.BytesIO(latest_qr_image), mimetype='image/png')

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- QR CODE CAPTURE ----------------
@client.event(QREv)
def on_qr(client: NewClient, event: QREv) -> None:
    global latest_qr_image
    qr_data = event.QR.decode("utf-8") if isinstance(event.QR, bytes) else str(event.QR)
    
    # Generate QR code as a PNG image in memory
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    latest_qr_image = buf.getvalue()
    logger.info("New QR code generated and available at /qr endpoint.")

# ---------------- VIDEO DOWNLOADER ----------------
def download_video(url: str, output_dir: Path) -> Path:
    output_template = str(output_dir / "video.%(ext)s")
    options = {
        "format": f"best[height<={MAX_HEIGHT}][ext=mp4]/best[height<={MAX_HEIGHT}]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "max_filesize": MAX_VIDEO_SIZE,
        "socket_timeout": 20,
        "retries": 2,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        downloaded_path = Path(downloader.prepare_filename(info))

    if not downloaded_path.exists():
        candidates = [p for p in output_dir.glob("video.*") if p.is_file()]
        if not candidates:
            raise FileNotFoundError("The downloader finished without producing a video file.")
        downloaded_path = candidates[0]

    if downloaded_path.stat().st_size > MAX_VIDEO_SIZE:
        downloaded_path.unlink(missing_ok=True)
        raise ValueError("The video exceeds the configured size limit.")

    return downloaded_path

# ---------------- WHATSAPP EVENT HANDLERS ----------------
@client.event(ConnectedEv)
def on_connected(client: NewClient, event: ConnectedEv) -> None:
    logger.info("Connected to WhatsApp.")

@client.event(MessageEv)
def on_message(client: NewClient, event: MessageEv) -> None:
    if event.Info.MessageSource.IsFromMe:
        return
    text = extract_text(event.Message)
    if not text:
        return
    match = INSTAGRAM_URL_RE.search(text)
    if not match:
        return

    url = match.group(0)
    chat = event.Info.MessageSource.Chat
    logger.info("Received an Instagram video link.")

    with tempfile.TemporaryDirectory(prefix="ig_video_") as temp:
        temp_dir = Path(temp)
        try:
            client.send_message(chat, "⏳ Processing your video...")
            video_path = download_video(url, temp_dir)
            client.send_video(chat, str(video_path), caption="Here is your video! 🎥", quoted=event)
            logger.info("Video sent successfully.")
        except Exception as exc:
            logger.warning("Video processing failed: %s", type(exc).__name__)
            try:
                client.send_message(chat, "❌ Couldn't process this video.")
            except Exception:
                logger.exception("Failed to send error message.")

# ---------------- START BOT & WEB SERVER ----------------
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    logger.info("Starting WhatsApp video bot on Render.")
    try:
        client.connect()
    except KeyboardInterrupt:
        logger.info("Stopping bot.")
        client.stop()