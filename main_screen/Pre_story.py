import os
import pygame

from util.transition import FadeTransition


SCREEN_SIZE = (800, 600)
BG_COLOR = (12, 12, 12)
TEXT_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (255, 255, 255, 160)
HIGHLIGHT_PADDING = 12
FONT_SIZE = 30
TYPE_INTERVAL_MS = 10
HOLD_MS = 120
BLINK_INTERVAL_MS = 250




class PreStoryScreen:
	def __init__(self, font):
		self.font = font
		self.line1 = (
			"The city known for its hazardous air, water scarcity, and "
			"mountains of garbage."
		)
		self.line2 = (
			"But what most don’t know… it was once Eden, a haven of green. "
			"But due to years of industrialisation and indiscriminate use of limited "
			"resources - now, it was a land where the rich threw gold for leisure "
			"while thousands starved on the streets.\n\n"
		)
		self.state = "title"
		self.typed_count = 0
		self.last_char_ms = 0
		self.state_start_ms = pygame.time.get_ticks()
		self.typing_start_ms = self.state_start_ms
		self.await_enter = True
		self.line2_typed_count = 0
		self.line2_typing_start = 0
		self.continue_blink_start = 0
		self.done = False
		self.background = self._load_background()
		self.text_margin = 60
		self.line_gap = 6
		self.pending_state = None
		self.text_fade = FadeTransition(
			out_ms=220,
			in_ms=220,
			out_alpha=(255, 0),
			in_alpha=(0, 255),
			idle_alpha=255,
		)
		self.title_image = self._load_title()

	def _load_background(self):
		base_dir = os.path.dirname(__file__)
		image_path = os.path.join(base_dir, "..", "assets", "pre_story.png")
		if os.path.exists(image_path):
			image = pygame.image.load(image_path).convert()
			return pygame.transform.smoothscale(image, SCREEN_SIZE)
		return None

	def _load_title(self):
		base_dir = os.path.dirname(__file__)
		image_path = os.path.join(base_dir, "..", "assets", "title.png")
		if os.path.exists(image_path):
			image = pygame.image.load(image_path).convert_alpha()
			target_width = int(SCREEN_SIZE[0] * 0.75)
			scale = target_width / image.get_width()
			new_size = (target_width, int(image.get_height() * scale))
			return pygame.transform.smoothscale(image, new_size)
		return None

	def _calc_typed_count(self, start_ms, text, now_ms):
		elapsed = now_ms - start_ms
		max_chars = len(text)
		return min(max_chars, elapsed // TYPE_INTERVAL_MS)

	def _wrap_text(self, text, max_width):
		lines = []
		for paragraph in text.split("\n"):
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
			if paragraph != text.split("\n")[-1]:
				lines.append("")
		return lines

	def _draw_text_block(self, screen, text, alpha=255, top_y=None):
		max_width = SCREEN_SIZE[0] - self.text_margin * 2
		lines = self._wrap_text(text, max_width)
		line_height = self.font.get_linesize()
		block_height = len(lines) * line_height + (len(lines) - 1) * self.line_gap
		x = self.text_margin
		if top_y is None:
			y = (SCREEN_SIZE[1] - block_height) // 2
		else:
			y = top_y
		max_line_width = max((self.font.size(line)[0] for line in lines if line), default=0)
		highlight_width = max_line_width + HIGHLIGHT_PADDING * 2
		highlight_height = block_height + HIGHLIGHT_PADDING * 2
		block_surface = pygame.Surface((highlight_width, highlight_height), pygame.SRCALPHA)
		block_surface.fill(HIGHLIGHT_COLOR)
		text_x = HIGHLIGHT_PADDING
		text_y = HIGHLIGHT_PADDING
		for line in lines:
			if line:
				surface = self.font.render(line, True, TEXT_COLOR)
				block_surface.blit(surface, (text_x, text_y))
			text_y += line_height + self.line_gap
		block_surface.set_alpha(alpha)
		screen.blit(block_surface, (x - HIGHLIGHT_PADDING, y - HIGHLIGHT_PADDING))

	def update(self, now_ms):
		self.text_fade.update(now_ms)
		if self.text_fade.should_swap() and self.pending_state == "screen2":
			self.state = "screen2"
			self.state_start_ms = now_ms
			self.line2_typing_start = now_ms
			self.line2_typed_count = 0
			self.pending_state = None
			self.await_enter = False
			self.continue_blink_start = now_ms
		if self.state == "title":
			return
		elif self.state == "screen1":
			should_be = self._calc_typed_count(self.typing_start_ms, self.line1, now_ms)
			if should_be > self.typed_count:
				self.typed_count = should_be
				self.last_char_ms = now_ms
			if self.typed_count >= len(self.line1) and not self.await_enter:
				self.await_enter = True
				self.continue_blink_start = now_ms
		elif self.state == "screen2":
			self.line2_typed_count = self._calc_typed_count(
				self.line2_typing_start, self.line2, now_ms
			)
			if self.line2_typed_count >= len(self.line2) and not self.await_enter:
				self.await_enter = True
				self.continue_blink_start = now_ms

	def handle_event(self, event):
		if self.await_enter and event.type == pygame.KEYDOWN:
			if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
				if self.state == "title":
					self.state = "screen1"
					self.await_enter = False
					self.state_start_ms = pygame.time.get_ticks()
					self.typing_start_ms = self.state_start_ms
					self.typed_count = 0
					self.last_char_ms = 0
				elif self.state == "screen1":
					if not self.text_fade.active:
						now = pygame.time.get_ticks()
						self.pending_state = "screen2"
						self.text_fade.start(now)
						self.await_enter = False
				elif self.state == "screen2":
					self.await_enter = False
					self.done = True

	def is_done(self):
		return self.done

	def draw(self, screen):
		if self.background:
			screen.blit(self.background, (0, 0))
		else:
			screen.fill(BG_COLOR)
		now_ms = pygame.time.get_ticks()
		text_alpha = self.text_fade.alpha(now_ms)
		blink_visible = (now_ms - self.continue_blink_start) % (BLINK_INTERVAL_MS * 2) < BLINK_INTERVAL_MS

		if self.state == "screen1":
			text = self.line1[: self.typed_count]
			if text:
				self._draw_text_block(screen, text, text_alpha)
			else:
				self._draw_text_block(screen, text, text_alpha)
			if self.await_enter and self.typed_count >= len(self.line1) and blink_visible:
				continue_font = pygame.font.SysFont(None, 24, bold=True)
				continue_text = continue_font.render("Press Enter to continue", True, TEXT_COLOR)
				continue_text.set_alpha(text_alpha)
				continue_rect = continue_text.get_rect()
				continue_rect.centerx = SCREEN_SIZE[0] // 2
				continue_rect.bottom = SCREEN_SIZE[1] - 30
				screen.blit(continue_text, continue_rect)
		elif self.state == "screen2":
			text = self.line2[: self.line2_typed_count]
			if text:
				self._draw_text_block(screen, text, text_alpha)
			if self.await_enter and self.line2_typed_count >= len(self.line2) and blink_visible:
				continue_font = pygame.font.SysFont(None, 24, bold=True)
				continue_text = continue_font.render("Press Enter to continue", True, TEXT_COLOR)
				continue_text.set_alpha(text_alpha)
				continue_rect = continue_text.get_rect()
				continue_rect.centerx = SCREEN_SIZE[0] // 2
				continue_rect.bottom = SCREEN_SIZE[1] - 30
				screen.blit(continue_text, continue_rect)
		elif self.state == "title":
			if self.title_image:
				title_rect = self.title_image.get_rect()
				title_rect.center = (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2)
				screen.blit(self.title_image, title_rect)
			if blink_visible:
				continue_font = pygame.font.SysFont(None, 24, bold=True)
				continue_text = continue_font.render("Press Enter to continue", True, TEXT_COLOR)
				continue_text.set_alpha(text_alpha)
				continue_rect = continue_text.get_rect()
				continue_rect.centerx = SCREEN_SIZE[0] // 2
				continue_rect.bottom = SCREEN_SIZE[1] - 30
				screen.blit(continue_text, continue_rect)


def create_pre_story_screen(font):
	return PreStoryScreen(font)
