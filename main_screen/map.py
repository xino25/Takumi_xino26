import os
import pygame

from util.const import SCREEN_SIZE


class MapScreen:
	def __init__(self, font):
		self.font = font
		self.default_text = "Map online. Choose your next route."
		self.text = self.default_text
		self.box_height = 150
		self.box_margin = 24
		self.text_color = (255, 255, 255)
		self.done = False
		self._background = self._load_background()
		self.locations = self._create_locations()
		self.hovered_key = None
		self.selected_key = None
		self.action = None
		self.completed_stages = set()

	def _create_locations(self):
		return [
			{
				"key": "livius",
				"label": "Livius City",
				"stage": "stage2",
				"tooltip": "The virus has taken over our city systems. Press Enter to continue.",
				"pos": (150, 460),
				"color": (220, 70, 70),
			},
			{
				"key": "acanth",
				"label": "Acanth Cave",
				"stage": "stage1",
				"tooltip": "You need to help the underground civilization. Press Enter to continue.",
				"pos": (470, 200),
				"color": (220, 70, 70),
			},
			{
				"key": "cyanor",
				"label": "Cyanor River",
				"stage": "stage3",
				"tooltip": "Solve the riddles to help the river. Press Enter to continue.",
				"pos": (430, 430),
				"color": (220, 70, 70),
			},
		]

	def _get_location_at(self, pos):
		for location in self.locations:
			lx, ly = location["pos"]
			if pygame.Vector2(lx, ly).distance_to(pos) <= 28:
				return location
		return None

	def _is_completed(self, location):
		return location["stage"] in self.completed_stages

	def _load_background(self):
		base_dir = os.path.dirname(os.path.dirname(__file__))
		path = os.path.join(base_dir, "assets", "map.png")
		if os.path.exists(path):
			return pygame.image.load(path).convert()
		return None

	def handle_event(self, event):
		if event.type == pygame.MOUSEMOTION:
			location = self._get_location_at(pygame.Vector2(event.pos))
			self.hovered_key = location["key"] if location else None
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			location = self._get_location_at(pygame.Vector2(event.pos))
			if location:
				if self._is_completed(location):
					self.text = "Route secured. Choose another route."
				else:
					self.selected_key = location["key"]
					self.text = location["tooltip"]
		elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
			if self.selected_key:
				location = next(
					(loc for loc in self.locations if loc["key"] == self.selected_key),
					None,
				)
				if location and not self._is_completed(location):
					self.action = location["stage"]
					self.done = True
			elif self.hovered_key:
				location = next(
					(loc for loc in self.locations if loc["key"] == self.hovered_key),
					None,
				)
				if location:
					if self._is_completed(location):
						self.text = "Route secured. Choose another route."
					else:
						self.selected_key = location["key"]
						self.text = location["tooltip"]
						self.action = location["stage"]
						self.done = True

	def update(self, now_ms):
		if self.hovered_key and not self.selected_key:
			location = next(
				(loc for loc in self.locations if loc["key"] == self.hovered_key),
				None,
			)
			if location:
				if self._is_completed(location):
					self.text = "Route secured. Choose another route."
				else:
					self.text = location["tooltip"]
		elif not self.selected_key:
			self.text = self.default_text

	def is_done(self):
		return self.done

	def pop_action(self):
		action = self.action
		self.action = None
		return action

	def reset(self):
		self.text = self.default_text
		self.done = False
		self.hovered_key = None
		self.selected_key = None
		self.action = None

	def mark_completed(self, stage_key):
		self.completed_stages.add(stage_key)

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
			screen.fill((15, 15, 20))

		box_width = SCREEN_SIZE[0] - self.box_margin * 2
		box_rect = pygame.Rect(
			self.box_margin,
			self.box_margin,
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

		for location in self.locations:
			lx, ly = location["pos"]
			is_hovered = location["key"] == self.hovered_key
			is_selected = location["key"] == self.selected_key
			radius = 10
			color = location.get("color", (255, 220, 140))
			if self._is_completed(location):
				color = (80, 150, 220)
			if is_selected:
				color = (255, 140, 80)
			elif is_hovered:
				color = (255, 200, 100) if not self._is_completed(location) else (120, 190, 240)
			pygame.draw.circle(screen, color, (int(lx), int(ly)), radius)
			pygame.draw.circle(screen, (60, 40, 30), (int(lx), int(ly)), radius, 2)
