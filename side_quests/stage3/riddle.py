import os
import sys

import pygame

if __name__ == "__main__" and __package__ is None:
	project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	sys.path.insert(0, project_root)

from util.const import SCREEN_SIZE
from util.font import load_font_feather
from util.state import State
from util.transition import FadeTransition

TITLE_COLOR = (245, 245, 240)
BODY_COLOR = (230, 230, 220)
ACCENT_COLOR = (140, 220, 140)
ERROR_COLOR = (230, 120, 120)
PANEL_BG = (10, 10, 14, 180)


class RiddleGame(State):
	def __init__(self, screen_size=SCREEN_SIZE):
		super().__init__()
		self.screen_size = screen_size
		self.width, self.height = screen_size
		self.background = self._load_background()
		self.font_title = load_font_feather(34)
		self.font_body = load_font_feather(24)
		self.font_small = load_font_feather(20)
		self.panel_rect = pygame.Rect(40, 40, self.width - 80, self.height - 80)
		self.riddles = self._build_riddles()
		self.current_index = 0
		self.correct_count = 0
		self.feedback = ""
		self.feedback_color = BODY_COLOR
		self.win = False
		self.option_labels = ["A", "B", "C", "D"]
		self.pending_index = None
		self.question_fade = FadeTransition(
			out_ms=240,
			in_ms=240,
			out_alpha=(255, 0),
			in_alpha=(0, 255),
			idle_alpha=255,
		)

	def _load_background(self):
		base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
		image_path = os.path.join(base_dir, "assets", "main_menu.png")
		if os.path.exists(image_path):
			image = pygame.image.load(image_path).convert()
			return pygame.transform.smoothscale(image, SCREEN_SIZE)
		return None

	def _build_riddles(self):
		return [
			{
				"question": "I have hundreds of keys but cannot open a single door. I have 'Space' but no room, and though I allow you to 'Enter', you can never leave. What am I?",
				"options": ["Piano", "Keyboard", "Prison", "Map"],
				"correct": 1,  # A piano has keys but no 'Space' or 'Enter' keys.
			},
			{
				"question": "I am always hungry and must be fed, but if you give me a drink, I’ll quickly be dead. I have no lungs, yet I breathe the very air around you. What am I?",
				"options": ["Human", "Fire", "Engine", "Storm"],
				"correct": 1,  # Humans and engines don't "die" from a single drink; storms aren't "fed" in this literal sense.
			},
			{
				"question": "I have two hands but no arms, and a face but no eyes. I am always running, yet I never leave my spot. What am I?",
				"options": ["Athlete", "River", "Clock", "Waterfall"],
				"correct": 2,  # Rivers and waterfalls don't have "hands" or a "face."
			},
			{
				"question": "I am always coming but never arrive. I am the place where all your 'somedays' live, yet you will never see me today. What am I?",
				"options": ["Yesterday", "The Future", "Tomorrow", "A Dream"],
				"correct": 2,  # "The Future" is a broad concept; "Tomorrow" is the specific noun that technically never arrives (because when it does, it's Today).
			},
			{
				"question": "I follow you all day long, mimicking your every move, yet I have no weight and you can never catch me in the dark. What am I?",
				"options": ["Reflection", "Shadow", "Ghost", "Memory"],
				"correct": 1,  # Reflections require a mirror/surface; shadows are the only ones that "vanish" specifically because of the absence of light.
			},
		]


	def handle_event(self, event):
		if event.type != pygame.KEYDOWN:
			return
		if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and (event.mod & pygame.KMOD_CTRL):
			self.correct_count = len(self.riddles)
			self.win = True
			self.feedback = "Demo complete."
			self.feedback_color = ACCENT_COLOR
			self.done = True
			return
		if event.key == pygame.K_ESCAPE:
			self.quit = True
			return
		if self.question_fade.active:
			return
		if self.win:
			if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
				self.done = True
			return
		if event.key in (pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d):
			index = event.key - pygame.K_a
			self._submit_answer(index)
			return
		if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
			index = event.key - pygame.K_1
			self._submit_answer(index)
			return

	def handle_events(self, events):
		for event in events:
			self.handle_event(event)

	def update(self, dt):
		self.question_fade.update(dt)
		if self.question_fade.should_swap() and self.pending_index is not None:
			self.current_index = self.pending_index
			self.pending_index = None
			self.feedback = ""
			self.feedback_color = BODY_COLOR

	def _submit_answer(self, index):
		current = self.riddles[self.current_index]
		if index == current["correct"]:
			self.correct_count += 1
			self.feedback = "Correct."
			self.feedback_color = ACCENT_COLOR
			if self.correct_count >= len(self.riddles):
				self.win = True
				self.feedback = "You answered all 5 riddles. You win."
			else:
				self.pending_index = self.current_index + 1
				self.question_fade.start(pygame.time.get_ticks())
		else:
			self.feedback = "Wrong answer."
			self.feedback_color = ERROR_COLOR

	def _wrap_text(self, text, font, max_width):
		lines = []
		words = text.split(" ")
		current = ""
		for word in words:
			test = word if not current else f"{current} {word}"
			if font.size(test)[0] <= max_width:
				current = test
			else:
				if current:
					lines.append(current)
				current = word
		if current:
			lines.append(current)
		return lines

	def draw(self, screen):
		if self.background:
			screen.blit(self.background, (0, 0))
		else:
			screen.fill((16, 16, 20))
		panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
		panel.fill(PANEL_BG)
		screen.blit(panel, self.panel_rect.topleft)
		pygame.draw.rect(screen, (160, 160, 160), self.panel_rect, 2)

		now_ms = pygame.time.get_ticks()
		content_alpha = self.question_fade.alpha(now_ms)

		title = self.font_title.render("Eden Riddle Trial", True, TITLE_COLOR)
		title_rect = title.get_rect()
		title_rect.midtop = (self.width // 2, self.panel_rect.top + 14)
		screen.blit(title, title_rect)

		progress_text = f"Correct: {self.correct_count}/5"
		progress = self.font_small.render(progress_text, True, BODY_COLOR)
		screen.blit(progress, (self.panel_rect.left + 18, self.panel_rect.top + 18))

		content_top = title_rect.bottom + 22
		content_left = self.panel_rect.left + 24
		content_width = self.panel_rect.width - 48

		if self.win:
			win_lines = self._wrap_text(self.feedback, self.font_body, content_width)
			y = content_top + 20
			for line in win_lines:
				surface = self.font_body.render(line, True, ACCENT_COLOR)
				screen.blit(surface, (content_left, y))
				y += self.font_body.get_linesize() + 6
			prompt = self.font_small.render("Press Enter to exit", True, BODY_COLOR)
			screen.blit(prompt, (content_left, y + 20))
			return

		current = self.riddles[self.current_index]
		question = current["question"]
		question_lines = self._wrap_text(question, self.font_body, content_width)
		y = content_top
		for line in question_lines:
			surface = self.font_body.render(line, True, BODY_COLOR)
			surface.set_alpha(content_alpha)
			screen.blit(surface, (content_left, y))
			y += self.font_body.get_linesize() + 6
		y += 16
		for index, option in enumerate(current["options"]):
			label = self.option_labels[index]
			option_text = f"{label}. {option}"
			option_lines = self._wrap_text(option_text, self.font_body, content_width)
			for line in option_lines:
				surface = self.font_body.render(line, True, TITLE_COLOR)
				surface.set_alpha(content_alpha)
				screen.blit(surface, (content_left, y))
				y += self.font_body.get_linesize() + 4
			y += 6

		if self.feedback:
			feedback_surface = self.font_small.render(self.feedback, True, self.feedback_color)
			feedback_surface.set_alpha(content_alpha)
			screen.blit(feedback_surface, (content_left, y))

		help_text = "A-D or 1-4 to answer. ESC to quit."
		help_surface = self.font_small.render(help_text, True, BODY_COLOR)
		screen.blit(
			help_surface,
			(content_left, self.panel_rect.bottom - 32),
		)


def run():
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE)
	pygame.display.set_caption("Eden - Riddle Trial")
	clock = pygame.time.Clock()
	game = RiddleGame(SCREEN_SIZE)

	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			else:
				game.handle_event(event)
		game.update(pygame.time.get_ticks())
		game.draw(screen)
		pygame.display.flip()
		clock.tick(60)
		if game.quit or game.done:
			running = False

	pygame.quit()


if __name__ == "__main__":
	run()
