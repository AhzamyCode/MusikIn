"""Reusable UI components"""
import flet as ft
from config import COLORS


class SearchBar(ft.Container):
    """Custom search bar"""
    def __init__(self, on_submit, **kwargs):
        self.text_field = ft.TextField(
            hint_text="Cari lagu, artis, atau album...",
            hint_style=ft.TextStyle(color=COLORS["text_disabled"]),
            text_style=ft.TextStyle(color=COLORS["text_primary"], size=14),
            border=ft.InputBorder.NONE,
            expand=True,
            on_submit=on_submit,
            autofocus=True,
        )
        
        super().__init__(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SEARCH, color=COLORS["text_secondary"]),  # <-- ft.Icons.SEARCH
                    self.text_field,
                ],
                spacing=10,
            ),
            bgcolor=COLORS["bg_secondary"],
            border_radius=25,
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border=ft.border.all(1, COLORS["bg_tertiary"]),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            **kwargs
        )
    
    @property
    def value(self) -> str:
        return self.text_field.value or ""
    
    def clear(self):
        self.text_field.value = ""
        self.text_field.update()


class TrackCard(ft.Container):
    """Card untuk menampilkan hasil pencarian"""
    def __init__(self, track, on_click, **kwargs):
        self.track = track
        
        thumbnail = ft.Image(
            src=track.thumbnail_url,
            width=60,
            height=60,
            border_radius=8,
            fit="cover",
            error_content=ft.Container(
                width=60, height=60, bgcolor=COLORS["bg_tertiary"],
                border_radius=8
            )
        )
        
        content = ft.Row(
            [
                thumbnail,
                ft.Column(
                    [
                        ft.Text(
                            track.title,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=COLORS["text_primary"],
                            no_wrap=True,
                            width=250
                        ),
                        ft.Text(
                            f"{track.artist} • {track.duration_str}",
                            size=12,
                            color=COLORS["text_secondary"],
                            no_wrap=True
                        ),
                    ],
                    spacing=4,
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Icon(
                    ft.Icons.PLAY_CIRCLE_FILLED,  # <-- ft.Icons.PLAY_CIRCLE_FILLED
                    color=COLORS["accent"],
                    size=32,
                    opacity=0,
                    animate_opacity=200,
                ),
            ],
            spacing=15,
        )
        
        super().__init__(
            content=content,
            padding=10,
            border_radius=10,
            bgcolor=COLORS["bg_primary"],
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=lambda e: on_click(track),
            on_hover=self._on_hover,
            **kwargs
        )
    
    def _on_hover(self, e: ft.HoverEvent):
        self.bgcolor = COLORS["bg_secondary"] if e.data == "true" else COLORS["bg_primary"]
        play_icon = self.content.controls[-1]
        play_icon.opacity = 1 if e.data == "true" else 0
        self.update()


class PlayerControls(ft.Container):
    """Kontrol pemutar (play, pause, next, prev, seek, volume)"""
    def __init__(self, player, on_seek, **kwargs):
        self.player = player
        self.on_seek = on_seek
        
        self.play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_FILLED,  # <-- ft.Icons.PLAY_CIRCLE_FILLED
            icon_size=48,
            icon_color=COLORS["text_primary"],
            on_click=self._toggle_play,
        )
        
        self.progress_slider = ft.Slider(
            min=0, max=100, value=0,
            active_color=COLORS["accent"],
            inactive_color=COLORS["bg_tertiary"],
            thumb_color=COLORS["text_primary"],
            on_change_end=lambda e: on_seek(e.data),
            expand=True,
        )
        
        self.current_time = ft.Text("0:00", size=12, color=COLORS["text_secondary"])
        self.total_time = ft.Text("0:00", size=12, color=COLORS["text_secondary"])
        
        self.volume_slider = ft.Slider(
            min=0, max=1, value=0.7,
            active_color=COLORS["accent"],
            inactive_color=COLORS["bg_tertiary"],
            width=100,
            on_change=lambda e: player.set_volume(float(e.data)),
        )
        
        super().__init__(
            content=ft.Column(
                [
                    ft.Row(
                        [self.current_time, self.progress_slider, self.total_time],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.SKIP_PREVIOUS,  # <-- ft.Icons.SKIP_PREVIOUS
                                icon_color=COLORS["text_primary"],
                            ),
                            self.play_btn,
                            ft.IconButton(
                                icon=ft.Icons.SKIP_NEXT,  # <-- ft.Icons.SKIP_NEXT
                                icon_color=COLORS["text_primary"],
                            ),
                            ft.Container(expand=True),
                            ft.Icon(ft.Icons.VOLUME_UP, color=COLORS["text_secondary"], size=20),  # <-- ft.Icons.VOLUME_UP
                            self.volume_slider,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=5,
            ),
            padding=20,
            **kwargs
        )
    
    def _toggle_play(self, e):
        is_playing = self.player.toggle_play_pause()
        self.play_btn.icon = (
            ft.Icons.PAUSE_CIRCLE_FILLED if is_playing   # <-- ft.Icons.PAUSE_CIRCLE_FILLED
            else ft.Icons.PLAY_CIRCLE_FILLED
        )
        self.play_btn.update()
    
    def update_progress(self, current: float, total: float):
        if total > 0:
            self.progress_slider.max = total
            self.progress_slider.value = min(current, total)
            self.current_time.value = self._format_time(current)
            self.total_time.value = self._format_time(total)
            self.progress_slider.update()
            self.current_time.update()
            self.total_time.update()
    
    def set_playing_state(self, is_playing: bool):
        self.play_btn.icon = (
            ft.Icons.PAUSE_CIRCLE_FILLED if is_playing   # <-- ft.Icons.PAUSE_CIRCLE_FILLED
            else ft.Icons.PLAY_CIRCLE_FILLED
        )
        self.play_btn.update()
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        return f"{m}:{s:02d}"


class LyricsDisplay(ft.Container):
    """Komponen tampilan lirik"""
    def __init__(self, **kwargs):
        self.lyrics_list = ft.ListView(
            expand=True,
            spacing=20,
            padding=ft.padding.symmetric(vertical=50),
        )
        
        super().__init__(
            content=self.lyrics_list,
            bgcolor=COLORS["bg_primary"],
            border_radius=15,
            padding=20,
            **kwargs
        )
    
    def set_lyrics(self, lyrics: list):
        self.lyrics_list.controls.clear()
        
        for line in lyrics:
            self.lyrics_list.controls.append(
                ft.Text(
                    line.text,
                    size=16,
                    color=COLORS["text_secondary"],
                    text_align=ft.TextAlign.CENTER,
                    animate_opacity=200,
                )
            )
        try:
            self.update()
        except RuntimeError:
            pass
    
    def highlight_line(self, index: int):
        for i, control in enumerate(self.lyrics_list.controls):
            if i == index:
                control.color = COLORS["accent"]
                control.size = 20
                control.weight = ft.FontWeight.BOLD
            else:
                control.color = COLORS["text_secondary"]
                control.size = 16
                control.weight = ft.FontWeight.NORMAL
        
        if 0 <= index < len(self.lyrics_list.controls):
            # Scroll to the highlighted line
            try:
                # Try offset parameter (Flet scroll_to method)
                offset = index * 60  # Rough estimate: 60 pixels per line
                self.lyrics_list.scroll_to(offset=offset, duration=500)
            except (TypeError, AttributeError):
                # If scroll_to fails or doesn't exist, skip scrolling
                pass
        
        try:
            self.lyrics_list.update()
        except RuntimeError:
            pass