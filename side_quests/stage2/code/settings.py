import pygame
from os import walk
from os.path import join
from pytmx.util_pygame import load_pygame

WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720
TILE_SIZE = 64 
FRAMERATE = 60
BG_COLOR = '#fcdfcd'

# Scale for the player sprite frames (e.g., 0.5 = 50%)
PLAYER_SCALE = 0.06
