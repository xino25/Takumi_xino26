import os
import sys
import pygame

from main_screen.Pre_story import SCREEN_SIZE, create_pre_story_screen
from util.font import load_font_feather
from util.transition import FadeTransition
from main_screen.menu import MenuScreen
from main_screen.cutscene import CutsceneScreen
from main_screen.cutscene2 import Cutscene2Screen
from main_screen.ending_cutscene import EndingCutsceneScreen
from main_screen.map import MapScreen
from side_quests.stage1.solar import create_solar_quest
from side_quests.stage3.main import Stage3Screen

BASE_DIR = os.path.dirname(__file__)
STAGE2_CODE_DIR = os.path.join(BASE_DIR, "side_quests", "stage2", "code")
if STAGE2_CODE_DIR not in sys.path:
	sys.path.insert(0, STAGE2_CODE_DIR)

from side_quests.stage2.code import settings as stage2_settings
from side_quests.stage2.code.main import Game as Stage2Game

FADE_OUT_MS = 500
FADE_IN_MS = 500


def main():
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE)
	pygame.display.set_caption("Eden")
	clock = pygame.time.Clock()

	font = load_font_feather(32)
	pre_story = create_pre_story_screen(font)
	menu_screen = MenuScreen(font)
	cutscene_screen = CutsceneScreen(font)
	cutscene2_screen = Cutscene2Screen(font)
	ending_cutscene_screen = EndingCutsceneScreen(font)
	map_screen = MapScreen(font)
	active_screen = "pre_story"
	stage1 = None
	stage2 = None
	stage3 = None
	stage2_surface = None
	exiting_stage = None
	transition = {
		"active": False,
		"from": None,
		"to": None,
	}
	screen_fade = FadeTransition(out_ms=FADE_OUT_MS, in_ms=FADE_IN_MS, color=(0, 0, 0))
	base_dir = BASE_DIR
	menu_music_path = os.path.join(base_dir, "assets", "music 1.mp3")
	music_state = None

	def start_transition(from_screen, to_screen, now_ms):
		transition["active"] = True
		transition["from"] = from_screen
		transition["to"] = to_screen
		screen_fade.start(now_ms)

	def all_stages_completed():
		return len(map_screen.completed_stages) == 3

	def set_music_state(state):
		nonlocal music_state
		if state == music_state:
			return
		music_state = state
		if state == "story_menu":
			if os.path.exists(menu_music_path):
				try:
					pygame.mixer.music.load(menu_music_path)
					pygame.mixer.music.play(-1)
				except pygame.error:
					pass
		else:
			try:
				pygame.mixer.music.stop()
			except pygame.error:
				pass

	def start_stage(stage_key, now_ms):
		nonlocal stage1, stage2, stage3, stage2_surface
		if stage_key == "stage1":
			stage1 = create_solar_quest()
			stage2 = None
			stage3 = None
			stage2_surface = None
		elif stage_key == "stage2":
			stage2_surface = pygame.Surface(
				(stage2_settings.WINDOW_WIDTH, stage2_settings.WINDOW_HEIGHT)
			)
			stage2 = Stage2Game(display_surface=stage2_surface, auto_return=True)
			stage1 = None
			stage3 = None
		elif stage_key == "stage3":
			stage3 = Stage3Screen()
			stage1 = None
			stage2 = None
			stage2_surface = None
		map_screen.reset()
		start_transition("map", stage_key, now_ms)

	running = True
	while running:
		dt = clock.tick(60) / 1000
		now_ms = pygame.time.get_ticks()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			if transition["active"]:
				continue
			if active_screen == "pre_story":
				pre_story.handle_event(event)
			elif active_screen == "menu":
				action = menu_screen.handle_event(event)
				if action == "quit":
					running = False
				elif action == "start":
					cutscene_screen.reset()
					start_transition("menu", "cutscene", now_ms)
			elif active_screen == "cutscene":
				cutscene_screen.handle_event(event)
			elif active_screen == "cutscene2":
				cutscene2_screen.handle_event(event)
			elif active_screen == "ending_cutscene":
				ending_cutscene_screen.handle_event(event)
			elif active_screen == "map":
				map_screen.handle_event(event)
			elif active_screen == "stage1" and stage1:
				stage1.handle_event(event)
			elif active_screen == "stage2" and stage2:
				stage2.handle_event(event)
			elif active_screen == "stage3" and stage3:
				stage3.handle_event(event)

		if active_screen in ("pre_story", "menu"):
			set_music_state("story_menu")
		else:
			set_music_state(None)

		if transition["active"]:
			screen_fade.update(now_ms)
			if screen_fade.should_swap():
				active_screen = transition["to"]
			if not screen_fade.active:
				transition["active"] = False
				transition["from"] = None
				transition["to"] = None
				if exiting_stage and active_screen == "map":
					if exiting_stage == "stage1":
						stage1 = None
					elif exiting_stage == "stage2":
						stage2 = None
						stage2_surface = None
					elif exiting_stage == "stage3":
						stage3 = None
					exiting_stage = None

		screen_to_draw = active_screen
		if transition["active"]:
			if screen_fade.phase == "out":
				screen_to_draw = transition["from"]
			elif screen_fade.phase == "in":
				screen_to_draw = transition["to"]

		if screen_to_draw == "pre_story":
			pre_story.update(now_ms)
			if pre_story.is_done() and not transition["active"]:
				start_transition("pre_story", "menu", now_ms)
			pre_story.draw(screen)
		elif screen_to_draw == "menu":
			menu_screen.update(now_ms)
			menu_screen.draw(screen)
		elif screen_to_draw == "cutscene":
			cutscene_screen.update(now_ms)
			if cutscene_screen.is_done() and not transition["active"]:
				cutscene2_screen.reset()
				start_transition("cutscene", "cutscene2", now_ms)
			cutscene_screen.draw(screen)
		elif screen_to_draw == "cutscene2":
			cutscene2_screen.update(now_ms)
			if cutscene2_screen.is_done() and not transition["active"]:
				start_transition("cutscene2", "map", now_ms)
			cutscene2_screen.draw(screen)
		elif screen_to_draw == "ending_cutscene":
			ending_cutscene_screen.update(now_ms)
			if ending_cutscene_screen.is_done() and not transition["active"]:
				start_transition("ending_cutscene", "menu", now_ms)
			ending_cutscene_screen.draw(screen)
		elif screen_to_draw == "map":
			map_screen.update(now_ms)
			map_screen.draw(screen)
			if map_screen.is_done() and not transition["active"]:
				stage = map_screen.pop_action()
				if stage in ("stage1", "stage2", "stage3"):
					start_stage(stage, now_ms)
		elif screen_to_draw == "stage1" and stage1:
			stage1.update(now_ms)
			stage1.draw(screen)
			if (stage1.done or stage1.quit) and not transition["active"]:
				if stage1.done and getattr(stage1, "win", False):
					map_screen.mark_completed("stage1")
				exiting_stage = "stage1"
				map_screen.reset()
				if all_stages_completed():
					ending_cutscene_screen.reset()
					start_transition("stage1", "ending_cutscene", now_ms)
				else:
					start_transition("stage1", "map", now_ms)
		elif screen_to_draw == "stage2" and stage2:
			stage2.step(dt)
			src_size = stage2_surface.get_size() if stage2_surface else screen.get_size()
			target_size = screen.get_size()
			if stage2_surface and src_size != target_size:
				scale = min(target_size[0] / src_size[0], target_size[1] / src_size[1])
				scaled_size = (int(src_size[0] * scale), int(src_size[1] * scale))
				scaled = pygame.transform.smoothscale(stage2_surface, scaled_size)
				screen.fill((0, 0, 0))
				screen.blit(
					scaled,
					((target_size[0] - scaled_size[0]) // 2, (target_size[1] - scaled_size[1]) // 2),
				)
			elif stage2_surface:
				screen.blit(stage2_surface, (0, 0))
			if stage2.done and not transition["active"]:
				if getattr(stage2, "victory", False):
					map_screen.mark_completed("stage2")
				stage2.stop_audio()
				exiting_stage = "stage2"
				map_screen.reset()
				if all_stages_completed():
					ending_cutscene_screen.reset()
					start_transition("stage2", "ending_cutscene", now_ms)
				else:
					start_transition("stage2", "map", now_ms)
		elif screen_to_draw == "stage3" and stage3:
			stage3.update(now_ms)
			stage3.draw(screen)
			if stage3.is_done() and not transition["active"]:
				if stage3.is_completed():
					map_screen.mark_completed("stage3")
				exiting_stage = "stage3"
				map_screen.reset()
				if all_stages_completed():
					ending_cutscene_screen.reset()
					start_transition("stage3", "ending_cutscene", now_ms)
				else:
					start_transition("stage3", "map", now_ms)

		if transition["active"]:
			screen_fade.draw_overlay(screen, now_ms)
		pygame.display.flip()

	pygame.quit()


if __name__ == "__main__":
	main()
