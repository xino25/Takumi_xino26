import os
import pygame

from util.const import SCREEN_SIZE


class Cutscene2Screen:
	def __init__(self, font):
		self.font = font
		self.text = (
			"The truth was undeniable - billions suffered under the whims of one "
			"billionaire - Kaanik. His Party had divided society into the \"haves\" "
			"and \"have-nots\" - and ruling at the top was Kaanik."
		)
		self.box_height = 160
		self.box_margin = 24
		self.text_color = (255, 255, 255)
		self._background = self._load_background()
		self.done = False

	def _load_background(self):
		base_dir = os.path.dirname(os.path.dirname(__file__))
		path = os.path.join(base_dir, "assets", "cutscene2.png")
		if os.path.exists(path):
			return pygame.image.load(path).convert()
		fallback = os.path.join(base_dir, "assets", "cutscene.png")
		if os.path.exists(fallback):
			return pygame.image.load(fallback).convert()
		return None

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
			self.done = True
		return None

	def reset(self):
		self.done = False

	def update(self, now_ms):
		pass

	def is_done(self):
		return self.done

	def _wrap_text(self, text, max_width):
		lines = []
		words = text.split(" ")
		current = ""
		for word in words:
			test = word if not current else f"{current} {word}"
			if self.font.size(test)[0] <= max_width:
				current = test
			else:
				if current:
					lines.append(current)
				current = word
		if current:
			lines.append(current)
		return lines

	def draw(self, screen):
		if self._background:
			bg = pygame.transform.smoothscale(self._background, SCREEN_SIZE)
			screen.blit(bg, (0, 0))
		else:
			screen.fill((0, 0, 0))
		box_width = SCREEN_SIZE[0] - self.box_margin * 2
		box_rect = pygame.Rect(
			self.box_margin,
			SCREEN_SIZE[1] - self.box_height - self.box_margin,
			box_width,
			self.box_height,
		)
		box_surface = pygame.Surface(box_rect.size, pygame.SRCALPHA)
		box_surface.fill((0, 0, 0, 170))
		screen.blit(box_surface, box_rect.topleft)
		pygame.draw.rect(screen, (255, 255, 255), box_rect, 2)

		max_width = box_rect.width - 24
		lines = self._wrap_text(self.text, max_width)
		x = box_rect.left + 12
		y = box_rect.top + 12
		line_height = self.font.get_linesize()
		for line in lines:
			surface = self.font.render(line, True, self.text_color)
			screen.blit(surface, (x, y))
			y += line_height + 4
