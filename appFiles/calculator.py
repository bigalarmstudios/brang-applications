import pygame
import math

# Global application state variables
expression = ""
result = ""
last_ans = "0"
advanced_mode = False

def get_buttons(app_x, app_y):
    """Dynamically calculates the layouts and hitboxes for buttons based on the mode."""
    btns = []
    
    # 1. Standard Calculator Grid Layout (5 rows, 4 columns)
    std_grid = [
        ["7", "8", "9", "/"],
        ["4", "5", "6", "*"],
        ["1", "2", "3", "-"],
        ["0", ".", "=", "+"],
        ["C", "CE", "Del", "Ans"]
    ]
    
    btn_w, btn_h = 75, 60
    gap = 12
    start_x = app_x + 20
    start_y = app_y + 220
    
    for row_idx, row in enumerate(std_grid):
        for col_idx, label in enumerate(row):
            if label == "": 
                continue
            bx = start_x + col_idx * (btn_w + gap)
            by = start_y + row_idx * (btn_h + gap)
            btns.append((pygame.Rect(bx, by, btn_w, btn_h), label))
            
    # 2. Advanced Operator Side Grid Layout (Visible only when toggled)
    if advanced_mode:
        adv_grid = [
            ["(", ")"],
            ["^", "%"],
            ["pi", "e"]
        ]
        # Shifts advanced controls immediately to the right side of the standard layout
        adv_start_x = app_x + 380
        for row_idx, row in enumerate(adv_grid):
            for col_idx, label in enumerate(row):
                bx = adv_start_x + col_idx * (btn_w + gap)
                by = start_y + row_idx * (btn_h + gap)
                btns.append((pygame.Rect(bx, by, btn_w, btn_h), label))
                
    return btns

def update(events):
    """Processes click logic on calculation matrix items passed from Brang OS."""
    global expression, result, advanced_mode, last_ans
    
    # Calculate app placement parameters dynamically to verify interaction bounds
    app_width = 560 if advanced_mode else 380
    app_x = 960 - app_width // 2
    app_y = 180
    
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            
            # Check if the Menu Expansion Toggle button was clicked
            mode_btn_rect = pygame.Rect(app_x + 20, app_y + 165, 180, 35)
            if mode_btn_rect.collidepoint(mx, my):
                advanced_mode = not advanced_mode
                continue
                
            # Evaluate grid matrix checks
            buttons = get_buttons(app_x, app_y)
            for rect, label in buttons:
                if rect.collidepoint(mx, my):
                    if label == "C":
                        expression = ""
                        result = ""
                    elif label == "CE":
                        expression = ""
                    elif label == "Del":
                        expression = expression[:-1]
                    elif label == "Ans":
                        expression += last_ans
                    elif label == "=":
                        if expression:
                            try:
                                # Sanitize expressions for execution compatibility 
                                clean_expr = expression.replace("^", "**")
                                clean_expr = clean_expr.replace("pi", str(math.pi))
                                clean_expr = clean_expr.replace("e", str(math.e))
                                
                                # Process mathematical operations safely
                                calc_val = eval(clean_expr, {"__builtins__": None}, {"math": math})
                                
                                # Format whole float conversions cleanly
                                if isinstance(calc_val, float) and calc_val.is_integer():
                                    calc_val = int(calc_val)
                                    
                                result = str(calc_val)
                                last_ans = result  # Cache calculation for memory recalls
                            except Exception:
                                result = "Syntax Error"
                    else:
                        # Append selection to string expression
                        expression += label

def render(screen):
    """Draws the Windows-style blocky calculator layout onto the core window."""
    # Compute center dimensions based on the current active UI panel configuration
    app_width = 560 if advanced_mode else 380
    app_height = 620
    app_x = 960 - app_width // 2
    app_y = 180
    
    # Initialize fonts
    sys_font = pygame.font.SysFont('Arial', 22)
    display_font = pygame.font.SysFont('Courier New', 26, bold=True)
    btn_font = pygame.font.SysFont('Arial', 24, bold=True)
    
    # ── 1. DRAW WINDOW CONTAINER FRAME ──────────────────────────────────
    app_rect = pygame.Rect(app_x, app_y, app_width, app_height)
    pygame.draw.rect(screen, (192, 192, 192), app_rect)        # Windows 95 Classic Grey Box
    pygame.draw.rect(screen, (100, 100, 100), app_rect, 6)     # Deep blocky casing border
    
    # Draw Window Top Header Bar
    header_bar = pygame.Rect(app_x, app_y, app_width, 45)
    pygame.draw.rect(screen, (52, 199, 255), header_bar)       # Accent color header
    pygame.draw.rect(screen, (100, 100, 100), header_bar, 3)
    
    title_txt = sys_font.render("System Calculator", True, (255, 255, 255))
    screen.blit(title_txt, (app_x + 15, app_y + 10))
    
    # ── 2. DRAW CALCULATOR MONITOR DISPLAY SCREEN ───────────────────────
    display_rect = pygame.Rect(app_x + 20, app_y + 70, app_width - 40, 80)
    pygame.draw.rect(screen, (255, 255, 255), display_rect)    # White display screen background
    pygame.draw.rect(screen, (50, 50, 50), display_rect, 3)     # Recessed framing outline
    
    # Draw calculation inputs (Right-aligned standard ledger layout)
    if expression:
        expr_surf = sys_font.render(expression, True, (80, 80, 80))
        screen.blit(expr_surf, (display_rect.right - expr_surf.get_width() - 12, display_rect.y + 12))
        
    # Draw answers/results output 
    res_string = result if result else "0"
    res_surf = display_font.render(res_string, True, (0, 0, 0))
    screen.blit(res_surf, (display_rect.right - res_surf.get_width() - 12, display_rect.bottom - res_surf.get_height() - 12))
    
    # ── 3. DRAW ADVANCED MODE EXPANSION TOGGLE BUTTON ─────────────────
    mode_btn_rect = pygame.Rect(app_x + 20, app_y + 165, 180, 35)
    pygame.draw.rect(screen, (220, 220, 220), mode_btn_rect)
    pygame.draw.rect(screen, (80, 80, 80), mode_btn_rect, 2)
    
    mode_label = "Mode: Standard <<" if advanced_mode else "Mode: Advanced >>"
    mode_txt = sys_font.render(mode_label, True, (0, 0, 0))
    screen.blit(mode_txt, (mode_btn_rect.x + 12, mode_btn_rect.y + 5))
    
    # ── 4. DRAW INTERACTIVE APP KEYPAD BUTTONS ─────────────────────────
    buttons = get_buttons(app_x, app_y)
    for rect, label in buttons:
        # Determine button colors based on functional classifications
        if label in ["=", "+", "-", "*", "/"]:
            btn_color = (255, 180, 50)  # Operator accent tint
        elif label in ["C", "CE", "Del"]:
            btn_color = (255, 100, 100) # Deletion/Reset warning tint
        else:
            btn_color = (235, 235, 235) # Standard numerical gray keys
            
        pygame.draw.rect(screen, btn_color, rect)
        pygame.draw.rect(screen, (50, 50, 50), rect, 2) # Outer 3D lip rim
        
        # Center typographical text label precisely on keys
        lbl_surf = btn_font.render(label, True, (0, 0, 0))
        lbl_x = rect.x + (rect.width // 2) - (lbl_surf.get_width() // 2)
        lbl_y = rect.y + (rect.height // 2) - (lbl_surf.get_height() // 2)
        screen.blit(lbl_surf, (lbl_x, lbl_y))