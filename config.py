"""Konfigurasi global MusikIn"""
import os

# === PATH ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# === UI ===
APP_NAME = "MusikIn"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
MINI_WIDTH = 400
MINI_HEIGHT = 180

# === THEME (Dark Mode) ===
COLORS = {
    "bg_primary": "#0D0D0D",      # Background utama
    "bg_secondary": "#1A1A1A",    # Card/Panel
    "bg_tertiary": "#262626",     # Hover state
    "accent": "#1DB954",          # Spotify-green accent
    "accent_hover": "#1ED760",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B3B3B3",
    "text_disabled": "#535353",
    "error": "#E22134",
}

# === AUDIO ===
AUDIO_BUFFER = 2048
DEFAULT_VOLUME = 0.7

# === LYRIC PROVIDER ===
LYRIC_PROVIDERS = ["lrclib", "musixmatch", "genius"]

# === YT-DLP ===
YTDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'cookiefile': None,  # Set path ke cookies.txt jika perlu bypass limit
}