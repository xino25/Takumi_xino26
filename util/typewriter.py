import pygame
from font import load_font_feather


class Typewriter:
    """A pygame typewriter effect for displaying text character by character."""

    def __init__(self, text, x, y, font, color, char_delay_ms=50):
        """
        Initialize the typewriter.
        """
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.color = color
        self.char_delay_ms = char_delay_ms
        self.start_time_ms = pygame.time.get_ticks()
        self.finished = False

    def update(self, now_ms):
        """Update the typewriter state."""
        elapsed = now_ms - self.start_time_ms
        chars_to_show = elapsed // self.char_delay_ms
        if chars_to_show >= len(self.text):
            self.finished = True

    def draw(self, screen, now_ms=None):
        """
        Draw the typewriter text on the screen.

        """
        if now_ms is None:
            now_ms = pygame.time.get_ticks()

        elapsed = now_ms - self.start_time_ms
        chars_to_show = min(len(self.text), elapsed // self.char_delay_ms)
        displayed_text = self.text[:chars_to_show]

        if displayed_text:
            text_surface = self.font.render(displayed_text, True, self.color)
            screen.blit(text_surface, (self.x, self.y))

    def is_finished(self):
        """Returns True if all characters have been displayed."""
        return self.finished

    def reset(self):
        """Reset the typewriter to the beginning."""
        self.start_time_ms = pygame.time.get_ticks()
        self.finished = False


def draw_typewriter_text(screen, text, x, y, font, color, now_ms, char_delay_ms=50):
    """
    Draw typewriter text directly without maintaining state.
    """
    chars_to_show = now_ms // char_delay_ms
    displayed_text = text[:chars_to_show]

    if displayed_text:
        text_surface = font.render(displayed_text, True, color)
        screen.blit(text_surface, (x, y))



        
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Typewriter Test")
    clock = pygame.time.Clock()

    font = load_font_feather(32)
    typewriter = Typewriter(
        "The quick brown fox jumps over the lazy dog. This is a typewriter effect test!",
        x=50,
        y=100,
        font=font,
        color=(255, 255, 255),
        char_delay_ms=50,
    )

    running = True
    start_time = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                typewriter.reset()

        now_ms = pygame.time.get_ticks() - start_time
        typewriter.update(now_ms)

        screen.fill((20, 20, 20))

        # Draw status info
        status_font = pygame.font.SysFont(None, 24)
        status_text = (
            f"{'[FINISHED]' if typewriter.is_finished() else '[TYPING...]'} "
            f"| Press R to reset | Press Q to quit"
        )
        status_surface = status_font.render(status_text, True, (100, 200, 100))
        screen.blit(status_surface, (50, 50))

        typewriter.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
