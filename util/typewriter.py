import pygame
from font import load_font_feather

class Typewriter:
    def __init__(self, text, x, y, font, color, char_delay_ms=50):
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.color = color
        self.char_delay_ms = char_delay_ms
        self.start_time_ms = pygame.time.get_ticks()
        self.finished = False

    def update(self, now_ms):
        elapsed = now_ms - self.start_time_ms
        chars_to_show = elapsed // self.char_delay_ms
        if chars_to_show >= len(self.text):
            self.finished = True

    def draw(self, screen, now_ms=None):
        if now_ms is None:
            now_ms = pygame.time.get_ticks()
        elapsed = now_ms - self.start_time_ms
        chars_to_show = min(len(self.text), elapsed // self.char_delay_ms)
        displayed_text = self.text[:chars_to_show]
        if displayed_text:
            text_surface = self.font.render(displayed_text, True, self.color)
            screen.blit(text_surface, (self.x, self.y))

    def is_finished(self):
        return self.finished

    def reset(self):
        self.start_time_ms = pygame.time.get_ticks()
        self.finished = False

def draw_typewriter_text(screen, text, x, y, font, color, now_ms, char_delay_ms=50):
    chars_to_show = now_ms // char_delay_ms
    displayed_text = text[:chars_to_show]
    if displayed_text:
        text_surface = font.render(displayed_text, True, color)
        screen.blit(text_surface, (x, y))
