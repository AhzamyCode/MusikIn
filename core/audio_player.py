"""Engine pemutaran audio menggunakan ffpyplayer (Real-time Streaming) atau pygame (fallback)"""
import threading
import time
import tempfile
import os
from typing import Callable, Optional, Any
from dataclasses import dataclass

try:
    from ffpyplayer.player import MediaPlayer
    HAS_FFPYPLAYER = True
    print("[AudioPlayer] ffpyplayer available - using real-time streaming")
except ImportError:
    MediaPlayer = Any  # Fallback type
    HAS_FFPYPLAYER = False
    print("[AudioPlayer] ffpyplayer not available - will use pygame fallback")

try:
    import pygame
    HAS_PYGAME = True
    print("[AudioPlayer] pygame available for fallback playback")
except (ImportError, RuntimeError) as e:
    HAS_PYGAME = False
    print(f"[AudioPlayer] pygame not available - no audio playback possible: {e}")


@dataclass
class PlayerState:
    is_playing: bool = False
    is_paused: bool = False
    current_position: float = 0.0  # detik
    duration: float = 0.0
    volume: float = 1.0


class AudioPlayer:
    def __init__(self):
        global HAS_PYGAME
        self._player: Optional[Any] = None
        self._pygame_mixer = None
        self._temp_file: Optional[str] = None
        self._state = PlayerState()
        self._position_thread: Optional[threading.Thread] = None
        self._stop_thread = threading.Event()
        self._current_stream_url: Optional[str] = None
        
        # Initialize pygame if available
        if HAS_PYGAME:
            try:
                pygame.mixer.init()
                print("[AudioPlayer] pygame mixer initialized")
            except Exception as e:
                print(f"[AudioPlayer] Failed to initialize pygame mixer: {e}")
                HAS_PYGAME = False
        
        # Callbacks
        self.on_position_update: Optional[Callable[[float], None]] = None
        self.on_track_end: Optional[Callable[[], None]] = None
        
        self.set_volume(1.0)
    
    def load_stream(self, stream_url: str, duration: float = 0) -> bool:
        """Load URL stream dengan ffpyplayer (streaming) atau pygame (download & play)"""
        print(f"[AudioPlayer] Loading stream: {stream_url[:60]}...")
        
        if HAS_FFPYPLAYER:
            return self._load_stream_ffpyplayer(stream_url, duration)
        elif HAS_PYGAME:
            return self._load_stream_pygame(stream_url, duration)
        else:
            print("[AudioPlayer] ERROR: Neither ffpyplayer nor pygame is available. Audio playback is unavailable.")
            return False
    
    def _load_stream_ffpyplayer(self, stream_url: str, duration: float = 0) -> bool:
        """Load URL stream dengan ffpyplayer (real-time streaming)"""
        print(f"[AudioPlayer] Using ffpyplayer for streaming")
        try:
            print(f"[AudioPlayer] Stopping current playback...")
            self.stop()
            self._current_stream_url = stream_url
            
            # ff_opts untuk audio-only streaming
            ff_opts = {
                'vn': True,           # No video
                'sn': True,           # No subtitles
                'nodisp': True,       # No display
                'paused': True,       # Start paused
                'volume': self._state.volume,
                'fflags': 'nobuffer', # Minimal buffering for streaming
                'flags': 'low_delay',
            }
            print(f"[AudioPlayer] ff_opts: {ff_opts}")
            
            print(f"[AudioPlayer] Creating MediaPlayer with ff_opts...")
            self._player = MediaPlayer(stream_url, ff_opts=ff_opts)
            print(f"[AudioPlayer] MediaPlayer created successfully")
            
            self._state.duration = duration
            self._state.current_position = 0
            
            print(f"[AudioPlayer] Stream loaded successfully: {stream_url[:60]}...")
            return True
            
        except Exception as e:
            print(f"[AudioPlayer] ERROR loading stream with ffpyplayer: {e}")
            print(f"[AudioPlayer] Exception type: {type(e).__name__}")
            import traceback
            print(f"[AudioPlayer] Full traceback:\n{traceback.format_exc()}")
            return False
    
    def _load_stream_pygame(self, stream_url: str, duration: float = 0) -> bool:
        """Load URL stream dengan pygame (download & play)"""
        print(f"[AudioPlayer] Using pygame fallback - downloading audio file")
        try:
            import requests
            
            print(f"[AudioPlayer] Stopping current playback...")
            self.stop()
            
            # Download audio file
            print(f"[AudioPlayer] Downloading audio from: {stream_url[:60]}...")
            response = requests.get(stream_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            self._temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            print(f"[AudioPlayer] Saving to temp file: {self._temp_file.name}")
            
            with open(self._temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"[AudioPlayer] Download complete, file size: {os.path.getsize(self._temp_file.name)} bytes")
            
            # Load with pygame
            print(f"[AudioPlayer] Loading with pygame mixer...")
            self._pygame_mixer = pygame.mixer.Sound(self._temp_file.name)
            self._current_stream_url = stream_url
            self._state.duration = duration
            self._state.current_position = 0
            
            print(f"[AudioPlayer] Audio loaded successfully with pygame")
            return True
            
        except Exception as e:
            print(f"[AudioPlayer] ERROR loading stream with pygame: {e}")
            print(f"[AudioPlayer] Exception type: {type(e).__name__}")
            import traceback
            print(f"[AudioPlayer] Full traceback:\n{traceback.format_exc()}")
            
            # Cleanup temp file if it exists
            if hasattr(self, '_temp_file') and self._temp_file:
                try:
                    os.unlink(self._temp_file.name)
                except:
                    pass
                self._temp_file = None
            
            return False
    
    def play(self):
        """Mulai/memutar audio"""
        print(f"[AudioPlayer] Play requested")
        if not self._state.is_playing:
            if self._player:  # ffpyplayer
                print(f"[AudioPlayer] Starting ffpyplayer playback")
                self._player.set_pause(False)
                self._state.is_playing = True
                self._state.is_paused = False
                self._start_position_tracker()
                print(f"[AudioPlayer] ffpyplayer playback started")
            elif self._pygame_mixer:  # pygame
                print(f"[AudioPlayer] Starting pygame playback")
                self._pygame_mixer.play()
                self._state.is_playing = True
                self._state.is_paused = False
                self._start_position_tracker()
                print(f"[AudioPlayer] pygame playback started")
            else:
                print(f"[AudioPlayer] Cannot play: no player available")
        else:
            print(f"[AudioPlayer] Already playing")
    
    def pause(self):
        """Pause audio"""
        print(f"[AudioPlayer] Pause requested")
        if self._state.is_playing and not self._state.is_paused:
            if self._player:  # ffpyplayer
                print(f"[AudioPlayer] Pausing ffpyplayer playback")
                self._player.set_pause(True)
                self._state.is_paused = True
                print(f"[AudioPlayer] ffpyplayer playback paused")
            elif self._pygame_mixer:  # pygame
                print(f"[AudioPlayer] Pausing pygame playback")
                pygame.mixer.pause()
                self._state.is_paused = True
                print(f"[AudioPlayer] pygame playback paused")
            else:
                print(f"[AudioPlayer] Cannot pause: no player available")
        else:
            print(f"[AudioPlayer] Cannot pause: is_playing={self._state.is_playing}, is_paused={self._state.is_paused}")
    
    def resume(self):
        """Resume dari pause"""
        print(f"[AudioPlayer] Resume requested")
        if self._state.is_paused:
            if self._player:  # ffpyplayer
                print(f"[AudioPlayer] Resuming ffpyplayer playback")
                self._player.set_pause(False)
                self._state.is_paused = False
                print(f"[AudioPlayer] ffpyplayer playback resumed")
            elif self._pygame_mixer:  # pygame
                print(f"[AudioPlayer] Resuming pygame playback")
                pygame.mixer.unpause()
                self._state.is_paused = False
                print(f"[AudioPlayer] pygame playback resumed")
            else:
                print(f"[AudioPlayer] Cannot resume: no player available")
        else:
            print(f"[AudioPlayer] Cannot resume: is_paused={self._state.is_paused}")
    
    def stop(self):
        """Hentikan pemutaran"""
        print(f"[AudioPlayer] Stop requested")
        self._stop_thread.set()
        
        if self._player:  # ffpyplayer
            print(f"[AudioPlayer] Closing ffpyplayer")
            self._player.set_pause(True)
            self._player.close_player()
            self._player = None
        elif self._pygame_mixer:  # pygame
            print(f"[AudioPlayer] Stopping pygame")
            self._pygame_mixer.stop()
            self._pygame_mixer = None
            
            # Cleanup temp file
            if self._temp_file:
                try:
                    os.unlink(self._temp_file.name)
                    print(f"[AudioPlayer] Cleaned up temp file: {self._temp_file.name}")
                except Exception as e:
                    print(f"[AudioPlayer] Failed to cleanup temp file: {e}")
                self._temp_file = None
        
        self._state.is_playing = False
        self._state.is_paused = False
        self._state.current_position = 0
        self._stop_thread.clear()
        print(f"[AudioPlayer] Playback stopped")
    
    def seek(self, position: float):
        """Lompat ke posisi tertentu (detik)"""
        print(f"[AudioPlayer] Seek requested to {position:.1f}s")
        if self._state.is_playing:
            if self._player:  # ffpyplayer
                try:
                    print(f"[AudioPlayer] Seeking ffpyplayer to {int(position * 1000)}ms")
                    self._player.seek(int(position * 1000), relative=False)
                    self._state.current_position = position
                    print(f"[AudioPlayer] ffpyplayer seek completed")
                except Exception as e:
                    print(f"[AudioPlayer] ffpyplayer seek failed: {e}")
            elif self._pygame_mixer:  # pygame
                # pygame doesn't support seeking, just update position
                print(f"[AudioPlayer] pygame doesn't support seeking, updating position only")
                self._state.current_position = position
            else:
                print(f"[AudioPlayer] Cannot seek: no player available")
        else:
            print(f"[AudioPlayer] Cannot seek: not playing")
    
    def set_volume(self, volume: float):
        """Set volume 0.0 - 1.0"""
        print(f"[AudioPlayer] Volume set to {volume}")
        self._state.volume = max(0.0, min(1.0, volume))
        if self._player:  # ffpyplayer
            self._player.set_volume(self._state.volume)
        elif self._pygame_mixer:  # pygame
            self._pygame_mixer.set_volume(self._state.volume)
    
    def toggle_play_pause(self) -> bool:
        """Toggle antara play dan pause"""
        print(f"[AudioPlayer] Toggle play/pause requested")
        if self._state.is_paused:
            self.resume()
        elif self._state.is_playing:
            self.pause()
        else:
            self.play()
        is_now_playing = self._state.is_playing and not self._state.is_paused
        print(f"[AudioPlayer] Toggle result: playing={is_now_playing}")
        return is_now_playing
    
    def _start_position_tracker(self):
        """Thread untuk tracking posisi pemutaran"""
        print(f"[AudioPlayer] Starting position tracker thread")
        def track():
            print(f"[AudioPlayer] Position tracker thread started")
            # Tunggu player siap
            time.sleep(0.5)
            
            while not self._stop_thread.is_set() and self._state.is_playing:
                if not self._state.is_paused and self._player:
                    # Get current position from ffpyplayer
                    pts = self._player.get_pts()
                    if pts is not None and pts > 0:
                        self._state.current_position = pts
                        
                        if self.on_position_update:
                            self.on_position_update(self._state.current_position)
                        
                        # Cek jika track selesai
                        if self._state.duration > 0 and self._state.current_position >= self._state.duration - 1:
                            print(f"[AudioPlayer] Track ended at {self._state.current_position:.1f}s")
                            self.on_track_end() if self.on_track_end else None
                            break
                
                time.sleep(0.5)
            
            print(f"[AudioPlayer] Position tracker thread ended")
        
        self._position_thread = threading.Thread(target=track, daemon=True)
        self._position_thread.start()
        print(f"[AudioPlayer] Position tracker thread launched")
    
    @property
    def state(self) -> PlayerState:
        return self._state


# Singleton
audio_player = AudioPlayer()