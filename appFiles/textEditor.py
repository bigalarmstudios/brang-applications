__version__ = "1.0"
import pygame
import os

# Initialize font engine if not done
pygame.font.init()
editor_font = pygame.font.SysFont('Courier New', 20)
ui_font = pygame.font.SysFont('Arial', 18, bold=True)

# Application Theme Colors
BG_COLOR = (30, 30, 30)       # Dark mode background
TEXT_COLOR = (240, 240, 240)  # White/Off-white text
BAR_COLOR = (45, 45, 48)      # Toolbar area
BTN_COLOR = (60, 60, 65)      # Button state
BTN_HOVER = (80, 80, 85)      # Highlight state
CURSOR_COLOR = (0, 122, 204)  # Accent blue

# State Variables
text_lines = [""]
cursor_row = 0
cursor_col = 0
file_to_edit = None
save_status_msg = ""
status_timer = 0

def load_file(file_path):
    """Called by the OS when launching with an argument string."""
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
    
    # Handle mouse tracking for Save button bounds
    mouse_pos = pygame.mouse.get_pos()
    save_rect = pygame.Rect(230, 95, 100, 35)
    
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if save_rect.collidepoint(mouse_pos):
                save_file()
                
        elif event.type == pygame.KEYDOWN:
            current_line = text_lines[cursor_row]
            
            if event.key == pygame.K_BACKSPACE:
                if cursor_col > 0:
                    # Remove character before cursor
                    text_lines[cursor_row] = current_line[:cursor_col-1] + current_line[cursor_col:]
                    cursor_col -= 1
                elif cursor_row > 0:
                    # Merge line upward
                    prev_line_len = len(text_lines[cursor_row-1])
                    text_lines[cursor_row-1] += current_line
                    text_lines.pop(cursor_row)
                    cursor_row -= 1
                    cursor_col = prev_line_len
                    
            elif event.key == pygame.K_RETURN:
                # Split line into a new row
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
                # Text unicode capture stream
                if event.unicode and event.unicode.isprintable():
                    text_lines[cursor_row] = current_line[:cursor_col] + event.unicode + current_line[cursor_col:]
                    cursor_col += 1

def render(screen):
    # Base background area layout (constrained workspace wrapper)
    work_area = pygame.Rect(210, 80, 1500, 900)
    pygame.draw.rect(screen, BG_COLOR, work_area)
    
    # Top Action Ribbon Bar
    ribbon = pygame.Rect(210, 80, 1500, 60)
    pygame.draw.rect(screen, BAR_COLOR, ribbon)
    
    # Render File Name Metadata Label
    display_title = os.path.basename(file_to_edit) if file_to_edit else "Untitled.txt"
    title_lbl = ui_font.render(f"Text Editor — {display_title}", True, TEXT_COLOR)
    screen.blit(title_lbl, (230, 98))
    
    # Draw Save Functional Button Hook
    save_rect = pygame.Rect(1500, 92, 100, 35)
    mouse_pos = pygame.mouse.get_pos()
    btn_c = BTN_HOVER if save_rect.collidepoint(mouse_pos) else BTN_COLOR
    pygame.draw.rect(screen, btn_c, save_rect)
    pygame.draw.rect(screen, (100, 100, 105), save_rect, 1)
    
    save_lbl = ui_font.render("Save File", True, TEXT_COLOR)
    screen.blit(save_lbl, (save_rect.x + 12, save_rect.y + 6))
    
    # Display Saving Confirmation status messages temporarily
    global save_status_msg
    if save_status_msg and pygame.time.get_ticks() - status_timer < 3000:
        msg_lbl = ui_font.render(save_status_msg, True, (100, 255, 100))
        screen.blit(msg_lbl, (1200, 98))
    else:
        save_status_msg = ""
        
    # Render Lines text grid inside editor space boundary walls
    text_start_x = 240
    text_start_y = 160
    line_spacing = 28
    
    for idx, line in enumerate(text_lines):
        line_y = text_start_y + (idx * line_spacing)
        if line_y > 950: 
            break # Avoid screen clipping
            
        lbl = editor_font.render(line, True, TEXT_COLOR)
        screen.blit(lbl, (text_start_x, line_y))
        
        # Calculate and draw typing block cursor safely
        if idx == cursor_row:
            text_before_cursor = line[:cursor_col]
            cursor_offset_x = editor_font.size(text_before_cursor)[0]
            cx = text_start_x + cursor_offset_x
            
            # Blink active visual state mapping calculation
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.rect(screen, CURSOR_COLOR, (cx, line_y + 2, 2, 22))