"""Fetcher lirik dari berbagai provider"""
import requests
import re
import time
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class LyricLine:
    time: float  # dalam detik
    text: str


class LyricsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        })
    
    def fetch_synced(self, title: str, artist: str, duration: int = 0) -> List[LyricLine]:
        """
        Ambil lirik sinkron (LRC format) dari Lrclib API.
        Return list of LyricLine, kosong jika tidak ditemukan.
        """
        try:
            # Lrclib API
            url = "https://lrclib.net/api/search"
            params = {
                'track_name': title,
                'artist_name': artist,
                'duration': duration if duration > 0 else None
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return []
            
            # Ambil hasil pertama yang punya syncedLyrics
            for result in data:
                synced = result.get('syncedLyrics')
                if synced:
                    return self._parse_lrc(synced)
            
            # Fallback: ambil plain lyrics
            for result in data:
                plain = result.get('plainLyrics', '')
                if plain:
                    return [LyricLine(time=0.0, text=line) for line in plain.split('\n') if line.strip()]
            
            return []
            
        except Exception as e:
            print(f"[Lyrics Fetch Error] {e}")
            return []
    
    def fetch_plain(self, title: str, artist: str) -> str:
        """Ambil lirik plain text sebagai fallback"""
        try:
            url = "https://lrclib.net/api/search"
            params = {'track_name': title, 'artist_name': artist}
            
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if data and data[0].get('plainLyrics'):
                return data[0]['plainLyrics']
            
            return "Lirik tidak tersedia."
            
        except Exception as e:
            return f"Gagal memuat lirik: {e}"
    
    def _parse_lrc(self, lrc_text: str) -> List[LyricLine]:
        """Parse format LRC ke list LyricLine"""
        lines = []
        pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
        
        for line in lrc_text.strip().split('\n'):
            match = re.match(pattern, line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                millis = int(match.group(3).ljust(3, '0')[:3])
                text = match.group(4).strip()
                
                total_seconds = minutes * 60 + seconds + millis / 1000
                lines.append(LyricLine(time=total_seconds, text=text))
        
        return lines
    
    def get_current_line(self, lyrics: List[LyricLine], position: float) -> Tuple[int, str]:
        """
        Dapatkan baris lirik yang sedang aktif berdasarkan posisi waktu.
        Return (index, text)
        """
        if not lyrics:
            return -1, ""
        
        current_idx = 0
        for i, line in enumerate(lyrics):
            if line.time <= position:
                current_idx = i
            else:
                break
        
        return current_idx, lyrics[current_idx].text if current_idx < len(lyrics) else ""


# Singleton
lyrics_fetcher = LyricsFetcher()