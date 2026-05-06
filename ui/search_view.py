"""View untuk pencarian - Async"""
import flet as ft
import threading
from config import COLORS
from ui.components import SearchBar, TrackCard
from core.search_engine import search_engine


class SearchView(ft.View):
    def __init__(self, on_track_selected):
        self.on_track_selected = on_track_selected
        self.results_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=8,
        )
        
        self.loading = ft.ProgressRing(
            width=30, height=30,
            color=COLORS["accent"],
            visible=False,
        )
        
        self.search_bar = SearchBar(on_submit=self._on_search)
        
        super().__init__(
            route="/search",
            bgcolor=COLORS["bg_primary"],
            padding=30,
            controls=[
                ft.Column(
                    [
                        ft.Text(
                            "MusikIn",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=COLORS["text_primary"],
                        ),
                        ft.Text(
                            "Cari dan dengarkan musik tanpa gangguan",
                            size=14,
                            color=COLORS["text_secondary"],
                        ),
                        ft.Divider(color=COLORS["bg_secondary"], height=30),
                        self.search_bar,
                        ft.Container(height=10),
                        ft.Row([self.loading], alignment=ft.MainAxisAlignment.CENTER),
                        self.results_column,
                    ],
                    expand=True,
                )
            ],
        )
    
    def _on_search(self, e):
        query = self.search_bar.value.strip()
        if not query:
            print(f"[SearchView] Empty search query, ignoring")
            return
        
        print(f"[SearchView] Starting search for: '{query}'")
        self.loading.visible = True
        self.results_column.controls.clear()
        self.update()
        
        def do_search():
            try:
                print(f"[SearchView] Searching YouTube for: '{query}'")
                results = search_engine.search(query, max_results=15)
                print(f"[SearchView] Search completed, found {len(results) if not isinstance(results, Exception) else 0} results")
            except Exception as ex:
                print(f"[SearchView] Search failed with exception: {ex}")
                results = ex
            
            async def update_ui():
                print(f"[SearchView] Updating UI with search results")
                self.loading.visible = False
                if isinstance(results, Exception):
                    print(f"[SearchView] Displaying search error")
                    self.results_column.controls.append(
                        ft.Text(
                            f"Error: {results}",
                            color=COLORS["error"],
                            text_align=ft.TextAlign.CENTER,
                        )
                    )
                elif not results:
                    print(f"[SearchView] No results found")
                    self.results_column.controls.append(
                        ft.Text(
                            "Tidak ada hasil ditemukan.",
                            color=COLORS["text_secondary"],
                            text_align=ft.TextAlign.CENTER,
                        )
                    )
                else:
                    print(f"[SearchView] Displaying {len(results)} search results")
                    for track in results:
                        self.results_column.controls.append(
                            TrackCard(track, on_click=self._on_track_click)
                        )
                self.update()
                print(f"[SearchView] UI updated with search results")
            
            if self.page:
                self.page.run_task(update_ui)
            else:
                print(f"[SearchView] Cannot update UI - no page reference")
        
        print(f"[SearchView] Starting search thread")
        threading.Thread(target=do_search, daemon=True).start()
    
    def _on_track_click(self, track):
        print(f"[SearchView] Track selected: {track.title} by {track.artist}")
        self.on_track_selected(track)