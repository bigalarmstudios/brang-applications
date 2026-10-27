"""A text-only YouTube search client for Brang OS.

This app uses the official YouTube Data API for searches.  It intentionally does
not download or cache videos.  Video playback stays in YouTube's own player.
"""

__version__ = "1.0"

import json
import os
import threading
import time
import urllib.parse
import urllib.request
import webbrowser

import pygame


APP_NAME = "YouTube Search"
WINDOW = pygame.Rect(260, 120, 1400, 840)
PLAYER_SIZE = (920, 610)
RESULT_LIMIT = 10
CACHE_SECONDS = 60 * 60 * 6

BACKGROUND = (45, 210, 255)
PANEL = (240, 244, 250)
HEADER = (45, 45, 48)
TEXT = (35, 40, 50)
MUTED = (120, 130, 145)
BUTTON = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
GREEN = (46, 184, 114)
RED = (210, 70, 70)
ORANGE = (240, 150, 45)
WHITE = (255, 255, 255)

FONT = None
SMALL_FONT = None
TITLE_FONT = None

search_text = ""
api_key = ""
focused_field = None
results = []
status = "Enter a search and your YouTube Data API key."
cache_enabled = True
searching = False
player = None
drag_offset = None


def init_fonts():
    global FONT, SMALL_FONT, TITLE_FONT
    if FONT is None:
        FONT = pygame.font.SysFont("Arial", 22)
        SMALL_FONT = pygame.font.SysFont("Arial", 17)
        TITLE_FONT = pygame.font.SysFont("Arial", 30, bold=True)


def brang_root():
    configured = os.environ.get("BRANG_OS_HOME")
    if configured:
        return configured
    return os.getcwd()


def cache_paths():
    directory = os.path.join(brang_root(), "programs", "cache")
    return directory, os.path.join(directory, "youtube_search_cache.json"), os.path.join(directory, "youtube_config.json")


def load_saved_key():
    global api_key
    _, _, config_file = cache_paths()
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            api_key = str(json.load(file).get("api_key", ""))
    except (OSError, ValueError, TypeError):
        api_key = ""


def save_key():
    directory, _, config_file = cache_paths()
    try:
        os.makedirs(directory, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as file:
            json.dump({"api_key": api_key}, file)
        return "API key saved on this computer."
    except OSError as error:
        return f"Could not save API key: {error}"


def read_cache(query):
    _, cache_file, _ = cache_paths()
    try:
        with open(cache_file, "r", encoding="utf-8") as file:
            cached = json.load(file)
        entry = cached.get(query.casefold())
        if entry and time.time() - entry.get("saved_at", 0) < CACHE_SECONDS:
            return entry.get("results", [])
    except (OSError, ValueError, TypeError):
        pass
    return None


def save_cache(query, found_results):
    directory, cache_file, _ = cache_paths()
    try:
        os.makedirs(directory, exist_ok=True)
        cached = {}
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as file:
                cached = json.load(file)
        cached[query.casefold()] = {"saved_at": time.time(), "results": found_results}
        with open(cache_file, "w", encoding="utf-8") as file:
            json.dump(cached, file)
    except (OSError, ValueError, TypeError):
        pass


def fetch_results(query, key):
    """Fetch only video metadata through YouTube's documented search endpoint."""
    params = urllib.parse.urlencode({
        "part": "snippet",
        "type": "video",
        "maxResults": RESULT_LIMIT,
        "q": query,
        "key": key,
    })
    request = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/search?{params}",
        headers={"User-Agent": "BrangOS-YouTubeSearch/1.0"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))

    found_results = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if video_id:
            found_results.append({
                "id": video_id,
                "title": snippet.get("title", "Untitled video"),
                "channel": snippet.get("channelTitle", "Unknown channel"),
            })
    return found_results


def begin_search():
    global searching, results, status
    query = search_text.strip()
    key = api_key.strip()
    if not query:
        status = "Type something to search for first."
        return
    if not key:
        status = "A YouTube Data API key is required. Type it above, then click Save key."
        return
    if searching:
        return

    cached = read_cache(query) if cache_enabled else None
    if cached is not None:
        results = cached
        status = f"Showing {len(results)} cached text results for \"{query}\"."
        return

    searching = True
    status = "Searching YouTube…"

    def worker():
        global searching, results, status
        try:
            found_results = fetch_results(query, key)
            results = found_results
            if cache_enabled:
                save_cache(query, found_results)
            status = f"Found {len(found_results)} video result(s). Select one to open it."
        except Exception as error:
            message = str(error)
            if "HTTP Error 400" in message or "HTTP Error 403" in message:
                status = "YouTube rejected the API key or this key does not have YouTube Data API v3 enabled."
            else:
                status = f"Search failed: {message}"
        finally:
            searching = False

    threading.Thread(target=worker, daemon=True).start()


