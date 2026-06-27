import pygame
import datetime

# Internal application state variables
show_colon = True
last_flash_time = 0

def update(events):
    """Processes any local app interaction events passed from Brang OS."""
    # The clock runs completely automatically, but this stays to satisfy the OS framework loop.
    pass

def render(screen):
    """Draws the retro system clock interface onto the core canvas surface."""
    global show_colon, last_flash_time
    
    # ── 1. RENDER RETRO SYSTEM WINDOW ───────────────────────────────────
    # A central container box matching the block style of Brang OS
    app_window = pygame.Rect(460, 240, 1000, 600)
    pygame.draw.rect(screen, (30, 35, 60), app_window)        # Retro Monitor Navy Background
    pygame.draw.rect(screen, (150, 150, 150), app_window, 8)  # Thick gray frame border
    
    # Window top banner header bar
    header_bar = pygame.Rect(460, 240, 1000, 50)
    pygame.draw.rect(screen, (52, 199, 255), header_bar)     # APPSTORE_BLUE header accent
    pygame.draw.rect(screen, (150, 150, 150), header_bar, 4)  # Edge border
    
    # Header title text 
    header_font = pygame.font.SysFont('Arial', 24)
    title_surface = header_font.render("System Clock Manager v1.0", True, (255, 255, 255))
    screen.blit(title_surface, (480, 252))
    
    # ── 2. LIVE DATE & TIME CALCULATIONS ────────────────────────────────
    now = datetime.datetime.now()
    
    # Calculate blinking animation for the colon separator every 500ms
    current_ticks = pygame.time.get_ticks()
    if current_ticks - last_flash_time > 500:
        show_colon = not show_colon
        last_flash_time = current_ticks
        
    colon_char = ":" if show_colon else " "
    
    # Format strings for digital time string and localized date calendar string
    formatted_time = now.strftime(f"%H{colon_char}%M{colon_char}%S")
    formatted_date = now.strftime("%A, %B %d, %Y")
    
    # ── 3. DRAW THE OLD-SCHOOL LCD INTERFACE ───────────────────────────
    # The terminal screen housing the green numbers
    lcd_screen = pygame.Rect(560, 360, 800, 200)
    pygame.draw.rect(screen, (10, 15, 20), lcd_screen)       # Deep black backing
    pygame.draw.rect(screen, (45, 210, 255), lcd_screen, 3)   # Cyber neon blue outline trim
    
    # Initialize stylized typographic fonts
    terminal_font = pygame.font.SysFont('Courier New', 95, bold=True)
    calendar_font = pygame.font.SysFont('Arial', 38)
    status_font   = pygame.font.SysFont('Arial', 20)
    
    # Render Time Data (Retro Terminal Emerald Green glow)
    time_surface = terminal_font.render(formatted_time, True, (0, 255, 100))
    time_x = lcd_screen.x + (lcd_screen.width // 2) - (time_surface.get_width() // 2)
    time_y = lcd_screen.y + (lcd_screen.height // 2) - (time_surface.get_height() // 2)
    screen.blit(time_surface, (time_x, time_y))
    
    # Render Calendar Date Data (Classic White text centered below LCD)
    date_surface = calendar_font.render(formatted_date, True, (255, 255, 255))
    date_x = app_window.x + (app_window.width // 2) - (date_surface.get_width() // 2)
    screen.blit(date_surface, (date_x, 610))
    
    # Render Bottom Status Context String
    status_surface = status_font.render("Clock Source: Local PC Hardware Interrupt  |  Status: Sync Verified", True, (160, 165, 170))
    screen.blit(status_surface, (560, 790))