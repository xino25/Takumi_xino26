import os
import sys

import pygame

if __name__ == "__main__" and __package__ is None:
	project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	sys.path.insert(0, project_root)

from util.const import SCREEN_SIZE
from side_quests.stage3.riddle import RiddleGame


class Stage3Screen:
	def __init__(self, window_size=SCREEN_SIZE):
		self.game = RiddleGame(window_size)

	def handle_event(self, event):
		self.game.handle_event(event)

	def update(self, now_ms):
		self.game.update(now_ms)

	def is_done(self):
		return self.game.done or self.game.quit

	def is_completed(self):
		return self.game.win and self.game.done

	def reset(self):
		self.game = RiddleGame(self.game.screen_size)

	def draw(self, screen):
		self.game.draw(screen)


def main():
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE)
	pygame.display.set_caption("Stage 3")
	clock = pygame.time.Clock()
	stage = Stage3Screen(SCREEN_SIZE)

	while not stage.is_done():
		for event in pygame.event.get():
			stage.handle_event(event)

		stage.update(pygame.time.get_ticks())
		stage.draw(screen)
		pygame.display.flip()
		clock.tick(60)

	pygame.quit()


if __name__ == "__main__":
	main()
