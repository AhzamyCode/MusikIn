"""Entry point MusikIn - Async"""
import flet as ft
from config import COLORS, APP_NAME, WINDOW_WIDTH, WINDOW_HEIGHT
from ui.search_view import SearchView
from ui.player_view import PlayerView


def main(page: ft.Page):
    print(f"[Main] Initializing MusikIn app")
    # Konfigurasi window
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLORS["bg_primary"]
    page.window_width = WINDOW_WIDTH
    page.window_height = WINDOW_HEIGHT
    page.window_min_width = 600
    page.window_min_height = 400
    page.padding = 0
    
    page.theme = ft.Theme(
        color_scheme_seed=COLORS["accent"],
        visual_density=ft.VisualDensity.COMFORTABLE,
    )
    print(f"[Main] Page configuration complete")
    
    def on_track_selected(track):
        print(f"[Main] Track selected: {track.title} by {track.artist} (ID: {track.id})")
        async def load_and_navigate():
            print(f"[Navigation] Starting track load: {track.title} by {track.artist}")
            await player_view.load_track(track)
            print(f"[Navigation] Track loaded, navigating to player view")
            await page.push_route("/player")
            # Refresh UI after navigation
            player_view.refresh_ui()
            print(f"[Navigation] Player view navigation complete")
        page.run_task(load_and_navigate)
    
    async def on_back():
        print(f"[Main] Back button pressed, returning to search")
        await page.push_route("/search")
    
    print(f"[Main] Creating views")
    search_view = SearchView(on_track_selected)
    player_view = PlayerView(on_back)
    print(f"[Main] Views created successfully")
    
    def route_change(e: ft.RouteChangeEvent):
        print(f"[Main] Route change: {e.route}")
        page.views.clear()
        if e.route == "/player":
            print(f"[Main] Navigating to player view")
            page.views.append(player_view)
        else:
            print(f"[Main] Navigating to search view")
            page.views.append(search_view)
        page.update()
        print(f"[Main] Route change complete")
    
    def view_pop(e: ft.ViewPopEvent):
        print(f"[Main] View pop event")
        page.views.pop()
        top_view = page.views[-1]
        print(f"[Main] Popping back to route: {top_view.route}")
        page.push_route(top_view.route)
    
    print(f"[Main] Setting up event handlers")
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    print(f"[Main] Initializing with search route")
    async def init():
        await page.push_route("/search")
        print(f"[Main] App initialization complete")
    page.run_task(init)


if __name__ == "__main__":
    ft.run(main)