def open_player(result):
    global player
    player = {
        "result": result,
        "rect": pygame.Rect(500, 220, *PLAYER_SIZE),
        "opened_at": time.time(),
        "buffering": True,
    }


def truncate(text, limit):
    return text if len(text) <= limit else f"{text[:limit - 1]}…"


def draw_button(screen, rect, label, color=BUTTON):
    mouse = pygame.mouse.get_pos()
    fill = BUTTON_HOVER if rect.collidepoint(mouse) and color == BUTTON else color
    pygame.draw.rect(screen, fill, rect, border_radius=4)
    label_surface = SMALL_FONT.render(label, True, WHITE)
    screen.blit(label_surface, label_surface.get_rect(center=rect.center))


def field_rects():
    return {
        "search": pygame.Rect(WINDOW.x + 30, WINDOW.y + 90, 700, 42),
        "key": pygame.Rect(WINDOW.x + 30, WINDOW.y + 158, 700, 38),
        "search_button": pygame.Rect(WINDOW.x + 750, WINDOW.y + 90, 210, 42),
        "save_button": pygame.Rect(WINDOW.x + 750, WINDOW.y + 158, 130, 38),
        "cache": pygame.Rect(WINDOW.x + 910, WINDOW.y + 164, 22, 22),
    }


def player_controls():
    if player is None:
        return {}
    rect = player["rect"]
    return {
        "title": pygame.Rect(rect.x, rect.y, rect.width, 52),
        "close": pygame.Rect(rect.right - 45, rect.y + 10, 30, 30),
        "open": pygame.Rect(rect.x + 260, rect.bottom - 70, 220, 42),
        "pause": pygame.Rect(rect.x + 500, rect.bottom - 70, 160, 42),
    }


def update(events):
    global focused_field, search_text, api_key, cache_enabled, status, player, drag_offset
    init_fonts()
    mouse = pygame.mouse.get_pos()
    fields = field_rects()
    controls = player_controls()

    if player and player["buffering"] and time.time() - player["opened_at"] > 0.8:
        player["buffering"] = False

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if player:
                if controls["close"].collidepoint(event.pos):
                    player = None
                    drag_offset = None
                    continue
                if controls["open"].collidepoint(event.pos):
                    video_id = player["result"]["id"]
                    webbrowser.open(f"https://www.youtube.com/watch?v={urllib.parse.quote(video_id)}")
                    status = "Opened the official YouTube player in your browser."
                    continue
                if controls["pause"].collidepoint(event.pos):
                    status = "Use YouTube's own player controls to pause or resume the video."
                    continue
                if controls["title"].collidepoint(event.pos):
                    drag_offset = (event.pos[0] - player["rect"].x, event.pos[1] - player["rect"].y)
                    continue

            if fields["search"].collidepoint(event.pos):
                focused_field = "search"
            elif fields["key"].collidepoint(event.pos):
                focused_field = "key"
            elif fields["search_button"].collidepoint(event.pos):
                begin_search()
            elif fields["save_button"].collidepoint(event.pos):
                status = save_key()
            elif fields["cache"].collidepoint(event.pos):
                cache_enabled = not cache_enabled
            else:
                for index, result in enumerate(results[:RESULT_LIMIT]):
                    result_rect = pygame.Rect(WINDOW.x + 30, WINDOW.y + 270 + index * 51, WINDOW.width - 60, 44)
                    if result_rect.collidepoint(event.pos):
                        open_player(result)
                        break
                else:
                    focused_field = None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            drag_offset = None

        elif event.type == pygame.MOUSEMOTION and drag_offset and player:
            player["rect"].x = max(20, min(1920 - player["rect"].width - 20, event.pos[0] - drag_offset[0]))
            player["rect"].y = max(20, min(1080 - player["rect"].height - 20, event.pos[1] - drag_offset[1]))

        elif event.type == pygame.KEYDOWN and focused_field:
            if event.key == pygame.K_RETURN:
                begin_search()
            elif event.key == pygame.K_BACKSPACE:
                if focused_field == "search":
                    search_text = search_text[:-1]
                else:
                    api_key = api_key[:-1]
            elif event.unicode and event.unicode.isprintable():
                if focused_field == "search" and len(search_text) < 120:
                    search_text += event.unicode
                elif focused_field == "key" and len(api_key) < 180:
                    api_key += event.unicode


