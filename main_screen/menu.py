import os
import pygame

from .Pre_story import BG_COLOR, SCREEN_SIZE, TEXT_COLOR


class MenuScreen:
	def __init__(self, font):
		self.font = font
		self.button_labels = ["Start", "Options", "Quit"]
		self.button_size = (220, 60)
		self.button_gap = 20
		self.button_margin = 30
		self.buttons = self._build_buttons()
		self.background = self._load_background()
		self.title_image = self._load_title_image()
		self.hover_index = -1
		self.button_alpha = 150
		self.button_color = (24, 24, 24)
		self.button_outline = (120, 120, 120)
		self.title_margin_top = 20

	def _load_background(self):
		base_dir = os.path.dirname(__file__)
		image_path = os.path.join(base_dir, "..", "assets", "main_menu.png")
		if os.path.exists(image_path):
			image = pygame.image.load(image_path).convert()
			return pygame.transform.smoothscale(image, SCREEN_SIZE)
		return None

	def _load_title_image(self):
		base_dir = os.path.dirname(__file__)
		image_path = os.path.join(base_dir, "..", "assets", "Name.png")
		if os.path.exists(image_path):
			image = pygame.image.load(image_path).convert_alpha()
			max_width = int(SCREEN_SIZE[0] * 0.6)
			if image.get_width() > max_width:
				scale = max_width / image.get_width()
				new_size = (max_width, int(image.get_height() * scale))
				return pygame.transform.smoothscale(image, new_size)
			return image
		return None

	def _build_buttons(self):
		width, height = self.button_size
		total_height = len(self.button_labels) * height + (len(self.button_labels) - 1) * self.button_gap
		start_y = (SCREEN_SIZE[1] - total_height) // 1.032
		x = SCREEN_SIZE[0] - self.button_margin - width

		buttons = []
		for index, label in enumerate(self.button_labels):
			y = start_y + index * (height + self.button_gap)
			buttons.append((label, pygame.Rect(x, y, width, height)))
		return buttons

	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			for index, (label, rect) in enumerate(self.buttons):
				if rect.collidepoint(event.pos):
					return label.lower()
		return None

	def update(self, now_ms):
		mouse_pos = pygame.mouse.get_pos()
		self.hover_index = -1
		for index, (_, rect) in enumerate(self.buttons):
			if rect.collidepoint(mouse_pos):
				self.hover_index = index
				break
		cursor = pygame.SYSTEM_CURSOR_HAND if self.hover_index != -1 else pygame.SYSTEM_CURSOR_ARROW
		pygame.mouse.set_cursor(cursor)

	def draw(self, screen):
		if self.background:
			screen.blit(self.background, (0, 0))
		else:
			screen.fill(BG_COLOR)
		if self.title_image:
			x = SCREEN_SIZE[0] - self.button_margin - self.title_image.get_width()
			y = self.title_margin_top
			screen.blit(self.title_image, (x, y))
		for index, (label, rect) in enumerate(self.buttons):
			is_hover = index == self.hover_index
			draw_rect = rect.inflate(14, 10) if is_hover else rect
			button_surface = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
			button_surface.fill((*self.button_color, self.button_alpha))
			screen.blit(button_surface, draw_rect.topleft)
			pygame.draw.rect(screen, self.button_outline, draw_rect, 2)
			text_surface = self.font.render(label, True, TEXT_COLOR)
			text_rect = text_surface.get_rect(center=draw_rect.center)
			screen.blit(text_surface, text_rect)
