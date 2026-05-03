import os
import pygame

from util.const import SCREEN_SIZE


class EndingCutsceneScreen:
	def __init__(self, font):
		self.font = font
		self.dialogue_text = (
			"The truth was undeniable - billions suffered under the whims of one "
			"billionaire - Kaanik. His Party had divided society into the \"haves\" "
			"and \"have-nots\" - and ruling at the top was Kaanik."
		)
		self.ending_text = "This is just the beginning..."
		self.to_be_continued_text = "TO BE CONTINUED"
		self.box_height = 160
		self.box_margin = 24
		self.text_color = (255, 255, 255)
		self._background = self._load_background()
		self.done = False
		self.phase = "dialogue"
		self.phase_timer = 0
		self.dialogue_duration = 3000
		self.to_be_continued_duration = 2000

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
		return None

	def reset(self):
		self.done = False
		self.phase = "dialogue"
		self.phase_timer = 0

	def update(self, now_ms):
		self.phase_timer += 1000 / 60
		
		if self.phase == "dialogue" and self.phase_timer >= self.dialogue_duration:
			self.phase = "to_be_continued"
			self.phase_timer = 0

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

		if self.phase == "dialogue":
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
			lines = self._wrap_text(self.ending_text, max_width)
			x = box_rect.left + 12
			y = box_rect.top + 12
			line_height = self.font.get_linesize()
			for line in lines:
				surface = self.font.render(line, True, self.text_color)
				screen.blit(surface, (x, y))
				y += line_height + 4

		elif self.phase == "to_be_continued":
			screen.fill((0, 0, 0))
			text_surface = self.font.render(self.to_be_continued_text, True, self.text_color)
			text_rect = text_surface.get_rect(center=(SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2))
			screen.blit(text_surface, text_rect)
