import os
import pygame

from util.const import SCREEN_SIZE
from util.transition import FadeTransition


class CutsceneScreen:
	def __init__(self, font):
		self.font = font
		self.text1 = "But the people did not sit quiet."
		self.text2 = """
The SolarPunks - a revolutionary uprising amidst ruin. They had a dream - Returning Eden. A dream that could be reality. A dream that will be reality. 
"""
		self.text3 = "Facing harsh oppression from the brutal dictator Kaanik, they set out to save the common people and restore the ecological balance of their home." 
		self.text4 = "The choice is yours - trip and hide from the obstacles in your way, or face them head on and restore Eden to its former, greener glory." 
		self.texts = [
			self.text1.strip(),
			self.text2.strip(),
			self.text3.strip(),
			self.text4.strip(),
		]
		self.box_height = 160
		self.box_margin = 24
		self.text_color = (255, 255, 255)
		self.logo_margin = 24
		self.logo_hold_ms = 1200
		self.type_interval_ms = 24
		self.text_hold_ms = 1200
		self._background = self._load_background()
		self.done = False
		self._logo = self._load_logo()
		self._logo = self._scale_logo(self._logo)
		self.enter_ms = None
		self.show_text = self._logo is None
		self.text_index = 0
		self.typed_count = 0
		self.typing_start_ms = None
		self.text_hold_start_ms = None
		self.logo_fade = FadeTransition(
			out_ms=500,
			in_ms=500,
			out_alpha=(255, 0),
			in_alpha=(0, 255),
			idle_alpha=255,
		)
		self.text_fade = FadeTransition(
			out_ms=350,
			in_ms=350,
			out_alpha=(255, 0),
			in_alpha=(0, 255),
			idle_alpha=255,
		)

	def _load_background(self):
		base_dir = os.path.dirname(os.path.dirname(__file__))
		path = os.path.join(base_dir, "assets", "cutscene.png")
		if os.path.exists(path):
			return pygame.image.load(path).convert()
		return None

	def _load_logo(self):
		base_dir = os.path.dirname(os.path.dirname(__file__))
		path = os.path.join(base_dir, "assets", "solar_punk.png")
		if os.path.exists(path):
			return pygame.image.load(path).convert_alpha()
		return None

	def _scale_logo(self, logo):
		if not logo:
			return None
		max_width = int(SCREEN_SIZE[0] * 0.8)
		width, height = logo.get_size()
		if width <= max_width:
			return logo
		scale = max_width / width
		new_size = (int(width * scale), int(height * scale))
		return pygame.transform.smoothscale(logo, new_size)

	def reset(self):
		self.enter_ms = None
		self.show_text = self._logo is None
		self.text_index = 0
		self.typed_count = 0
		self.typing_start_ms = None
		self.text_hold_start_ms = None
		self.logo_fade = FadeTransition(
			out_ms=500,
			in_ms=500,
			out_alpha=(255, 0),
			in_alpha=(0, 255),
			idle_alpha=255,
		)
		self.text_fade = FadeTransition(
			out_ms=350,
			in_ms=350,
			out_alpha=(255, 0),
			in_alpha=(0, 255),
			idle_alpha=255,
		)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
			self.done = True
		return None

	def update(self, now_ms):
		if self.enter_ms is None:
			self.enter_ms = now_ms
		if not self.show_text and not self.logo_fade.active:
			if now_ms - self.enter_ms >= self.logo_hold_ms:
				self.logo_fade.start(now_ms)
		self.logo_fade.update(now_ms)
		if self.logo_fade.should_swap():
			self.show_text = True
			self.text_index = 0
			self.typed_count = 0
			self.typing_start_ms = now_ms
			self.text_hold_start_ms = None
			self.text_fade.start(now_ms, phase="in")
		if not self.show_text:
			return

		self.text_fade.update(now_ms)
		if self.typing_start_ms is None:
			self.typing_start_ms = now_ms
		current_text = self.texts[self.text_index]
		elapsed = now_ms - self.typing_start_ms
		self.typed_count = min(len(current_text), elapsed // self.type_interval_ms)

		if self.typed_count >= len(current_text):
			if self.text_hold_start_ms is None:
				self.text_hold_start_ms = now_ms
			if self.text_index < len(self.texts) - 1:
				if (
					not self.text_fade.active
					and now_ms - self.text_hold_start_ms >= self.text_hold_ms
				):
					self.text_fade.start(now_ms)
				if self.text_fade.should_swap():
					self.text_index += 1
					self.typing_start_ms = now_ms
					self.typed_count = 0
					self.text_hold_start_ms = None

	def is_done(self):
		return self.done

	def _wrap_text(self, text, max_width):
		lines = []
		paragraphs = text.split("\n")
		for index, paragraph in enumerate(paragraphs):
			words = paragraph.split(" ")
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
			if index < len(paragraphs) - 1:
				lines.append("")
		return lines

	def draw(self, screen):
		if self._background:
			bg = pygame.transform.smoothscale(self._background, SCREEN_SIZE)
			screen.blit(bg, (0, 0))
		else:
			screen.fill((0, 0, 0))

		now_ms = pygame.time.get_ticks()
		logo_alpha = self.logo_fade.alpha(now_ms)
		if self._logo and not self.show_text:
			logo = self._logo.copy()
			logo.set_alpha(logo_alpha)
			logo_rect = logo.get_rect()
			logo_rect.midbottom = (
				SCREEN_SIZE[0] // 2,
				SCREEN_SIZE[1] - self.logo_margin,
			)
			screen.blit(logo, logo_rect)
			return
		box_width = SCREEN_SIZE[0] - self.box_margin * 2
		box_rect = pygame.Rect(
			self.box_margin,
			SCREEN_SIZE[1] - self.box_height - self.box_margin,
			box_width,
			self.box_height,
		)
		text_alpha = self.text_fade.alpha(now_ms) if self.show_text else 0
		box_alpha = int(170 * (text_alpha / 255)) if text_alpha > 0 else 0
		box_surface = pygame.Surface(box_rect.size, pygame.SRCALPHA)
		box_surface.fill((0, 0, 0, box_alpha))
		screen.blit(box_surface, box_rect.topleft)
		if box_alpha > 0:
			border = pygame.Surface(box_rect.size, pygame.SRCALPHA)
			border.fill((0, 0, 0, 0))
			pygame.draw.rect(border, (255, 255, 255, box_alpha), border.get_rect(), 2)
			screen.blit(border, box_rect.topleft)

		max_width = box_rect.width - 24
		current_text = self.texts[self.text_index][: self.typed_count]
		lines = self._wrap_text(current_text, max_width)
		x = box_rect.left + 12
		y = box_rect.top + 12
		line_height = self.font.get_linesize()
		for line in lines:
			surface = self.font.render(line, True, self.text_color)
			surface.set_alpha(text_alpha)
			screen.blit(surface, (x, y))
			y += line_height + 4
