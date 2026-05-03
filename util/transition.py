import pygame


class FadeTransition:
	def __init__(
		self,
		out_ms=500,
		in_ms=500,
		out_alpha=(0, 255),
		in_alpha=(255, 0),
		idle_alpha=0,
		color=(0, 0, 0),
	):
		self.out_ms = out_ms
		self.in_ms = in_ms
		self.out_alpha = out_alpha
		self.in_alpha = in_alpha
		self.idle_alpha = idle_alpha
		self.color = color
		self.active = False
		self.phase = None
		self.start_ms = 0
		self._pending_swap = False

	def start(self, now_ms, phase="out"):
		self.active = True
		self.phase = phase
		self.start_ms = now_ms
		self._pending_swap = False

	def update(self, now_ms):
		if not self.active:
			return
		duration = self.out_ms if self.phase == "out" else self.in_ms
		if duration <= 0 or now_ms - self.start_ms >= duration:
			if self.phase == "out":
				self.phase = "in"
				self.start_ms = now_ms
				self._pending_swap = True
			else:
				self.active = False
				self.phase = None

	def should_swap(self):
		if self._pending_swap:
			self._pending_swap = False
			return True
		return False

	def alpha(self, now_ms):
		if not self.active:
			return self.idle_alpha
		duration = self.out_ms if self.phase == "out" else self.in_ms
		if duration <= 0:
			start_alpha, end_alpha = (
				self.out_alpha if self.phase == "out" else self.in_alpha
			)
			return end_alpha
		progress = min(1.0, (now_ms - self.start_ms) / duration)
		start_alpha, end_alpha = (
			self.out_alpha if self.phase == "out" else self.in_alpha
		)
		return int(start_alpha + (end_alpha - start_alpha) * progress)

	def draw_overlay(self, screen, now_ms):
		alpha = self.alpha(now_ms)
		if alpha <= 0:
			return
		overlay = pygame.Surface(screen.get_size())
		overlay.fill(self.color)
		overlay.set_alpha(alpha)
		screen.blit(overlay, (0, 0))
