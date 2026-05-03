"""
Theme Systems for Code Wars 2025: Invisible + Memory Overload
Shared by Stage 1 and Stage 2
"""

import pygame
from typing import List, Tuple
import math
from collections import deque

class CognitiveLoadManager:
    """
    Manages the Memory Overload theme - tracks cognitive load percentage
    and provides visual/gameplay effects when overloaded
    """
    def __init__(self, start_load=0, max_load=100):
        self.load = start_load
        self.max_load = max_load
        self.overload_threshold = 80  # Effects start at 80%
        self.critical_threshold = 60  # Warning effects at 60%
        
    def update_load(self, change):
        """Add or remove cognitive load"""
        self.load = max(0, min(self.max_load, self.load + change))
        return self.load
        
    def get_load_percentage(self):
        """Get load as percentage (0-100)"""
        return (self.load / self.max_load) * 100
        
    def is_critical(self):
        """Check if at critical levels (60%+)"""
        return self.get_load_percentage() >= self.critical_threshold
        
    def is_overloaded(self):
        """Check if overloaded (80%+)"""
        return self.get_load_percentage() >= self.overload_threshold
        
    def is_game_over(self):
        """Check if cognitive load caused game over"""
        return self.load >= self.max_load
        
    def get_color(self):
        """Get color based on load level"""
        percentage = self.get_load_percentage()
        if percentage < 30:
            return (0, 255, 0)  # Green
        elif percentage < 60:
            return (255, 255, 0)  # Yellow
        elif percentage < 80:
            return (255, 165, 0)  # Orange
        else:
            return (255, 0, 0)  # Red
            
    def draw_meter(self, surface, pos, width=200, height=20, font=None):
        """Draw the cognitive load meter UI"""
        x, y = pos
        
        # Background
        pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))
        
        # Fill bar
        fill_width = int((self.load / self.max_load) * width)
        pygame.draw.rect(surface, self.get_color(), (x, y, fill_width, height))
        
        # Border
        pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)
        
        # Text
        if font:
            text = f"Memory Load: {int(self.get_load_percentage())}%"
            text_surface = font.render(text, True, (255, 255, 255))
            surface.blit(text_surface, (x, y - 25))
            
    def get_screen_shake_intensity(self):
        """Returns shake intensity (0-8 pixels) based on load"""
        if not self.is_critical():
            return 0
        percentage = self.get_load_percentage()
        if percentage < 60:
            return 0
        elif percentage < 80:
            return 2
        elif percentage < 90:
            return 4
        else:
            return 8
            
    def get_speed_multiplier(self):
        """Returns player speed multiplier (0.5-1.0) based on load"""
        if not self.is_overloaded():
            return 1.0
        percentage = self.get_load_percentage()
        # At 80% = 0.9x speed, at 100% = 0.7x speed
        return max(0.7, 1.0 - ((percentage - 80) / 100))


