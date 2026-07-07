__version__ = "2.10"
import pygame
# REMOVED: screen = pygame.display.set_mode(...) <- This was breaking the main desktop window
import os
import shutil
import tkinter as tk
from tkinter import simpledialog, messagebox

pygame.font.init()
ui_font = None
file_font = None

def init_fonts():
    global ui_font, file_font
    if ui_font is None:
        ui_font = pygame.font.SysFont('Arial', 18, bold=True)
        file_font = pygame.font.SysFont('Arial', 16)

BASE_DIR = os.getcwd()
FILES_ROOT = os.path.join(BASE_DIR, "files")

if not os.path.exists(FILES_ROOT):
    os.makedirs(FILES_ROOT)

current_path = FILES_ROOT
selected_item = None
file_rects = {}

last_clicked_item = None
last_click_time = 0
is_save_as_intercept = False

moving_source_path = None     
move_worker_generator = None  

def get_relative_path():
    rel = os.path.relpath(current_path, FILES_ROOT)
    return "Root" if rel == "." else f"Root/{rel}".replace("\\", "/")

def prompt_user_input(title, prompt_text):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    result = simpledialog.askstring(title, prompt_text, parent=root)
    root.destroy()
    return result

def load_file(mode_argument):
    global is_save_as_intercept
    if mode_argument == "SAVE_AS_MODE":
        is_save_as_intercept = True

def process_save_as_handover():
    global is_save_as_intercept
    is_save_as_intercept = False
    
    name = prompt_user_input("Save Unsaved Document", "Enter filename to create (e.g., draft.txt):")
    if not name:
        return
    if not name.endswith(".txt"):
        name += ".txt"
        
    full_new_path = os.path.join(current_path, name.strip())
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
    buffer_path = os.path.join(cache_dir, "editor_buffer_cache.txt")
    
    saved_content = ""
    if os.path.exists(buffer_path):
        with open(buffer_path, "r", encoding="utf-8") as f:
            saved_content = f.read()
        os.remove(buffer_path)
        
    with open(full_new_path, "w", encoding="utf-8") as f:
        f.write(saved_content)
        
    handover_path = os.path.join(cache_dir, "app_handover.txt")
    with open(handover_path, "w", encoding="utf-8") as f:
        f.write(f"textEditor|{full_new_path}")
        
    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"action": "exit_to_editor"}))

def check_text_editor_launch(full_file_path):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    ans = messagebox.askyesno("Open File", f"Would you like to open {os.path.basename(full_file_path)} inside textEditor?")
    root.destroy()
    
    if ans:
        handover_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "app_handover.txt")
        os.makedirs(os.path.dirname(handover_path), exist_ok=True)
        with open(handover_path, "w", encoding="utf-8") as f:
            f.write(f"textEditor|{full_file_path}")
        return True
    return False

def check_paint_or_viewer_launch(full_file_path):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    # Prompt 1: Open with Paint
    ans_paint = messagebox.askyesno("Open File", f"Would you like to open {os.path.basename(full_file_path)} inside Paint to edit?")
    if ans_paint:
        root.destroy()
        handover_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "app_handover.txt")
        os.makedirs(os.path.dirname(handover_path), exist_ok=True)
        with open(handover_path, "w", encoding="utf-8") as f:
            f.write(f"paint|{full_file_path}")
        pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"action": "exit_to_paint"}))
        return True
        
    # Prompt 2: Open with ImageViewer
    ans_viewer = messagebox.askyesno("Open File", f"Would you like to open {os.path.basename(full_file_path)} inside ImageViewer instead?")
    root.destroy()
    if ans_viewer:
        handover_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "app_handover.txt")
        os.makedirs(os.path.dirname(handover_path), exist_ok=True)
        with open(handover_path, "w", encoding="utf-8") as f:
            f.write(f"imageViewer|{full_file_path}")
        pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"action": "exit_to_imageViewer"}))
        return True

    return False

