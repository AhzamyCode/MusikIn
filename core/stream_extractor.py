"""Ekstraksi URL stream audio"""
from core.search_engine import search_engine


class StreamExtractor:
    """Wrapper untuk mendapatkan stream URL"""
    
    @staticmethod
    def get_audio_url(video_id: str) -> str | None:
        return search_engine.get_stream_url(video_id)