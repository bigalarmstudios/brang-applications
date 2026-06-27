import pygame
import os
import shutil
import tkinter as tk
from tkinter import simpledialog, messagebox

# ── SAFELY INITIALIZE FONTS ONCE ──────────────────────────────────────
pygame.font.init()
ui_font = None
file_font = None

def init_fonts():
    global ui_font, file_font
    if ui_font is None:
        ui_font = pygame.font.SysFont('Arial', 18, bold=True)
        file_font = pygame.font.SysFont('Arial', 16)

# ── CRASH FIX: LOOK AT THE REAL DISK PATH ─────────────────────────────
# This gets the true directory path of brangdesktop.py on your PC
BASE_DIR = os.getcwd()
FILES_ROOT = os.path.join(BASE_DIR, "files")

# Ensure the core "files" folder exists on launch
if not os.path.exists(FILES_ROOT):
    os.makedirs(FILES_ROOT)

# Track current active path inside the explorer
current_path = FILES_ROOT

# UI Scroll/List offsets
selected_item = None
file_rects = {}  # Maps Pygame Rects -> File/Folder names

def get_relative_path():
    """Returns a clean display path relative to the files root."""
    rel = os.path.relpath(current_path, FILES_ROOT)
    return "Root" if rel == "." else f"Root/{rel}".replace("\\", "/")

def prompt_user_input(title, prompt):
    """Helper to open a neat popup string dialog window."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    result = simpledialog.askstring(title, prompt, parent=root)
    root.destroy()
    return result

def show_alert(title, message):
    """Helper to display warning or info boxes."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo(title, message, parent=root)
    root.destroy()

def update(events):
    global current_path, selected_item, file_rects
    
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            
            # 1. Check top utility button clicks
            if pygame.Rect(480, 305, 90, 35).collidepoint(mx, my):
                handle_create()
            elif pygame.Rect(580, 305, 90, 35).collidepoint(mx, my):
                handle_rename()
            elif pygame.Rect(680, 305, 90, 35).collidepoint(mx, my):
                handle_delete()
            elif pygame.Rect(780, 305, 90, 35).collidepoint(mx, my):
                handle_move()
            elif pygame.Rect(1340, 305, 90, 35).collidepoint(mx, my):
                handle_back_directory()
                
            # 2. Check file/folder list clicks
            else:
                clicked_something = False
                for rect, item_name in list(file_rects.items()):
                    if rect.collidepoint(mx, my):
                        clicked_something = True
                        full_item_path = os.path.join(current_path, item_name)
                        
                        if selected_item == item_name:
                            # Double-click context: If it's a directory, go inside
                            if os.path.isdir(full_item_path):
                                current_path = full_item_path
                                selected_item = None
                        else:
                            selected_item = item_name
                        break
                
                if not clicked_something:
                    # Clicking blank empty space clears selection
                    if pygame.Rect(480, 360, 960, 440).collidepoint(mx, my):
                        selected_item = None

# ── OS FILE OPERATIONS HANDLERS ───────────────────────────────────────

def handle_create():
    global current_path
    name = prompt_user_input("Create Item", "Enter name (end with extension for files, e.g. notes.txt):")
    if name:
        target = os.path.join(current_path, name)
        try:
            if "." in name: # Treat as file
                with open(target, "w") as f:
                    f.write("")
            else: # Treat as directory folder
                os.makedirs(target, exist_ok=True)
        except Exception as e:
            show_alert("Error", f"Could not create item: {e}")

def handle_rename():
    global current_path, selected_item
    if not selected_item:
        show_alert("Selection Required", "Please select a file or folder first!")
        return
    new_name = prompt_user_input("Rename", f"Enter new name for '{selected_item}':")
    if new_name:
        src = os.path.join(current_path, selected_item)
        dst = os.path.join(current_path, new_name)
        if not os.path.exists(dst):
            try:
                os.rename(src, dst)
                selected_item = None
            except Exception as e:
                show_alert("Error", f"Rename failed: {e}")
        else:
            show_alert("Error", "An item with that name already exists.")

def handle_delete():
    global current_path, selected_item
    if not selected_item:
        show_alert("Selection Required", "Please select an item to delete!")
        return
    target = os.path.join(current_path, selected_item)
    try:
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
        selected_item = None
    except Exception as e:
        show_alert("Error", f"Could not delete item: {e}")

