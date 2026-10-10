# WhatsApp Instagram Downloader Bot

A simple Python bot that downloads Instagram videos using `yt-dlp` and sends them back through WhatsApp using `neonize`.

## Features

- Download Instagram posts and Reels.
- Select videos up to 360p.
- Limit file size to 16 MiB.
- Automatically delete temporary files.
- Run locally on your computer.

## Tech Stack

- Python 3.10+
- [Neonize](https://github.com/krypton-byte/neonize)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- FFmpeg

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/whatsapp-insta-bot.git
cd whatsapp-insta-bot
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install FFmpeg:

```bash
sudo apt install ffmpeg
```

## Usage

Run the bot:

```bash
python bot.py
```

1. Link your WhatsApp account by following the pairing instructions.
2. Send an Instagram video link to the linked account to try the bot.

## Project Structure

```text
whatsapp-insta-bot/
├── bot.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Notes

- Keep `whatsapp_session.db` private. Never upload it to GitHub.
- This project uses an unofficial WhatsApp client.
- Only download content you own or have permission to download.