__version__ = "1.3"
import pygame
import os
import tkinter as tk
from tkinter import simpledialog, messagebox

pygame.font.init()
ui_font = pygame.font.SysFont('Arial', 14, bold=True)
warning_font = pygame.font.SysFont('Arial', 24, bold=True)

# OS Work Area Dimensions
WORK_AREA = pygame.Rect(210, 80, 1500, 900)
TOOLBAR_RECT = pygame.Rect(210, 80, 1500, 75)
CANVAS_RECT = pygame.Rect(230, 175, 1460, 785)

# Colors
BG_COLOR = (240, 244, 250)      
BAR_COLOR = (45, 45, 48)        
TEXT_COLOR = (240, 240, 240)  
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PANEL_BORDER = (200, 210, 230)

PALETTE = [
    (0, 0, 0), (255, 0, 0), (0, 0, 255), (0, 255, 0),
    (255, 255, 0), (255, 165, 0), (128, 0, 128), (139, 69, 19)
]

# App States
current_tool = "brush"   
current_color = (0, 0, 0)
slider_r, slider_g, slider_b = 0, 0, 0
dragging_slider = None   
brush_size = 5
is_drawing = False
last_mouse_pos = None
save_status_msg = ""
status_timer = 0
current_file_path = None  # Tracks the currently opened file

# Check dependency on launch
BASE_DIR = os.getcwd()
EXPLORER_PATH = os.path.join(BASE_DIR, "programs", "installedApps", "fileExplorer.py")
FILES_ROOT = os.path.join(BASE_DIR, "files")
has_file_explorer = os.path.exists(EXPLORER_PATH)

canvas_surface = pygame.Surface((CANVAS_RECT.width, CANVAS_RECT.height))
canvas_surface.fill(WHITE)

# Keeps a clean copy of the original image for the iPhone markup eraser
original_image_surface = pygame.Surface((CANVAS_RECT.width, CANVAS_RECT.height))
original_image_surface.fill(WHITE)

# UI Hitboxes
BTN_BRUSH_RECT  = pygame.Rect(230, 100, 65, 32)
BTN_ERASER_RECT = pygame.Rect(300, 100, 65, 32)
BTN_BUCKET_RECT = pygame.Rect(370, 100, 65, 32)

SIZE_MINUS_RECT = pygame.Rect(705, 100, 30, 32)
SIZE_PLUS_RECT  = pygame.Rect(780, 100, 30, 32)

SLIDER_R_RECT = pygame.Rect(855, 100, 100, 32)
SLIDER_G_RECT = pygame.Rect(995, 100, 100, 32)
SLIDER_B_RECT = pygame.Rect(1135, 100, 100, 32)
PREVIEW_RECT  = pygame.Rect(1255, 100, 32, 32)

SAVE_BTN_RECT = pygame.Rect(1560, 100, 120, 32)

def load_file(passed_argument):
    """Called by brangdesktop.py handover sequence when opening an image."""
    global current_file_path, canvas_surface, original_image_surface
    current_file_path = passed_argument
    
    if os.path.exists(current_file_path):
        try:
            loaded_img = pygame.image.load(current_file_path)
            canvas_surface.fill(WHITE)
            canvas_surface.blit(loaded_img, (0, 0))
            
            # Lock the base image layout into the background restoration canvas
            original_image_surface.fill(WHITE)
            original_image_surface.blit(loaded_img, (0, 0))
        except Exception as e:
            print(f"Error loading image into Paint: {e}")

def prompt_filename():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    result = simpledialog.askstring("Save Artwork", "Enter filename (e.g., painting.png):", parent=root)
    root.destroy()
    return result