def create_move_worker(src, dst_dir):
    if not os.path.exists(src):
        return
    
    basename = os.path.basename(src)
    dst = os.path.join(dst_dir, basename)
    
    if src == dst_dir or dst_dir.startswith(src + os.sep):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror("Movement Loop Error", "Cannot move a parent folder inside itself or its own subdirectories!")
        root.destroy()
        return

    if os.path.exists(dst):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        overwrite = messagebox.askyesno("Item Exists", f"'{basename}' already exists here. Overwrite it?")
        root.destroy()
        if not overwrite:
            return
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        else:
            os.remove(dst)

    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        for root_item, dirs, files in os.walk(src):
            for file in files:
                s_file = os.path.join(root_item, file)
                rel = os.path.relpath(s_file, src)
                d_file = os.path.join(dst, rel)
                os.makedirs(os.path.dirname(d_file), exist_ok=True)
                shutil.copy2(s_file, d_file)
                yield 
            yield
        shutil.rmtree(src)
    else:
        shutil.copy2(src, dst)
        yield
        os.remove(src)

def draw_vector_icon(screen, x, y, is_dir):
    if is_dir:
        pygame.draw.rect(screen, (240, 200, 90), (x, y + 4, 22, 14), border_radius=2)
        pygame.draw.rect(screen, (210, 170, 60), (x, y + 1, 10, 5), border_top_left_radius=2, border_top_right_radius=2)
    else:
        pygame.draw.rect(screen, (230, 235, 240), (x + 3, y, 16, 20), border_radius=1)
        pygame.draw.rect(screen, (170, 180, 190), (x + 3, y, 16, 20), 1, border_radius=1)
        pygame.draw.line(screen, (170, 180, 190), (x + 7, y + 6), (x + 15, y + 6), 1)
        pygame.draw.line(screen, (170, 180, 190), (x + 7, y + 10), (x + 15, y + 10), 1)
        pygame.draw.line(screen, (170, 180, 190), (x + 7, y + 14), (x + 12, y + 14), 1)

