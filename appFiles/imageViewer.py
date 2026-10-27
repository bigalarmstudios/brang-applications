__version__ = "3.0"
import pygame
import os

pygame.font.init()
ui_font = pygame.font.SysFont('Arial', 18, bold=True)

# Application state
loaded_image = None
image_path = ""

def load_file(passed_argument):
    """
    Called automatically by brangdesktop.py when handing over a file.
    This receives the filepath string directly in memory.
    """
    global loaded_image, image_path

    image_path = passed_argument
    if os.path.exists(image_path):
        try:
            loaded_image = pygame.image.load(image_path)
        except Exception as e:
            print(f"Error loading image: {e}")
            loaded_image = None
    else:
        loaded_image = None

def update(events):
    global loaded_image

def render(screen):
    # Dark modern background canvas for viewing pictures
    SCREEN_BG = (20, 22, 26)
    PANEL_BG = (30, 35, 45)
    TEXT_LIGHT = (240, 244, 250)

    screen.fill(SCREEN_BG)

    # Draw top control bar
    pygame.draw.rect(screen, PANEL_BG, (210, 80, 1500, 50))
    pygame.draw.line(screen, (50, 55, 65), (210, 130), (1710, 130), 1)

    if loaded_image:
        # Determine image dimensions and center it in the work area
        work_width, work_height = 1500, 850
        work_center_x = 210 + (work_width // 2)
        work_center_y = 130 + (work_height // 2)

        # Keep large photos visible instead of drawing them outside the window.
        image = loaded_image
        max_width, max_height = work_width - 40, work_height - 40
        if image.get_width() > max_width or image.get_height() > max_height:
            scale = min(max_width / image.get_width(), max_height / image.get_height())
            image = pygame.transform.smoothscale(
                image,
                (int(image.get_width() * scale), int(image.get_height() * scale)),
            )

        img_rect = image.get_rect(center=(work_center_x, work_center_y))
        screen.blit(image, img_rect)

        # Display filename at the top
        filename = os.path.basename(image_path)
        title_surface = ui_font.render(f"Viewing: {filename}", True, TEXT_LIGHT)
        screen.blit(title_surface, (230, 95))
    else:
        # Fallback if no image is loaded
        error_surface = ui_font.render("No image loaded or file not found. Please press exit to return.", True, (240, 100, 100))
        screen.blit(error_surface, (230, 95))
if __name__ == "__main__":
    # Initialize standalone window environment
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption("Image Viewer")
    clock = pygame.time.Clock()

    # Check if an image path was passed via command line arguments
    import sys
    if len(sys.argv) > 1:
        load_file(sys.argv[1])

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Close button coordinate check matching your desktop environment
                if pygame.Rect(1800, 20, 40, 40).collidepoint(event.pos):
                    running = False

        # Paint background defaults to white canvas area
        screen.fill((240, 244, 250))

        # Drive the modular core functions
        update(events)
        render(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