def save_canvas():
    global save_status_msg, status_timer, current_file_path
    
    # Overwrite directly if file path is already known
    if current_file_path and os.path.exists(current_file_path):
        target_path = current_file_path
    else:
        name = prompt_filename()
        if not name:
            return
        name = name.strip()
        if not (name.endswith(".png") or name.endswith(".jpg")):
            name += ".png"
            
        if not os.path.exists(FILES_ROOT):
            os.makedirs(FILES_ROOT)
            
        target_path = os.path.join(FILES_ROOT, name)
        current_file_path = target_path
        
    try:
        pygame.image.save(canvas_surface, target_path)
        save_status_msg = "Saved successfully!"
        # Commit the save into original image baseline so future erasures stop here
        original_image_surface.blit(canvas_surface, (0, 0))
    except Exception as e:
        save_status_msg = f"Save failed: {e}"
    status_timer = pygame.time.get_ticks()

def erase_at(pos, radius):
    """Restores the original image backdrop pixels within a circular stamp."""
    cx, cy = pos
    x1 = max(0, cx - radius)
    y1 = max(0, cy - radius)
    x2 = min(CANVAS_RECT.width, cx + radius)
    y2 = min(CANVAS_RECT.height, cy + radius)
    
    w = x2 - x1
    h = y2 - y1
    if w <= 0 or h <= 0:
        return
        
    patch = pygame.Surface((w, h))
    patch.blit(original_image_surface, (0, 0), (x1, y1, w, h))
    
    mask = pygame.Surface((w, h))
    mask.fill((255, 0, 255))  # Magenta chroma-key background
    pygame.draw.circle(mask, (0, 0, 0), (cx - x1, cy - y1), radius)
    mask.set_colorkey((0, 0, 0))
    
    patch.blit(mask, (0, 0))
    patch.set_colorkey((255, 0, 255))
    canvas_surface.blit(patch, (x1, y1))