def update(events):
    global current_path, selected_item, file_rects, last_clicked_item, last_click_time
    global moving_source_path, move_worker_generator
    init_fonts()
    
    if move_worker_generator is not None:
        try:
            next(move_worker_generator)
        except StopIteration:
            move_worker_generator = None
            selected_item = None
        return 

    if is_save_as_intercept:
        process_save_as_handover()
        return
        
    mouse_pos = pygame.mouse.get_pos()
    
    new_folder_rect = pygame.Rect(230, 310, 130, 35)
    new_file_rect   = pygame.Rect(375, 310, 110, 35)
    delete_rect     = pygame.Rect(500, 310, 90, 35)
    move_btn_rect   = pygame.Rect(605, 310, 130, 35) 
    back_btn_rect   = pygame.Rect(230, 165, 80, 35)
    
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if back_btn_rect.collidepoint(mouse_pos):
                if current_path != FILES_ROOT:
                    current_path = os.path.dirname(current_path)
                    selected_item = None
                continue
                
            if new_folder_rect.collidepoint(mouse_pos):
                name = prompt_user_input("New Folder", "Enter folder name:")
                if name:
                    target = os.path.join(current_path, name.strip())
                    if not os.path.exists(target):
                        os.makedirs(target)
                continue
                
            if new_file_rect.collidepoint(mouse_pos):
                name = prompt_user_input("New File", "Enter file name (e.g. canvas.png):")
                if name:
                    name = name.strip()
                    if not (name.endswith(".png") or name.endswith(".jpg")):
                        name += ".png"
                    
                    target = os.path.join(current_path, name)
                    if not os.path.exists(target):
                        try:
                            surf = pygame.Surface((1460, 785))
                            surf.fill((255, 255, 255))
                            pygame.image.save(surf, target)
                        except Exception as e:
                            print(f"Error creating file: {e}")
                        
                    handover_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "app_handover.txt")
                    os.makedirs(os.path.dirname(handover_path), exist_ok=True)
                    with open(handover_path, "w", encoding="utf-8") as f:
                        f.write(f"paint|{target}")
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"action": "exit_to_paint"}))
                continue
                
            if delete_rect.collidepoint(mouse_pos) and selected_item:
                target = os.path.join(current_path, selected_item)
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                confirm = messagebox.askyesno("Confirm Delete", f"Delete '{selected_item}' permanently?")
                root.destroy()
                if confirm:
                    if os.path.isdir(target):
                        shutil.rmtree(target)
                    else:
                        os.remove(target)
                    selected_item = None
                continue

            if move_btn_rect.collidepoint(mouse_pos):
                if moving_source_path is None:
                    if selected_item:
                        moving_source_path = os.path.join(current_path, selected_item)
                else:
                    move_worker_generator = create_move_worker(moving_source_path, current_path)
                    moving_source_path = None
                continue
                
            clicked_something = False
            for item, rect in file_rects.items():
                if rect.collidepoint(mouse_pos):
                    clicked_something = True
                    current_time = pygame.time.get_ticks()
                    
                    if item == last_clicked_item and (current_time - last_click_time) < 400:
                        full_path = os.path.join(current_path, item)
                        if os.path.isdir(full_path):
                            current_path = full_path
                            selected_item = None
                        elif item.endswith(".txt"):
                            if check_text_editor_launch(full_path):
                                pygame.event.post(pygame.event.Event(pygame.USEREVENT, {"action": "exit_to_editor"}))
                        elif item.endswith(".png"):
                            check_paint_or_viewer_launch(full_path)
                        last_clicked_item = None
                        break
                    else:
                        selected_item = item
                        last_clicked_item = item
                        last_click_time = current_time
                    
            if not clicked_something:
                list_area = pygame.Rect(490, 375, 1180, 560)
                if list_area.collidepoint(mouse_pos):
                    selected_item = None

        if event.type == pygame.USEREVENT and getattr(event, "action", "") in ["exit_to_editor", "exit_to_explorer", "exit_to_paint", "exit_to_imageViewer"]:
            events.append(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

def render(screen):
    init_fonts()
    PANEL_BG = (240, 244, 250)
    WHITE = (255, 255, 255)
    PANEL_BORDER = (200, 210, 230)
    BTN_COLOR = (70, 130, 180)
    BTN_HOVER = (100, 160, 210)
    BTN_ACTIVE_GREEN = (46, 184, 114)
    TEXT_DARK = (40, 45, 55)
    
    work_area = pygame.Rect(210, 80, 1500, 900)
    pygame.draw.rect(screen, PANEL_BG, work_area)
    pygame.draw.rect(screen, PANEL_BORDER, work_area, 3)
    
    header_rect = pygame.Rect(210, 80, 1500, 65)
    pygame.draw.rect(screen, WHITE, header_rect)
    pygame.draw.rect(screen, PANEL_BORDER, header_rect, 2)
    
    path_str = get_relative_path()
    path_lbl = ui_font.render(f"Location: {path_str}", True, TEXT_DARK)
    screen.blit(path_lbl, (240, 100))
    
    mouse_pos = pygame.mouse.get_pos()
    back_rect = pygame.Rect(230, 165, 80, 35)
    is_root = (current_path == FILES_ROOT)
    b_color = (210, 215, 225) if is_root else (BTN_HOVER if back_rect.collidepoint(mouse_pos) else BTN_COLOR)
    pygame.draw.rect(screen, b_color, back_rect)
    screen.blit(ui_font.render("<- Up", True, WHITE), (back_rect.x + 15, back_rect.y + 6))
    
    new_folder_rect = pygame.Rect(230, 310, 130, 35)
    new_file_rect   = pygame.Rect(375, 310, 110, 35)
    delete_rect     = pygame.Rect(500, 310, 90, 35)
    move_btn_rect   = pygame.Rect(605, 310, 130, 35)
    
    for r, t in [(new_folder_rect, "+ Folder"), (new_file_rect, "+ Image File"), (delete_rect, "Delete")]:
        c = BTN_HOVER if r.collidepoint(mouse_pos) else BTN_COLOR
        if t == "Delete" and not selected_item:
            c = (210, 215, 225)
        pygame.draw.rect(screen, c, r)
        screen.blit(ui_font.render(t, True, WHITE), (r.x + 12, r.y + 6))

    if moving_source_path is None:
        c = BTN_HOVER if move_btn_rect.collidepoint(mouse_pos) else BTN_COLOR
        if not selected_item:
            c = (210, 215, 225)
        pygame.draw.rect(screen, c, move_btn_rect)
        screen.blit(ui_font.render("Move File", True, WHITE), (move_btn_rect.x + 14, move_btn_rect.y + 6))
    else:
        c = BTN_HOVER if move_btn_rect.collidepoint(mouse_pos) else BTN_ACTIVE_GREEN
        pygame.draw.rect(screen, c, move_btn_rect)
        screen.blit(ui_font.render("Move Here", True, WHITE), (move_btn_rect.x + 12, move_btn_rect.y + 6))

    sidebar = pygame.Rect(230, 375, 240, 560)
    pygame.draw.rect(screen, WHITE, sidebar)
    pygame.draw.rect(screen, PANEL_BORDER, sidebar, 2)
    
    lbl_side = ui_font.render("System Actions", True, BTN_COLOR)
    screen.blit(lbl_side, (245, 395))
    
    hint_lbl1 = file_font.render("Double-click directories", True, TEXT_DARK)
    hint_lbl2 = file_font.render("to enter them.", True, TEXT_DARK)
    hint_lbl3 = file_font.render("Double-click .png files", True, TEXT_DARK)
    hint_lbl4 = file_font.render("to edit or view them.", True, TEXT_DARK)
    screen.blit(hint_lbl1, (245, 440))
    screen.blit(hint_lbl2, (245, 465))
    screen.blit(hint_lbl3, (245, 500))
    screen.blit(hint_lbl4, (245, 525))
    
    if moving_source_path:
        src_lbl = file_font.render("Holding File:", True, BTN_ACTIVE_GREEN)
        name_lbl = file_font.render(os.path.basename(moving_source_path), True, TEXT_DARK)
        screen.blit(src_lbl, (245, 580))
        screen.blit(name_lbl, (245, 605))

    list_area = pygame.Rect(490, 375, 1180, 560)
    pygame.draw.rect(screen, WHITE, list_area)
    pygame.draw.rect(screen, PANEL_BORDER, list_area, 2)
    
    try:
        items = sorted(os.listdir(current_path), key=lambda x: not os.path.isdir(os.path.join(current_path, x)))
    except Exception:
        items = []
        
    file_rects.clear()
    
    if not items:
        empty_lbl = ui_font.render("This folder is completely empty.", True, (160, 170, 185))
        text_x = list_area.x + (list_area.width // 2 - empty_lbl.get_width() // 2)
        text_y = list_area.y + (list_area.height // 2 - empty_lbl.get_height() // 2)
        screen.blit(empty_lbl, (text_x, text_y))
    else:
        start_x, start_y = 510, 395
        column_width = 280
        row_height = 50
        items_per_column = 10
        
        for index, item in enumerate(items):
            col = index // items_per_column
            row = index % items_per_column
            
            item_x = start_x + (col * column_width)
            item_y = start_y + (row * row_height)
            
            if item_x + column_width > 1650:
                continue
                
            full_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(full_path)
            
            item_rect = pygame.Rect(item_x, item_y, 260, 40)
            file_rects[item] = item_rect
            
            if selected_item == item:
                pygame.draw.rect(screen, (220, 235, 255), item_rect)
                pygame.draw.rect(screen, (150, 190, 255), item_rect, 1)
            else:
                pygame.draw.rect(screen, (248, 250, 254), item_rect)
                pygame.draw.rect(screen, PANEL_BORDER, item_rect, 1)
            
            draw_vector_icon(screen, item_x + 10, item_y + 10, is_dir)
            
            display_text = item
            if len(display_text) > 22:
                display_text = display_text[:19] + "..."
                
            txt_surface = file_font.render(display_text, True, TEXT_DARK)
            screen.blit(txt_surface, (item_x + 40, item_y + 10))

    if move_worker_generator is not None:
        overlay_rect = pygame.Rect(490, 375, 1180, 560)
        pygame.draw.rect(screen, (240, 240, 240, 200), overlay_rect)
        pygame.draw.rect(screen, PANEL_BORDER, overlay_rect, 2)
        
        load_msg = ui_font.render("Moving file/s... Please wait.", True, BTN_COLOR)
        screen.blit(load_msg, (overlay_rect.x + (overlay_rect.width // 2 - load_msg.get_width() // 2),
                               overlay_rect.y + (overlay_rect.height // 2 - load_msg.get_height() // 2)))