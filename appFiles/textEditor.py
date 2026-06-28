__version__ = "1.3"
import pygame
import os

pygame.font.init()
editor_font = pygame.font.SysFont('Courier New', 20)
ui_font = pygame.font.SysFont('Arial', 18, bold=True)

BG_COLOR = (30, 30, 30)       
TEXT_COLOR = (240, 240, 240)  
BAR_COLOR = (45, 45, 48)      
BTN_COLOR = (60, 60, 65)      
BTN_HOVER = (80, 80, 85)      
CURSOR_COLOR = (0, 122, 204)  

text_lines = [""]
cursor_row = 0
cursor_col = 0
file_to_edit = None
save_status_msg = ""
status_timer = 0

# Adjusted Save Box button coordinates to match upper-right screen boundaries
SAVE_RECT_BOUNDS = pygame.Rect(1500, 92, 100, 35)

def load_file(file_path):
    global text_lines, file_to_edit, cursor_row, cursor_col
    file_to_edit = file_path
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                text_lines = content.splitlines()
                if not text_lines:
                    text_lines = [""]
        except Exception:
            text_lines = ["Error loading file."]
    else:
        text_lines = [""]
    cursor_row = 0
    cursor_col = 0

def save_file():
    global save_status_msg, status_timer
    if file_to_edit:
        try:
            content = "\n".join(text_lines)
            with open(file_to_edit, "w", encoding="utf-8") as f:
                f.write(content)
            save_status_msg = "Saved successfully!"
        except Exception as e:
            save_status_msg = f"Save failed: {e}"
    else:
        save_status_msg = "No file target assigned."
    status_timer = pygame.time.get_ticks()

def update(events):
    global text_lines, cursor_row, cursor_col, save_status_msg
    mouse_pos = pygame.mouse.get_pos()
    
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if SAVE_RECT_BOUNDS.collidepoint(mouse_pos):
                save_file()
                
        elif event.type == pygame.KEYDOWN:
            current_line = text_lines[cursor_row]
            
            if event.key == pygame.K_BACKSPACE:
                if cursor_col > 0:
                    text_lines[cursor_row] = current_line[:cursor_col-1] + current_line[cursor_col:]
                    cursor_col -= 1
                elif cursor_row > 0:
                    prev_line_len = len(text_lines[cursor_row-1])
                    text_lines[cursor_row-1] += current_line
                    text_lines.pop(cursor_row)
                    cursor_row -= 1
                    cursor_col = prev_line_len
                    
            elif event.key == pygame.K_RETURN:
                line_left = current_line[:cursor_col]
                line_right = current_line[cursor_col:]
                text_lines[cursor_row] = line_left
                text_lines.insert(cursor_row + 1, line_right)
                cursor_row += 1
                cursor_col = 0
                
            elif event.key == pygame.K_LEFT:
                if cursor_col > 0:
                    cursor_col -= 1
                elif cursor_row > 0:
                    cursor_row -= 1
                    cursor_col = len(text_lines[cursor_row])
                    
            elif event.key == pygame.K_RIGHT:
                if cursor_col < len(current_line):
                    cursor_col += 1
                elif cursor_row < len(text_lines) - 1:
                    cursor_row += 1
                    cursor_col = 0
                    
            elif event.key == pygame.K_UP:
                if cursor_row > 0:
                    cursor_row -= 1
                    cursor_col = min(cursor_col, len(text_lines[cursor_row]))
                    
            elif event.key == pygame.K_DOWN:
                if cursor_row < len(text_lines) - 1:
                    cursor_row += 1
                    cursor_col = min(cursor_col, len(text_lines[cursor_row]))
                    
            else:
                if event.unicode and event.unicode.isprintable():
                    text_lines[cursor_row] = current_line[:cursor_col] + event.unicode + current_line[cursor_col:]
                    cursor_col += 1

def render(screen):
    work_area = pygame.Rect(210, 80, 1500, 900)
    pygame.draw.rect(screen, BG_COLOR, work_area)
    
    ribbon = pygame.Rect(210, 80, 1500, 60)
    pygame.draw.rect(screen, BAR_COLOR, ribbon)
    
    display_title = os.path.basename(file_to_edit) if file_to_edit else "Untitled.txt"
    title_lbl = ui_font.render(f"Text Editor — {display_title}", True, TEXT_COLOR)
    screen.blit(title_lbl, (230, 98))
    
    mouse_pos = pygame.mouse.get_pos()
    btn_c = BTN_HOVER if SAVE_RECT_BOUNDS.collidepoint(mouse_pos) else BTN_COLOR
    pygame.draw.rect(screen, btn_c, SAVE_RECT_BOUNDS)
    pygame.draw.rect(screen, (100, 100, 105), SAVE_RECT_BOUNDS, 1)
    
    save_lbl = ui_font.render("Save File", True, TEXT_COLOR)
    screen.blit(save_lbl, (SAVE_RECT_BOUNDS.x + 12, SAVE_RECT_BOUNDS.y + 6))
    
    global save_status_msg
    if save_status_msg and pygame.time.get_ticks() - status_timer < 3000:
        msg_lbl = ui_font.render(save_status_msg, True, (100, 255, 100))
        screen.blit(msg_lbl, (1200, 98))
    else:
        save_status_msg = ""
        
    text_start_x = 240
    text_start_y = 160
    line_spacing = 28
    
    for idx, line in enumerate(text_lines):
        line_y = text_start_y + (idx * line_spacing)
        if line_y > 950: 
            break
            
        lbl = editor_font.render(line, True, TEXT_COLOR)
        screen.blit(lbl, (text_start_x, line_y))
        
        if idx == cursor_row:
            text_before_cursor = line[:cursor_col]
            cursor_offset_x = editor_font.size(text_before_cursor)[0]
            cx = text_start_x + cursor_offset_x
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.rect(screen, CURSOR_COLOR, (cx, line_y + 2, 2, 22))