def erase_line(p1, p2, radius):
    """Interpolates steps across mouse drag vectors to prevent choppy eraser gaps."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    distance = max(1, int(((dx**2) + (dy**2))**0.5))
    
    for i in range(0, distance + 1, max(1, radius // 2)):
        t = i / distance
        cx = int(x1 + dx * t)
        cy = int(y1 + dy * t)
        erase_at((cx, cy), radius)

def fast_flood_fill(surface, start_pos, fill_color):
    target_color = surface.get_at(start_pos)[:3]
    fill_rgb = fill_color[:3]
    if target_color == fill_rgb:
        return
    
    width, height = surface.get_size()
    pixels = pygame.PixelArray(surface)
    
    target_mapped = surface.map_rgb(target_color)
    fill_mapped = surface.map_rgb(fill_rgb)
    
    stack = [start_pos]
    while stack:
        x, y = stack.pop()
        if pixels[x, y] == target_mapped:
            pixels[x, y] = fill_mapped
            if x > 0 and pixels[x-1, y] == target_mapped: 
                stack.append((x - 1, y))
            if x < width - 1 and pixels[x+1, y] == target_mapped: 
                stack.append((x + 1, y))
            if y > 0 and pixels[x, y-1] == target_mapped: 
                stack.append((x, y - 1))
            if y < height - 1 and pixels[x, y+1] == target_mapped: 
                stack.append((x, y + 1))
    del pixels

def update(events):
    global current_color, brush_size, is_drawing, last_mouse_pos, current_tool
    global slider_r, slider_g, slider_b, dragging_slider
    
    if not has_file_explorer:
        return

    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()
    
    canvas_mouse_x = mouse_pos[0] - CANVAS_RECT.x
    canvas_mouse_y = mouse_pos[1] - CANVAS_RECT.y
    current_canvas_pos = (canvas_mouse_x, canvas_mouse_y)

    if dragging_slider and mouse_pressed[0]:
        if dragging_slider == "R":
            rel_x = max(0, min(100, mouse_pos[0] - SLIDER_R_RECT.x))
            slider_r = int((rel_x / 100) * 255)
        elif dragging_slider == "G":
            rel_x = max(0, min(100, mouse_pos[0] - SLIDER_G_RECT.x))
            slider_g = int((rel_x / 100) * 255)
        elif dragging_slider == "B":
            rel_x = max(0, min(100, mouse_pos[0] - SLIDER_B_RECT.x))
            slider_b = int((rel_x / 100) * 255)
        
        current_color = (slider_r, slider_g, slider_b)
        if current_tool == "eraser":
            current_tool = "brush"

    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if SAVE_BTN_RECT.collidepoint(mouse_pos):
                save_canvas()
                continue
            
            if BTN_BRUSH_RECT.collidepoint(mouse_pos):
                current_tool = "brush"
                continue
            if BTN_ERASER_RECT.collidepoint(mouse_pos):
                current_tool = "eraser"
                continue
            if BTN_BUCKET_RECT.collidepoint(mouse_pos):
                current_tool = "bucket"
                continue

            if SIZE_MINUS_RECT.collidepoint(mouse_pos):
                brush_size = max(1, brush_size - 2)
                continue
            if SIZE_PLUS_RECT.collidepoint(mouse_pos):
                brush_size = min(50, brush_size + 2)
                continue

            for idx, color in enumerate(PALETTE):
                color_rect = pygame.Rect(450 + (idx * 28), 104, 22, 22)
                if color_rect.collidepoint(mouse_pos):
                    current_color = color
                    slider_r, slider_g, slider_b = color
                    if current_tool == "eraser":
                        current_tool = "brush"
                    continue

            if SLIDER_R_RECT.inflate(0, 10).collidepoint(mouse_pos):
                dragging_slider = "R"
            elif SLIDER_G_RECT.inflate(0, 10).collidepoint(mouse_pos):
                dragging_slider = "G"
            elif SLIDER_B_RECT.inflate(0, 10).collidepoint(mouse_pos):
                dragging_slider = "B"

            if CANVAS_RECT.collidepoint(mouse_pos):
                if current_tool == "bucket":
                    fast_flood_fill(canvas_surface, current_canvas_pos, current_color)
                else:
                    is_drawing = True
                    last_mouse_pos = current_canvas_pos
                    if current_tool == "eraser":
                        erase_at(current_canvas_pos, brush_size)
                    else:
                        pygame.draw.circle(canvas_surface, current_color, current_canvas_pos, brush_size)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            is_drawing = False
            last_mouse_pos = None
            dragging_slider = None

    if is_drawing and mouse_pressed[0] and current_tool != "bucket":
        if CANVAS_RECT.collidepoint(mouse_pos):
            if last_mouse_pos is not None:
                if current_tool == "eraser":
                    erase_line(last_mouse_pos, current_canvas_pos, brush_size)
                else:
                    pygame.draw.line(canvas_surface, current_color, last_mouse_pos, current_canvas_pos, brush_size * 2)
                    pygame.draw.circle(canvas_surface, current_color, current_canvas_pos, brush_size)
            last_mouse_pos = current_canvas_pos
        else:
            last_mouse_pos = None

def render(screen):
    pygame.draw.rect(screen, BG_COLOR, WORK_AREA)
    pygame.draw.rect(screen, PANEL_BORDER, WORK_AREA, 3)
    
    if not has_file_explorer:
        error_overlay = pygame.Rect(210, 80, 1500, 900)
        pygame.draw.rect(screen, (40, 45, 55), error_overlay)
        screen.blit(warning_font.render("CRITICAL SYSTEM ERROR", True, (255, 100, 100)), (550, 400))
        screen.blit(ui_font.render("The 'fileExplorer' application is not installed on this system.", True, WHITE), (550, 460))
        screen.blit(ui_font.render("You must download it from the Big Alarm Store first before using Paint.", True, WHITE), (550, 490))
        return

    pygame.draw.rect(screen, BAR_COLOR, TOOLBAR_RECT)
    mouse_pos = pygame.mouse.get_pos()
    
    for btn, name, mode_id in [(BTN_BRUSH_RECT, "Brush", "brush"), (BTN_ERASER_RECT, "Eraser", "eraser"), (BTN_BUCKET_RECT, "Bucket", "bucket")]:
        if current_tool == mode_id:
            c = (0, 122, 204)
        else:
            c = (80, 80, 85) if btn.collidepoint(mouse_pos) else (60, 60, 65)
        pygame.draw.rect(screen, c, btn, border_radius=3)
        lbl = ui_font.render(name, True, TEXT_COLOR)
        screen.blit(lbl, (btn.x + (btn.width // 2 - lbl.get_width() // 2), btn.y + 8))

    for idx, color in enumerate(PALETTE):
        color_rect = pygame.Rect(450 + (idx * 28), 104, 22, 22)
        pygame.draw.rect(screen, color, color_rect)
        if current_color == color and current_tool != "eraser":
            pygame.draw.rect(screen, WHITE, color_rect, 2)
        else:
            pygame.draw.rect(screen, (100, 100, 105), color_rect, 1)

    c_minus = (100, 100, 105) if SIZE_MINUS_RECT.collidepoint(mouse_pos) else (60, 60, 65)
    pygame.draw.rect(screen, c_minus, SIZE_MINUS_RECT, border_radius=2)
    screen.blit(ui_font.render("-", True, TEXT_COLOR), (SIZE_MINUS_RECT.x + 11, SIZE_MINUS_RECT.y + 6))
    
    screen.blit(ui_font.render(f"Size: {brush_size}", True, TEXT_COLOR), (742, 108))
    
    c_plus = (100, 100, 105) if SIZE_PLUS_RECT.collidepoint(mouse_pos) else (60, 60, 65)
    pygame.draw.rect(screen, c_plus, SIZE_PLUS_RECT, border_radius=2)
    screen.blit(ui_font.render("+", True, TEXT_COLOR), (SIZE_PLUS_RECT.x + 9, SIZE_PLUS_RECT.y + 6))

    for slider, val, lbl_text, color_theme in [(SLIDER_R_RECT, slider_r, "R", (255, 70, 70)), (SLIDER_G_RECT, slider_g, "G", (70, 255, 70)), (SLIDER_B_RECT, slider_b, "B", (70, 70, 255))]:
        screen.blit(ui_font.render(lbl_text, True, TEXT_COLOR), (slider.x - 16, slider.y + 6))
        pygame.draw.line(screen, (80, 80, 85), (slider.x, slider.y + 16), (slider.x + 100, slider.y + 16), 4)
        handle_x = slider.x + int((val / 255) * 100)
        pygame.draw.rect(screen, color_theme, (handle_x - 4, slider.y + 6, 8, 20))

    pygame.draw.rect(screen, current_color, PREVIEW_RECT, border_radius=2)
    pygame.draw.rect(screen, WHITE, PREVIEW_RECT, 1)

    btn_save_c = (100, 100, 105) if SAVE_BTN_RECT.collidepoint(mouse_pos) else (60, 60, 65)
    pygame.draw.rect(screen, btn_save_c, SAVE_BTN_RECT, border_radius=3)
    
    save_text = "Quick Save" if current_file_path else "Save Image"
    screen.blit(ui_font.render(save_text, True, TEXT_COLOR), (SAVE_BTN_RECT.x + 24, SAVE_BTN_RECT.y + 8))

    global save_status_msg
    if save_status_msg and pygame.time.get_ticks() - status_timer < 3000:
        msg_lbl = ui_font.render(save_status_msg, True, (100, 255, 100))
        screen.blit(msg_lbl, (1320, 108))
    else:
        save_status_msg = ""

    screen.blit(canvas_surface, (CANVAS_RECT.x, CANVAS_RECT.y))
    pygame.draw.rect(screen, PANEL_BORDER, CANVAS_RECT, 2)