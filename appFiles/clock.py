import pygame
import datetime
import calendar

# Keep trackers to ensure we only load system assets exactly once
FONTS_INITIALIZED = False
font_large_time = None
font_sec = None
font_sub = None
font_cal = None
font_cal_header = None

def init_fonts():
    """Safely loads fonts into memory only once when the app runs."""
    global FONTS_INITIALIZED, font_large_time, font_sec, font_sub, font_cal, font_cal_header
    if not FONTS_INITIALIZED:
        pygame.font.init()
        font_large_time = pygame.font.SysFont('Arial', 110, bold=True)
        font_sec        = pygame.font.SysFont('Arial', 45, bold=True)
        font_sub        = pygame.font.SysFont('Arial', 28, bold=True)
        font_cal        = pygame.font.SysFont('Arial', 22, bold=True)
        font_cal_header = pygame.font.SysFont('Arial', 18, bold=True)
        FONTS_INITIALIZED = True

def update(events):
    pass

def render(screen):
    # Safely load fonts on the first active render frame
    init_fonts()

    # ── 1. CORE DSi PALETTE ───────────────────────────────────────────
    BG_WHITE      = (245, 247, 250)
    DS_GRAY       = (215, 220, 225)
    DARK_TEXT     = (70, 75, 85)
    LIGHT_TEXT    = (140, 145, 155)
    DS_AQUA       = (0, 164, 228)    
    DS_ORANGE     = (255, 100, 0)    
    
    app_rect = pygame.Rect(460, 240, 1000, 600)
    
    # Base background
    pygame.draw.rect(screen, BG_WHITE, app_rect)
    pygame.draw.rect(screen, DS_GRAY, app_rect, 6)
    
    # Ambient layout squares
    pygame.draw.rect(screen, (235, 238, 242), (490, 280, 80, 80))
    pygame.draw.rect(screen, (235, 238, 242), (1320, 680, 110, 110))
    pygame.draw.rect(screen, (235, 238, 242), (1240, 300, 60, 60))
    
    # ── 2. LIVE TIME CALCULATIONS (PERFECT SECOND SYNC) ───────────────
    now = datetime.datetime.now()
    
    # Sync blink with the exact microsecond of the current system second
    show_colon = now.microsecond < 500000  # True for the first half of the second
    colon = ":" if show_colon else " "
    
    time_str = now.strftime(f"%I{colon}%M")  
    sec_str = now.strftime("%S")             
    ampm_str = now.strftime("%p")            
    date_str = now.strftime("%B %d, %Y (%a)") 

    # ── 3. LEFT PANEL: DIGITAL READOUT ─────────────────────────────────
    time_surf = font_large_time.render(time_str, True, DARK_TEXT)
    screen.blit(time_surf, (510, 380))
    
    sec_surf = font_sec.render(sec_str, True, DS_AQUA)
    screen.blit(sec_surf, (510 + time_surf.get_width() + 10, 395))
    
    ampm_surf = font_cal_header.render(ampm_str, True, LIGHT_TEXT)
    screen.blit(ampm_surf, (510 + time_surf.get_width() + 12, 450))
    
    date_surf = font_sub.render(date_str, True, DARK_TEXT)
    screen.blit(date_surf, (510, 520))
    
    pygame.draw.rect(screen, DS_AQUA, (510, 575, 340, 5))
    
    # ── 4. RIGHT PANEL: MINI MONTH CALENDAR GRID ───────────────────────
    cal_box = pygame.Rect(920, 290, 480, 500)
    pygame.draw.rect(screen, (255, 255, 255), cal_box)
    pygame.draw.rect(screen, DS_GRAY, cal_box, 3)
    
    month_title = font_sub.render(now.strftime("%B %Y"), True, DS_AQUA)
    screen.blit(month_title, (950, 315))
    
    days_headers = ["M", "T", "W", "T", "F", "S", "S"]
    for i, day_h in enumerate(days_headers):
        color = DS_ORANGE if i >= 5 else DARK_TEXT  
        h_surf = font_cal_header.render(day_h, True, color)
        screen.blit(h_surf, (955 + i * 62, 370))
        
    pygame.draw.line(screen, DS_GRAY, (940, 395), (1380, 395), 2)
    
    month_matrix = calendar.monthcalendar(now.year, now.month)
    
    start_grid_y = 410
    for row_idx, week in enumerate(month_matrix):
        for col_idx, day_num in enumerate(week):
            if day_num == 0:
                continue 
                
            cell_x = 945 + col_idx * 62
            cell_y = start_grid_y + row_idx * 55
            
            if day_num == now.day:
                pygame.draw.rect(screen, DS_ORANGE, (cell_x - 8, cell_y - 4, 45, 40))
                num_surf = font_cal.render(str(day_num), True, (255, 255, 255))
            else:
                color = DS_AQUA if col_idx >= 5 else DARK_TEXT
                num_surf = font_cal.render(str(day_num), True, color)
                
            screen.blit(num_surf, (cell_x + 12 - num_surf.get_width() // 2, cell_y))