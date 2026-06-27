import pygame
import datetime
import calendar  # Built-in tool to easily layout the monthly calendar grid

# Internal application state variables
show_colon = True
last_flash_time = 0

def update(events):
    """Processes system events passed from Brang OS."""
    pass

def render(screen):
    """Draws a clean, nostalgic Nintendo DSi-style clock and calendar interface."""
    global show_colon, last_flash_time
    
    # ── 1. CORE DSi PALETTE (Light, Clean, and Playful) ────────────────
    BG_WHITE      = (245, 247, 250)
    DS_GRAY       = (215, 220, 225)
    DARK_TEXT     = (70, 75, 85)
    LIGHT_TEXT    = (140, 145, 155)
    DS_AQUA       = (0, 164, 228)    # Classic Nintendo DSi accent blue
    DS_ORANGE     = (255, 100, 0)    # Vibrant selector highlight orange
    
    # App dimensions (centered inside Brang OS frame)
    app_rect = pygame.Rect(460, 240, 1000, 600)
    
    # ── 2. DRAW BASE DECORATIONS ───────────────────────────────────────
    # Main app backing
    pygame.draw.rect(screen, BG_WHITE, app_rect)
    pygame.draw.rect(screen, DS_GRAY, app_rect, 6)
    
    # Subtle background pattern: Playful floating structural squares (very Nintendo)
    pygame.draw.rect(screen, (235, 238, 242), (490, 280, 80, 80))
    pygame.draw.rect(screen, (235, 238, 242), (1320, 680, 110, 110))
    pygame.draw.rect(screen, (235, 238, 242), (1240, 300, 60, 60))
    
    # ── 3. FETCH TIME & CALENDAR METRICS ──────────────────────────────
    now = datetime.datetime.now()
    
    # Handle colon blinking logic
    current_ticks = pygame.time.get_ticks()
    if current_ticks - last_flash_time > 500:
        show_colon = not show_colon
        last_flash_time = current_ticks
    colon = ":" if show_colon else " "
    
    # Time formats
    time_str = now.strftime(f"%I{colon}%M")  # 12-hour format hours/minutes
    sec_str = now.strftime("%S")             # Separate seconds counter
    ampm_str = now.strftime("%p")            # AM / PM Tag
    date_str = now.strftime("%B %d, %Y (%a)") # e.g., "June 27, 2026 (Sat)"

    # Fonts
    font_large_time = pygame.font.SysFont('Arial', 110, bold=True)
    font_sec        = pygame.font.SysFont('Arial', 45, bold=True)
    font_sub        = pygame.font.SysFont('Arial', 28, bold=True)
    font_cal        = pygame.font.SysFont('Arial', 22, bold=True)
    font_cal_header = pygame.font.SysFont('Arial', 18, bold=True)

    # ── 4. LEFT PANEL: DIGITAL READOUT ─────────────────────────────────
    # Render main time string (Hours and Minutes)
    time_surf = font_large_time.render(time_str, True, DARK_TEXT)
    screen.blit(time_surf, (510, 380))
    
    # Render Seconds count (Stacked higher up next to minutes)
    sec_surf = font_sec.render(sec_str, True, DS_AQUA)
    screen.blit(sec_surf, (510 + time_surf.get_width() + 10, 395))
    
    # Render AM/PM tag directly below seconds
    ampm_surf = font_cal_header.render(ampm_str, True, LIGHT_TEXT)
    screen.blit(ampm_surf, (510 + time_surf.get_width() + 12, 450))
    
    # Render Full detailed text date strip
    date_surf = font_sub.render(date_str, True, DARK_TEXT)
    screen.blit(date_surf, (510, 520))
    
    # Decorative DSi indicator line
    pygame.draw.rect(screen, DS_AQUA, (510, 575, 340, 5))
    
    # ── 5. RIGHT PANEL: MINI MONTH CALENDAR GRID ───────────────────────
    # Calendar panel wrapper box
    cal_box = pygame.Rect(920, 290, 480, 500)
    pygame.draw.rect(screen, (255, 255, 255), cal_box)
    pygame.draw.rect(screen, DS_GRAY, cal_box, 3)
    
    # Calendar month text title bar
    month_title = font_sub.render(now.strftime("%B %Y"), True, DS_AQUA)
    screen.blit(month_title, (950, 315))
    
    # Weekday header labels
    days_headers = ["M", "T", "W", "T", "F", "S", "S"]
    for i, day_h in enumerate(days_headers):
        color = DS_ORANGE if i >= 5 else DARK_TEXT  # Make weekends pop out visually
        h_surf = font_cal_header.render(day_h, True, color)
        screen.blit(h_surf, (955 + i * 62, 370))
        
    pygame.draw.line(screen, DS_GRAY, (940, 395), (1380, 395), 2)
    
    # Extract structural month calendar layout lists matrix
    month_matrix = calendar.monthcalendar(now.year, now.month)
    
    # Draw calendar grid rows and slots
    start_grid_y = 410
    for row_idx, week in enumerate(month_matrix):
        for col_idx, day_num in enumerate(week):
            if day_num == 0:
                continue # Blank day buffer filler slots before month start
                
            # Compute specific coordinates for this cell date block
            cell_x = 945 + col_idx * 62
            cell_y = start_grid_y + row_idx * 55
            
            # Is this specific slot highlighting TODAY'S date?
            if day_num == now.day:
                # Draw the iconic flashing orange square box highlight
                pygame.draw.rect(screen, DS_ORANGE, (cell_x - 8, cell_y - 4, 45, 40))
                num_surf = font_cal.render(str(day_num), True, (255, 255, 255))
            else:
                # Default daily rendering
                color = DS_AQUA if col_idx >= 5 else DARK_TEXT
                num_surf = font_cal.render(str(day_num), True, color)
                
            # Align number output text centered inside calculated bounds
            screen.blit(num_surf, (cell_x + 12 - num_surf.get_width() // 2, cell_y))