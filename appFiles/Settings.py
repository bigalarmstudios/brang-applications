"""Local Brang OS preferences. Changes take effect after Brang OS restarts."""

__version__ = "1.0"

import json
import os

import pygame


DEFAULTS = {"theme": "classic", "cursor_size": 50, "use_catalog_cache": True}
THEMES = [("classic", "Classic Blue"), ("night", "Night"), ("forest", "Forest")]

PANEL = pygame.Rect(390, 180, 1140, 720)
THEME_BUTTONS = [pygame.Rect(470 + index * 240, 360, 210, 55) for index in range(len(THEMES))]
MINUS_BUTTON = pygame.Rect(470, 510, 50, 45)
PLUS_BUTTON = pygame.Rect(720, 510, 50, 45)
CACHE_BUTTON = pygame.Rect(470, 620, 30, 30)
SAVE_BUTTON = pygame.Rect(1130, 790, 300, 55)

font = None
small_font = None
title_font = None
settings = DEFAULTS.copy()
status = "Choose what you prefer, then save."


def init_fonts():
    global font, small_font, title_font
    if font is None:
        font = pygame.font.SysFont("Arial", 24)
        small_font = pygame.font.SysFont("Arial", 18)
        title_font = pygame.font.SysFont("Arial", 34, bold=True)


def settings_file():
    root = os.environ.get("BRANG_OS_HOME", os.getcwd())
    return os.path.join(root, "programs", "cache", "brang_settings.json")


def load_settings():
    global settings
    try:
        with open(settings_file(), "r", encoding="utf-8") as file:
            stored = json.load(file)
        if isinstance(stored, dict):
            settings.update(stored)
    except (OSError, ValueError, TypeError):
        pass
    if settings.get("theme") not in {name for name, _ in THEMES}:
        settings["theme"] = DEFAULTS["theme"]
    try:
        settings["cursor_size"] = max(20, min(80, int(settings.get("cursor_size", 50))))
    except (TypeError, ValueError):
        settings["cursor_size"] = DEFAULTS["cursor_size"]
    settings["use_catalog_cache"] = bool(settings.get("use_catalog_cache", True))


def save_settings():
    global status
    try:
        path = settings_file()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=2)
        status = "Saved locally. Close Brang OS and start it again to apply these changes."
    except OSError as error:
        status = f"Could not save settings: {error}"


def update(events):
    global status
    init_fonts()
    for event in events:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            continue
        for index, (name, _) in enumerate(THEMES):
            if THEME_BUTTONS[index].collidepoint(event.pos):
                settings["theme"] = name
                status = "Theme selected. Save, then restart Brang OS to apply it."
                break
        else:
            if MINUS_BUTTON.collidepoint(event.pos):
                settings["cursor_size"] = max(20, settings["cursor_size"] - 5)
            elif PLUS_BUTTON.collidepoint(event.pos):
                settings["cursor_size"] = min(80, settings["cursor_size"] + 5)
            elif CACHE_BUTTON.collidepoint(event.pos):
                settings["use_catalog_cache"] = not settings["use_catalog_cache"]
            elif SAVE_BUTTON.collidepoint(event.pos):
                save_settings()


def button(screen, rect, label, selected=False):
    mouse = pygame.mouse.get_pos()
    color = (46, 184, 114) if selected else ((100, 160, 210) if rect.collidepoint(mouse) else (70, 130, 180))
    pygame.draw.rect(screen, color, rect, border_radius=4)
    text = small_font.render(label, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=rect.center))


def render(screen):
    init_fonts()
    screen.fill((0, 0, 255))
    pygame.draw.rect(screen, (240, 244, 250), PANEL, border_radius=7)
    pygame.draw.rect(screen, (190, 205, 225), PANEL, 3, border_radius=7)
    pygame.draw.rect(screen, (45, 45, 48), (PANEL.x, PANEL.y, PANEL.width, 65), border_top_left_radius=7, border_top_right_radius=7)
    screen.blit(title_font.render("Brang OS Settings", True, (255, 255, 255)), (PANEL.x + 28, PANEL.y + 14))

    screen.blit(font.render("Desktop theme", True, (35, 40, 50)), (470, 305))
    for index, (name, label) in enumerate(THEMES):
        button(screen, THEME_BUTTONS[index], label, settings["theme"] == name)

    screen.blit(font.render("Cursor square size", True, (35, 40, 50)), (470, 465))
    button(screen, MINUS_BUTTON, "−")
    screen.blit(font.render(f"{settings['cursor_size']} pixels", True, (35, 40, 50)), (545, 520))
    button(screen, PLUS_BUTTON, "+")

    screen.blit(font.render("Big Alarm Store", True, (35, 40, 50)), (470, 580))
    pygame.draw.rect(screen, (255, 255, 255), CACHE_BUTTON, border_radius=3)
    pygame.draw.rect(screen, (70, 130, 180), CACHE_BUTTON, 2, border_radius=3)
    if settings["use_catalog_cache"]:
        pygame.draw.line(screen, (46, 184, 114), CACHE_BUTTON.topleft, CACHE_BUTTON.bottomright, 3)
        pygame.draw.line(screen, (46, 184, 114), CACHE_BUTTON.topright, CACHE_BUTTON.bottomleft, 3)
    screen.blit(small_font.render("Reuse the saved catalogue when possible", True, (35, 40, 50)), (515, 626))
    screen.blit(small_font.render("Turn this off to always request a fresh catalogue.", True, (120, 130, 145)), (515, 650))

    screen.blit(small_font.render(status, True, (70, 90, 115)), (470, 748))
    button(screen, SAVE_BUTTON, "Save settings")


load_settings()