def render(screen):
    init_fonts()
    screen.fill(BACKGROUND)
    pygame.draw.rect(screen, PANEL, WINDOW, border_radius=6)
    pygame.draw.rect(screen, (190, 205, 225), WINDOW, 3, border_radius=6)
    pygame.draw.rect(screen, HEADER, (WINDOW.x, WINDOW.y, WINDOW.width, 58), border_top_left_radius=6, border_top_right_radius=6)
    screen.blit(TITLE_FONT.render(APP_NAME, True, WHITE), (WINDOW.x + 24, WINDOW.y + 12))

    fields = field_rects()
    screen.blit(SMALL_FONT.render("Search YouTube", True, TEXT), (fields["search"].x, fields["search"].y - 24))
    screen.blit(SMALL_FONT.render("YouTube Data API key", True, TEXT), (fields["key"].x, fields["key"].y - 24))
    for name in ("search", "key"):
        border = BUTTON if focused_field == name else (180, 190, 205)
        pygame.draw.rect(screen, WHITE, fields[name], border_radius=3)
        pygame.draw.rect(screen, border, fields[name], 2, border_radius=3)
    screen.blit(FONT.render(search_text or "Type what you want to find", True, TEXT if search_text else MUTED), (fields["search"].x + 10, fields["search"].y + 8))
    masked_key = "•" * max(0, len(api_key) - 4) + api_key[-4:] if api_key else "Paste your key here"
    screen.blit(SMALL_FONT.render(masked_key, True, TEXT if api_key else MUTED), (fields["key"].x + 10, fields["key"].y + 10))

    draw_button(screen, fields["search_button"], "Search YouTube now!", GREEN)
    draw_button(screen, fields["save_button"], "Save key")
    pygame.draw.rect(screen, WHITE, fields["cache"], border_radius=3)
    pygame.draw.rect(screen, BUTTON, fields["cache"], 2, border_radius=3)
    if cache_enabled:
        pygame.draw.line(screen, GREEN, fields["cache"].topleft, fields["cache"].bottomright, 3)
        pygame.draw.line(screen, GREEN, fields["cache"].topright, fields["cache"].bottomleft, 3)
    screen.blit(SMALL_FONT.render("Cache text results for 6 hours", True, TEXT), (fields["cache"].right + 8, fields["cache"].y + 2))

    status_color = ORANGE if searching else TEXT
    screen.blit(SMALL_FONT.render(truncate(status, 125), True, status_color), (WINDOW.x + 30, WINDOW.y + 220))
    for index, result in enumerate(results[:RESULT_LIMIT]):
        result_rect = pygame.Rect(WINDOW.x + 30, WINDOW.y + 270 + index * 51, WINDOW.width - 60, 44)
        is_hovered = result_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (225, 235, 248) if is_hovered else WHITE, result_rect, border_radius=3)
        pygame.draw.rect(screen, (195, 210, 230), result_rect, 1, border_radius=3)
        title = f"{index + 1}. {truncate(result['title'], 82)}"
        screen.blit(SMALL_FONT.render(title, True, TEXT), (result_rect.x + 12, result_rect.y + 4))
        screen.blit(SMALL_FONT.render(truncate(result["channel"], 70), True, MUTED), (result_rect.x + 12, result_rect.y + 23))

    if player:
        draw_player(screen)


def draw_player(screen):
    controls = player_controls()
    rect = player["rect"]
    result = player["result"]
    pygame.draw.rect(screen, (20, 22, 26), rect, border_radius=6)
    pygame.draw.rect(screen, WHITE, rect, 3, border_radius=6)
    pygame.draw.rect(screen, HEADER, controls["title"], border_top_left_radius=6, border_top_right_radius=6)
    screen.blit(FONT.render("YouTube player — drag this bar to move", True, WHITE), (rect.x + 18, rect.y + 14))
    draw_button(screen, controls["close"], "X", RED)

    content = pygame.Rect(rect.x + 35, rect.y + 95, rect.width - 70, rect.height - 190)
    pygame.draw.rect(screen, (32, 37, 47), content, border_radius=5)
    screen.blit(TITLE_FONT.render(truncate(result["title"], 48), True, WHITE), (content.x + 35, content.y + 90))
    screen.blit(FONT.render(result["channel"], True, (190, 205, 225)), (content.x + 35, content.y + 140))
    state = "Buffering search selection…" if player["buffering"] else "Ready to open in YouTube"
    screen.blit(FONT.render(state, True, ORANGE if player["buffering"] else GREEN), (content.x + 35, content.y + 205))
    screen.blit(SMALL_FONT.render("Video is played by YouTube in your browser; this app does not download video.", True, (190, 205, 225)), (content.x + 35, content.y + 250))
    draw_button(screen, controls["open"], "Open in YouTube", RED)
    draw_button(screen, controls["pause"], "Pause: use browser", (100, 110, 125))
