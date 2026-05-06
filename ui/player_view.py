"""View Now Playing - Async"""
import flet as ft
import requests
import asyncio
from io import BytesIO
from PIL import Image
from config import COLORS
from ui.components import PlayerControls, LyricsDisplay
from core.audio_player import audio_player
from core.lyrics_fetcher import lyrics_fetcher
from core.stream_extractor import StreamExtractor


class PlayerView(ft.View):
    def __init__(self, on_back):
        self.on_back = on_back
        self.current_track = None
        self.lyrics = []
        
        self.album_art = ft.Container(
            content=ft.Image(
                src="",
                width=350,
                height=350,
                border_radius=20,
                fit="cover",
            ),
            bgcolor=COLORS["bg_secondary"],
            border_radius=20,
        )
        
        self.track_title = ft.Text(
            size=24,
            weight=ft.FontWeight.BOLD,
            color=COLORS["text_primary"],
            text_align=ft.TextAlign.CENTER,
        )
        self.track_artist = ft.Text(
            size=16,
            color=COLORS["text_secondary"],
            text_align=ft.TextAlign.CENTER,
        )
        
        self.lyrics_display = LyricsDisplay(expand=True)
        
        self.player_controls = PlayerControls(
            audio_player,
            on_seek=self._on_seek,
        )
        
        self.back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=COLORS["text_primary"],
            on_click=lambda e: self._handle_back(),
        )
        
        super().__init__(
            route="/player",
            bgcolor=COLORS["bg_primary"],
            padding=0,
            controls=[
                ft.Column(
                    [
                        ft.Container(
                            content=self.back_btn,
                            padding=20,
                        ),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        self.album_art,
                                        ft.Container(height=20),
                                        self.track_title,
                                        self.track_artist,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    expand=2,
                                ),
                                ft.Container(
                                    content=self.lyrics_display,
                                    expand=3,
                                    margin=ft.margin.only(right=30),
                                ),
                            ],
                            expand=True,
                            spacing=30,
                        ),
                        self.player_controls,
                    ],
                    expand=True,
                )
            ],
        )
    
    async def load_track(self, track):
        """Load dan mulai memutar track secara async"""
        print(f"[PlayerView] Loading track: {track.title} by {track.artist}")
        self.current_track = track
        
        self.track_title.value = track.title
        self.track_artist.value = track.artist
        print(f"[PlayerView] UI text updated for track")
        
        # Store thumbnail URL for later loading (after navigation)
        self.pending_thumbnail_url = track.thumbnail_url
        print(f"[PlayerView] Stored thumbnail URL for later loading: {track.thumbnail_url}")
        
        # Fetch stream URL
        print(f"[PlayerView] Extracting stream URL for video ID: {track.id}")
        try:
            stream_url = StreamExtractor.get_audio_url(track.id)
            print(f"[PlayerView] StreamExtractor returned: {stream_url}")
            if not stream_url:
                error_msg = "Tidak dapat memuat stream - StreamExtractor returned None"
                print(f"[PlayerView] ERROR: {error_msg}")
                self.track_title.value = f"Error: {error_msg}"
                return
        except Exception as e:
            error_msg = f"Tidak dapat memuat stream - Exception: {e}"
            print(f"[PlayerView] ERROR: {error_msg}")
            self.track_title.value = f"Error: {error_msg}"
            return
        
        print(f"[PlayerView] Stream URL obtained: {stream_url[:60]}...")
        
        # Load audio stream (sync)
        print(f"[PlayerView] Loading audio stream...")
        try:
            success = audio_player.load_stream(stream_url, track.duration)
            print(f"[PlayerView] Audio load result: {success}")
            if not success:
                error_msg = "Tidak dapat memuat audio - load_stream failed"
                print(f"[PlayerView] ERROR: {error_msg}")
                self.track_title.value = f"Error: {error_msg}"
                return
        except Exception as e:
            error_msg = f"Tidak dapat memuat audio - Exception: {e}"
            print(f"[PlayerView] ERROR: {error_msg}")
            self.track_title.value = f"Error: {error_msg}"
            return
        
        print(f"[PlayerView] Audio stream loaded successfully")
        
        # Fetch lyrics (async)
        print(f"[PlayerView] Fetching lyrics...")
        self.lyrics = await self._fetch_lyrics(track.title, track.artist, track.duration)
        
        if self.lyrics:
            print(f"[PlayerView] Synced lyrics found: {len(self.lyrics)} lines")
            self.lyrics_display.set_lyrics(self.lyrics)
        else:
            print(f"[PlayerView] No synced lyrics, fetching plain lyrics...")
            plain = lyrics_fetcher.fetch_plain(track.title, track.artist)
            print(f"[PlayerView] Plain lyrics: {len(plain.split('\n'))} lines")
            self.lyrics_display.set_lyrics([
                type('obj', (object,), {'text': line, 'time': 0}) 
                for line in plain.split('\n')
            ])
        
        # Setup callbacks
        print(f"[PlayerView] Setting up audio callbacks")
        audio_player.on_position_update = self._on_position_update
        audio_player.on_track_end = self._on_track_end
        
        # Play
        print(f"[PlayerView] Starting playback")
        audio_player.play()
        # Don't update controls here - will be done after navigation
    
    def refresh_ui(self):
        """Refresh UI setelah view ditambahkan ke page"""
        print(f"[PlayerView] Refreshing UI after navigation")
        print(f"[PlayerView] Page available: {self.page is not None}")
        try:
            print(f"[PlayerView] Setting play state to True")
            self.player_controls.set_playing_state(True)
            print(f"[PlayerView] Calling self.update()")
            self.update()
            print(f"[PlayerView] UI refresh successful")
            
            # Load pending thumbnail now that we're on the page
            self._load_pending_thumbnail()
            
        except RuntimeError as e:
            print(f"[PlayerView] UI refresh failed (expected if not on page): {e}")
            pass  # View belum di page
        except Exception as e:
            print(f"[PlayerView] UI refresh failed with unexpected error: {e}")
            import traceback
            print(f"[PlayerView] UI refresh traceback:\n{traceback.format_exc()}")
    
    def _load_pending_thumbnail(self):
        """Load thumbnail setelah view ditambahkan ke page"""
        if hasattr(self, 'pending_thumbnail_url') and self.pending_thumbnail_url:
            print(f"[PlayerView] Loading pending thumbnail: {self.pending_thumbnail_url}")
            # Load thumbnail asynchronously tanpa blocking
            asyncio.create_task(self._load_thumbnail(self.pending_thumbnail_url))
            # Clear the pending URL so we don't load it again
            self.pending_thumbnail_url = None
    
    async def _load_thumbnail(self, url: str):
        """Load thumbnail secara async"""
        print(f"[PlayerView] Starting thumbnail download from: {url}")
        try:
            print(f"[PlayerView] Making HTTP request to thumbnail URL...")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, timeout=10)
            )
            print(f"[PlayerView] HTTP response status: {response.status_code}")
            print(f"[PlayerView] Response content length: {len(response.content)} bytes")
            
            if response.status_code != 200:
                print(f"[PlayerView] ERROR: HTTP {response.status_code} for thumbnail")
                raise Exception(f"HTTP {response.status_code}")
            
            print(f"[PlayerView] Processing image...")
            img = Image.open(BytesIO(response.content))
            print(f"[PlayerView] Original image size: {img.size}, format: {img.format}")
            
            img = img.resize((400, 400), Image.LANCZOS)
            print(f"[PlayerView] Resized image to: {img.size}")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            print(f"[PlayerView] Encoded image to PNG, size: {len(buffer.getvalue())} bytes")
            
            import base64
            b64 = base64.b64encode(buffer.getvalue()).decode()
            print(f"[PlayerView] Base64 encoded, length: {len(b64)} chars")
            
            self.album_art.content.src_base64 = b64
            print(f"[PlayerView] Set album art src_base64")
            
            if self.page:
                print(f"[PlayerView] Updating album art UI...")
                self.album_art.content.update()
                print(f"[PlayerView] Album art UI updated successfully")
            else:
                print(f"[PlayerView] Page not available, skipping UI update")
            
        except Exception as e:
            print(f"[PlayerView] Thumbnail loading failed: {e}")
            print(f"[PlayerView] Exception type: {type(e).__name__}")
            # Set default thumbnail
            print(f"[PlayerView] Setting fallback thumbnail...")
            self.album_art.content.src = ""  # Clear any existing image
            try:
                if self.page:
                    self.album_art.content.update()
                    print(f"[PlayerView] Fallback thumbnail set successfully")
                else:
                    print(f"[PlayerView] Page not available for fallback update")
            except RuntimeError as re:
                print(f"[PlayerView] Fallback update failed (expected): {re}")
                pass
    
    async def _fetch_lyrics(self, title: str, artist: str, duration: int):
        """Fetch lyrics secara async"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lyrics_fetcher.fetch_synced,
            title, artist, duration
        )
    
    def _on_position_update(self, position: float):
        """Callback posisi audio"""
        print(f"[PlayerView] Position update: {position:.1f}s")
        try:
            if self.page:
                self._update_ui_position(position)
        except RuntimeError as e:
            print(f"[PlayerView] Position update failed (not on page): {e}")
            pass  # View belum di page
    
    def _update_ui_position(self, position: float):
        """Update UI"""
        if self.current_track:
            print(f"[PlayerView] Updating UI position: {position:.1f}s / {self.current_track.duration:.1f}s")
            self.player_controls.update_progress(position, self.current_track.duration)
            if self.lyrics:
                idx, _ = lyrics_fetcher.get_current_line(self.lyrics, position)
                print(f"[PlayerView] Highlighting lyrics line: {idx}")
                self.lyrics_display.highlight_line(idx)
    
    def _on_seek(self, position_str: str):
        """Seek"""
        try:
            position = float(position_str)
            audio_player.seek(position)
        except ValueError:
            pass
    
    def _on_track_end(self):
        """Callback ketika track selesai"""
        print(f"[PlayerView] Track ended")
        try:
            if self.page:
                print(f"[PlayerView] Updating UI for track end")
                self.player_controls.set_playing_state(False)
                # Reset position to beginning
                self._update_ui_position(0)
        except RuntimeError as e:
            print(f"[PlayerView] Track end update failed (not on page): {e}")
            pass  # View belum di page
    
    def _handle_back(self):
        """Handle back button click"""
        print(f"[PlayerView] Back button clicked")
        if self.page:
            self.page.run_task(self.on_back)
        else:
            print(f"[PlayerView] Cannot go back - no page reference")