class MemoryTrail:
    """
    Creates fading trail effect for invisible entities
    Shows where enemies were in the past
    """
    def __init__(self, max_length=5, fade_time=2.0, color=(0, 255, 255)):
        self.positions = deque(maxlen=max_length)
        self.fade_time = fade_time  # Seconds for trail to fade
        self.color = color
        self.max_alpha = 200
        
    def add_position(self, pos):
        """Add a new position to the trail"""
        self.positions.append({
            'pos': pos,
            'time': pygame.time.get_ticks()
        })
        
    def update(self):
        """Remove old positions"""
        current_time = pygame.time.get_ticks()
        # Remove positions older than fade_time
        while self.positions and (current_time - self.positions[0]['time']) > (self.fade_time * 1000):
            self.positions.popleft()
            
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the trail with fading effect"""
        current_time = pygame.time.get_ticks()
        
        for i, trail_point in enumerate(self.positions):
            age = (current_time - trail_point['time']) / 1000.0  # Age in seconds
            alpha = int(self.max_alpha * (1 - (age / self.fade_time)))
            alpha = max(0, min(255, alpha))
            
            # Size decreases with age
            size_factor = 1.0 - (age / self.fade_time)
            size = int(20 * size_factor)
            size = max(5, size)
            
            if alpha > 0:
                # Create temporary surface for alpha
                trail_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (*self.color, alpha), (size, size), size)
                
                # Adjust position with camera offset
                draw_pos = (
                    trail_point['pos'][0] - camera_offset[0] - size,
                    trail_point['pos'][1] - camera_offset[1] - size
                )
                surface.blit(trail_surf, draw_pos)


class InvisibilityManager:
    """
    Manages the Invisible theme - handles entity visibility states
    """
    def __init__(self):
        self.visibility_states = {}  # entity_id: {'alpha': int, 'visible': bool, 'timer': float}
        
    def register_entity(self, entity_id, start_visible=True):
        """Register an entity for invisibility tracking"""
        self.visibility_states[entity_id] = {
            'alpha': 255 if start_visible else 50,
            'visible': start_visible,
            'timer': 0,
            'fade_duration': 2.0,  # 2 seconds to fade in/out
            'visible_duration': 3.0,  # Stay visible for 3 seconds
            'invisible_duration': 3.0,  # Stay invisible for 3 seconds
        }
        
    def update(self, entity_id, dt):
        """Update visibility state for an entity"""
        if entity_id not in self.visibility_states:
            return 255
            
        state = self.visibility_states[entity_id]
        state['timer'] += dt
        
        if state['visible']:
            # Entity is visible, check if should start fading out
            if state['timer'] >= state['visible_duration']:
                state['visible'] = False
                state['timer'] = 0
        else:
            # Entity is invisible, check if should start fading in
            if state['timer'] >= state['invisible_duration']:
                state['visible'] = True
                state['timer'] = 0
                
        # Calculate alpha based on transition
        if state['visible']:
            # Fading in
            progress = min(1.0, state['timer'] / state['fade_duration'])
            state['alpha'] = int(50 + (205 * progress))  # 50 to 255
        else:
            # Fading out
            progress = min(1.0, state['timer'] / state['fade_duration'])
            state['alpha'] = int(255 - (205 * progress))  # 255 to 50
            
        return state['alpha']
        
    def get_alpha(self, entity_id):
        """Get current alpha value for entity"""
        if entity_id not in self.visibility_states:
            return 255
        return self.visibility_states[entity_id]['alpha']
        
    def is_visible(self, entity_id):
        """Check if entity is currently visible"""
        if entity_id not in self.visibility_states:
            return True
        return self.visibility_states[entity_id]['alpha'] > 150
        
    def force_visible(self, entity_id, duration=2.0):
        """Force entity to be visible for a duration (memory flash)"""
        if entity_id in self.visibility_states:
            self.visibility_states[entity_id]['alpha'] = 255
            self.visibility_states[entity_id]['visible'] = True
            self.visibility_states[entity_id]['timer'] = -duration  # Negative timer to stay visible


class MemoryFlashEffect:
    """
    Visual effect when memory flash is activated
    Brief white screen flash that reveals all invisible entities
    """
    def __init__(self, duration=0.5):
        self.active = False
        self.duration = duration
        self.timer = 0
        
    def activate(self):
        """Start the flash effect"""
        self.active = True
        self.timer = 0
        
    def update(self, dt):
        """Update the flash timer"""
        if self.active:
            self.timer += dt
            if self.timer >= self.duration:
                self.active = False
                
    def draw(self, surface):
        """Draw the flash overlay"""
        if self.active:
            # Calculate alpha - strong at start, fades out
            progress = self.timer / self.duration
            alpha = int(200 * (1 - progress))
            
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, alpha))
            surface.blit(overlay, (0, 0))


class OverloadVisualEffect:
    """
    Visual effects when cognitive load is high
    Screen shake, vignette, chromatic aberration
    """
    def __init__(self):
        self.shake_offset = (0, 0)
        
    def get_screen_shake(self, intensity):
        """Generate screen shake offset"""
        if intensity <= 0:
            return (0, 0)
        import random
        self.shake_offset = (
            random.randint(-intensity, intensity),
            random.randint(-intensity, intensity)
        )
        return self.shake_offset
        
    def draw_vignette(self, surface, intensity):
        """Draw dark vignette around screen edges"""
        if intensity <= 0:
            return
            
        width, height = surface.get_size()
        
        # Create vignette surface
        vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw multiple rectangles with increasing alpha
        max_alpha = int(150 * (intensity / 100))
        for i in range(5):
            alpha = int(max_alpha * (i / 5))
            border = i * 20
            pygame.draw.rect(vignette, (100, 0, 0, alpha), 
                           (border, border, width - border * 2, height - border * 2), 20)
        
        surface.blit(vignette, (0, 0))


class PatternMemoryChallenge:
    """
    Mini-game: Remember and reproduce a pattern
    Used in both stages as cognitive challenge
    """
    def __init__(self, pattern_length=4, display_time=3.0):
        self.pattern_length = pattern_length
        self.display_time = display_time
        self.pattern = []
        self.player_input = []
        self.showing = False
        self.show_timer = 0
        self.complete = False
        self.success = False
        
    def start(self, pattern_length=None):
        """Start a new pattern challenge"""
        if pattern_length:
            self.pattern_length = pattern_length
            
        # Generate random pattern (could be numbers, colors, positions, etc.)
        import random
        self.pattern = [random.randint(1, 4) for _ in range(self.pattern_length)]
        self.player_input = []
        self.showing = True
        self.show_timer = 0
        self.complete = False
        self.success = False
        
    def update(self, dt):
        """Update the challenge timer"""
        if self.showing:
            self.show_timer += dt
            if self.show_timer >= self.display_time:
                self.showing = False
                
    def add_input(self, value):
        """Player inputs a value"""
        if self.showing or self.complete:
            return
            
        self.player_input.append(value)
        
        # Check if pattern is complete
        if len(self.player_input) >= len(self.pattern):
            self.complete = True
            self.success = self.player_input == self.pattern
            
    def draw(self, surface, font, position):
        """Draw the pattern challenge UI"""
        x, y = position
        
        # Background box
        box_width = 400
        box_height = 200
        box_rect = pygame.Rect(x - box_width // 2, y - box_height // 2, box_width, box_height)
        pygame.draw.rect(surface, (0, 0, 0), box_rect)
        pygame.draw.rect(surface, (255, 255, 255), box_rect, 3)
        
        if self.showing:
            # Show the pattern
            title = font.render("Remember this pattern:", True, (255, 255, 255))
            surface.blit(title, (box_rect.centerx - title.get_width() // 2, box_rect.y + 20))
            
            # Show pattern numbers
            pattern_str = " - ".join(str(n) for n in self.pattern)
            pattern_surf = font.render(pattern_str, True, (255, 215, 0))
            surface.blit(pattern_surf, (box_rect.centerx - pattern_surf.get_width() // 2, box_rect.centery - 10))
            
            # Timer
            time_left = self.display_time - self.show_timer
            timer_surf = font.render(f"Time: {time_left:.1f}s", True, (200, 200, 200))
            surface.blit(timer_surf, (box_rect.centerx - timer_surf.get_width() // 2, box_rect.bottom - 40))
            
        elif not self.complete:
            # Input phase
            title = font.render("Input the pattern (1-4 keys):", True, (255, 255, 255))
            surface.blit(title, (box_rect.centerx - title.get_width() // 2, box_rect.y + 20))
            
            # Show current input
            input_str = " - ".join(str(n) for n in self.player_input)
            if not input_str:
                input_str = "..."
            input_surf = font.render(input_str, True, (0, 255, 255))
            surface.blit(input_surf, (box_rect.centerx - input_surf.get_width() // 2, box_rect.centery - 10))
            
            # Instructions
            inst = font.render(f"({len(self.player_input)}/{len(self.pattern)})", True, (200, 200, 200))
            surface.blit(inst, (box_rect.centerx - inst.get_width() // 2, box_rect.bottom - 40))
            
        else:
            # Show result
            if self.success:
                result = font.render("SUCCESS!", True, (0, 255, 0))
                msg = font.render("Cognitive load reduced!", True, (200, 255, 200))
            else:
                result = font.render("FAILED", True, (255, 0, 0))
                msg = font.render("Cognitive load increased!", True, (255, 200, 200))
                
            surface.blit(result, (box_rect.centerx - result.get_width() // 2, box_rect.y + 50))
            surface.blit(msg, (box_rect.centerx - msg.get_width() // 2, box_rect.centery))


# Utility function for both stages
def apply_invisibility_to_surface(surface, alpha):
    """
    Apply alpha transparency to a surface
    Returns a new surface with applied alpha
    """
    if alpha >= 255:
        return surface
        
    # Create a copy and set alpha
    alpha_surface = surface.copy()
    alpha_surface.set_alpha(alpha)
    return alpha_surface