def handle_move():
    global current_path, selected_item
    if not selected_item:
        show_alert("Selection Required", "Please select an item to move!")
        return
    dest_folder = prompt_user_input("Move Item", "Enter destination folder relative to Root (e.g. downloads):")
    if dest_folder is not None:
        if dest_folder.strip() in ["", "Root", "root"]:
            target_dir = FILES_ROOT
        else:
            target_dir = os.path.join(FILES_ROOT, dest_folder)
            
        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            src = os.path.join(current_path, selected_item)
            dst = os.path.join(target_dir, selected_item)
            try:
                shutil.move(src, dst)
                selected_item = None
            except Exception as e:
                show_alert("Error", f"Could not move file: {e}")
        else:
            show_alert("Error", "Destination folder directory does not exist.")

def handle_back_directory():
    global current_path, selected_item
    if current_path != FILES_ROOT:
        current_path = os.path.dirname(current_path)
        selected_item = None

# ── RENDER ENGINE ─────────────────────────────────────────────────────

def render(screen):
    global file_rects, selected_item
    init_fonts()
    
    WINDOW_BG     = (240, 244, 248)
    PANEL_BORDER  = (180, 190, 200)
    TEXT_DARK     = (40, 45, 55)
    BTN_GRAY      = (210, 215, 225)
    BTN_HOVER     = (130, 200, 240)
    FOLDER_COLOR  = (240, 190, 70)
    FILE_COLOR    = (70, 160, 240)
    
    app_rect = pygame.Rect(460, 240, 1000, 600)
    pygame.draw.rect(screen, WINDOW_BG, app_rect)
    pygame.draw.rect(screen, PANEL_BORDER, app_rect, 5)
    
    pygame.draw.rect(screen, (255, 255, 255), (480, 255, 960, 40))
    pygame.draw.rect(screen, PANEL_BORDER, (480, 255, 960, 40), 2)
    path_lbl = ui_font.render(f" Location: {get_relative_path()}", True, TEXT_DARK)
    screen.blit(path_lbl, (490, 263))
    
    buttons = [
        ("Create", 480, 305),
        ("Rename", 580, 305),
        ("Delete", 680, 305),
        ("Move", 780, 305),
        ("Up [..]", 1340, 305)
    ]
    
    for text, bx, by in buttons:
        btn_rect = pygame.Rect(bx, by, 90, 35)
        pygame.draw.rect(screen, BTN_GRAY, btn_rect)
        pygame.draw.rect(screen, PANEL_BORDER, btn_rect, 2)
        btn_txt = ui_font.render(text, True, TEXT_DARK)
        screen.blit(btn_txt, (bx + (45 - btn_txt.get_width() // 2), by + 7))

    list_area = pygame.Rect(480, 360, 960, 440)
    pygame.draw.rect(screen, (255, 255, 255), list_area)
    pygame.draw.rect(screen, PANEL_BORDER, list_area, 2)
    
    try:
        raw_items = os.listdir(current_path)
        folders = sorted([i for i in raw_items if os.path.isdir(os.path.join(current_path, i))], key=lambda s: s.lower())
        files = sorted([i for i in raw_items if not os.path.isdir(os.path.join(current_path, i))], key=lambda s: s.lower())
        items = folders + files
    except Exception:
        items = []
        
    file_rects.clear()
    start_x, start_y = 500, 385
    column_width = 230
    row_height = 50
    items_per_column = 8

    for index, item in enumerate(items):
        col = index // items_per_column
        row = index % items_per_column
        
        item_x = start_x + (col * column_width)
        item_y = start_y + (row * row_height)
        
        if item_y + 40 > 800:
            continue
            
        full_path = os.path.join(current_path, item)
        is_dir = os.path.isdir(full_path)
        
        item_rect = pygame.Rect(item_x, item_y, 210, 40)
        file_rects[item_rect] = item
        
        if selected_item == item:
            pygame.draw.rect(screen, BTN_HOVER, item_rect)
        else:
            pygame.draw.rect(screen, (245, 248, 252), item_rect)
        pygame.draw.rect(screen, PANEL_BORDER, item_rect, 1)
        
        icon_color = FOLDER_COLOR if is_dir else FILE_COLOR
        pygame.draw.rect(screen, icon_color, (item_x + 8, item_y + 10, 20, 20))
        
        display_name = item if len(item) <= 16 else item[:14] + ".."
        name_surf = file_font.render(display_name, True, TEXT_DARK)
        screen.blit(name_surf, (item_x + 36, item_y + 11))