import pygame, os

def load_font_feather(size):
	base_dir = os.path.dirname(__file__)
	font_path = os.path.join(base_dir, "..", "assets", "Feathergraphy_Clean.ttf")
	if os.path.exists(font_path):
		return pygame.font.Font(font_path, size)
	return pygame.font.SysFont(None, size)
