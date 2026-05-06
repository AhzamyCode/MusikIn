"""Engine pencarian & ekstraksi metadata dari YouTube"""
import yt_dlp
from dataclasses import dataclass
from typing import List, Optional
from config import YTDL_OPTS


@dataclass
class Track:
    id: str
    title: str
    artist: str
    duration: int          # dalam detik
    duration_str: str      # format MM:SS
    thumbnail_url: str
    uploader: str
    upload_date: str
    url: str               # YouTube URL
    
    @property
    def display_title(self) -> str:
        return f"{self.title} — {self.artist}"


class SearchEngine:
    def __init__(self):
        self.ydl = yt_dlp.YoutubeDL(YTDL_OPTS)
    
    def search(self, query: str, max_results: int = 10) -> List[Track]:
        """
        Mencari lagu di YouTube berdasarkan keyword.
        Mengembalikan list of Track objects.
        """
        search_query = f"ytsearch{max_results}:{query}"
        
        try:
            result = self.ydl.extract_info(search_query, download=False)
            entries = result.get('entries', []) if result else []
            
            tracks = []
            for entry in entries:
                if not entry:
                    continue
                
                # Parse judul: biasanya "Artist - Title" atau "Title - Artist"
                title_raw = entry.get('title', 'Unknown Title')
                artist, title = self._parse_title(title_raw, entry.get('uploader', 'Unknown'))
                
                # Format durasi
                duration = entry.get('duration', 0) or 0
                duration_str = self._format_duration(duration)
                
                # Thumbnail high-res
                thumbnails = entry.get('thumbnails', [])
                thumbnail_url = self._get_best_thumbnail(thumbnails)
                
                track = Track(
                    id=entry.get('id', ''),
                    title=title,
                    artist=artist,
                    duration=duration,
                    duration_str=duration_str,
                    thumbnail_url=thumbnail_url,
                    uploader=entry.get('uploader', 'Unknown'),
                    upload_date=entry.get('upload_date', 'Unknown'),
                    url=entry.get('webpage_url', entry.get('url', ''))
                )
                tracks.append(track)
            
            return tracks
            
        except Exception as e:
            print(f"[Search Error] {e}")
            return []
    
    def get_stream_url(self, video_id: str) -> Optional[str]:
        """Mendapatkan direct audio stream URL dari video ID"""
        url = f"https://youtube.com/watch?v={video_id}"
        print(f"[SearchEngine] Extracting stream for video ID: {video_id}")
        print(f"[SearchEngine] YouTube URL: {url}")
        
        try:
            print(f"[SearchEngine] Calling yt_dlp.extract_info...")
            info = self.ydl.extract_info(url, download=False)
            print(f"[SearchEngine] yt_dlp extraction successful")
            
            formats = info.get('formats', [])
            print(f"[SearchEngine] Found {len(formats)} formats")
            
            # Prioritaskan audio-only format (lebih ringan)
            audio_formats = [
                f for f in formats 
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none'
            ]
            print(f"[SearchEngine] Found {len(audio_formats)} audio-only formats")
            
            if audio_formats:
                # Pilih yang bitrate paling tinggi
                best = max(audio_formats, key=lambda x: x.get('abr', 0) or 0)
                stream_url = best['url']
                print(f"[SearchEngine] Selected audio format: abr={best.get('abr', 'unknown')}, url={stream_url[:60]}...")
                return stream_url
            
            # Fallback: ambil format terbaik yang ada
            if formats:
                stream_url = formats[-1]['url']
                print(f"[SearchEngine] Using fallback format: url={stream_url[:60]}...")
                return stream_url
            else:
                print(f"[SearchEngine] No formats found")
                return None
            
        except Exception as e:
            print(f"[SearchEngine] Stream extraction failed: {e}")
            print(f"[SearchEngine] Exception type: {type(e).__name__}")
            return None
    
    def _parse_title(self, raw_title: str, uploader: str) -> tuple:
        """Parse judul mentah menjadi (artist, title)"""
        separators = [' - ', ' – ', ' — ', ' | ']
        
        for sep in separators:
            if sep in raw_title:
                parts = raw_title.split(sep, 1)
                # Heuristic: jika uploader mirip part pertama, itu artist
                if uploader.lower() in parts[0].lower() or len(parts[0]) < 40:
                    return parts[0].strip(), parts[1].strip()
                else:
                    return uploader, raw_title.strip()
        
        return uploader, raw_title.strip()
    
    def _format_duration(self, seconds: int) -> str:
        """Konversi detik ke MM:SS"""
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"
    
    def _get_best_thumbnail(self, thumbnails: list) -> str:
        """Ambil thumbnail resolusi tertinggi"""
        if not thumbnails:
            return ""
        
        # Cari yang resolusinya paling besar
        best = max(thumbnails, key=lambda x: (x.get('width', 0) or 0) * (x.get('height', 0) or 0))
        return best.get('url', thumbnails[-1].get('url', ''))


# Singleton instance
search_engine = SearchEngine()