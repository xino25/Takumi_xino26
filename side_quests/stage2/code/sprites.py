from settings import * 
from timer import Timer
from math import sin
import math
from random import randint, uniform
import pygame

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf 
        self.rect = self.image.get_frect(topleft = pos)

class Bullet(Sprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(pos, surf, groups)
        self.image = pygame.transform.flip(self.image, direction == -1, False)
        self.direction = direction
        self.speed = 850
    
    def update(self, dt):
        self.rect.x += self.direction * self.speed * dt

# Enemy bullet classes removed per design request.

class Fire(Sprite):
    def __init__(self, surf, pos, groups, player):
        super().__init__(pos, surf, groups)
        self.player = player 
        self.flip = player.flip
        self.timer = Timer(100, autostart = True, func = self.kill)
        self.y_offset = pygame.Vector2(0,8)
        if self.player.flip:
            self.rect.midright = self.player.rect.midleft + self.y_offset
            self.image = pygame.transform.flip(self.image, True, False)
        else:
            self.rect.midleft = self.player.rect.midright + self.y_offset

    def update(self, _):
        self.timer.update()
        if self.player.flip:
            self.rect.midright = self.player.rect.midleft + self.y_offset
        else:
            self.rect.midleft = self.player.rect.midright + self.y_offset
        if self.flip != self.player.flip:
            self.kill()

class AnimatedSprite(Sprite):
    def __init__(self, frames, pos, groups):
        self.frames, self.frame_index, self.animation_speed = frames, 0, 10
        super().__init__(pos, self.frames[self.frame_index], groups)

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

class Enemy(AnimatedSprite):
    def __init__(self, frames, pos, groups):
        super().__init__(frames, pos, groups)
        self.death_timer = Timer(200, func = self.kill)
        self.health = 1
        self.alpha = 255  # For invisibility system
        self.original_image = None  # Store original for alpha changes
        self.dying = False
        self.death_start = 0
        self.death_duration = 300  # ms fade-out

    def set_alpha(self, alpha):
        """Set transparency level (0-255)"""
        self.alpha = alpha
    
    def destroy(self):
        # Start a fade-out instead of white mask
        if not self.dying:
            self.dying = True
            self.death_start = pygame.time.get_ticks()
            self.animation_speed = 0

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            self.destroy()

    def animate(self, dt):
        """Override to apply alpha after animation and handle fade-out"""
        self.frame_index += self.animation_speed * dt
        base_image = self.frames[int(self.frame_index) % len(self.frames)]
        
        # Apply alpha transparency
        img = base_image.copy()
        img.set_alpha(self.alpha)
        self.image = img

    def update(self, dt):
        # Handle fade-out when dying
        if self.dying:
            elapsed = pygame.time.get_ticks() - self.death_start
            progress = min(1.0, elapsed / self.death_duration)
            self.alpha = int(255 * (1 - progress))
            if progress >= 1.0:
                self.kill()
                return
        
        self.death_timer.update()
        if not self.death_timer and not self.dying:
            self.move(dt)
        self.animate(dt)
        self.constraint()

class TouhouBee(Enemy):
    def __init__(self, frames, pos, groups, speed, player):
        super().__init__(frames, pos, groups)
        self.speed = speed
        self.amplitude = randint(300, 400)
        self.frequency = randint(200, 400)
        self.player = player
        # Shooting removed

    def move(self, dt):
        self.rect.x -= self.speed * dt
        self.rect.y += sin(pygame.time.get_ticks() / self.frequency) * self.amplitude * dt
    
    def update(self, dt):
        super().update(dt)
    
    def constraint(self):
        if self.rect.right <= 0:
            self.kill()


class Bee(Enemy):
    def __init__(self, frames, pos, groups, speed):
        super().__init__(frames, pos, groups)
        self.speed = speed
        self.amplitude = randint(500,600)
        self.frequency = randint(300,600)

    def move(self, dt):
        self.rect.x -= self.speed * dt
        self.rect.y += sin(pygame.time.get_ticks() / self.frequency) * self.amplitude * dt
    
    def constraint(self):
        if self.rect.right <= 0:
            self.kill()

class Worm(Enemy):
    def __init__(self, frames, rect, groups):
        super().__init__(frames, rect.topleft, groups)
        self.rect.bottomleft = rect.bottomleft
        self.main_rect = rect
        self.speed = randint(160,200)
        self.direction = 1
    
    def move(self, dt):
        self.rect.x += self.direction * self.speed * dt

    def constraint(self):
        if not self.main_rect.contains(self.rect):
            self.direction *= -1
            self.frames = [pygame.transform.flip(surf, True, False) for surf in self.frames]

class SequenceBee(Enemy):
    """Moving bee used for sequence memory gameplay"""
    def __init__(self, frames, pos, groups, index, player):
        super().__init__(frames, pos, groups)
        self.index = index
        self.highlight = False
        self.base_alpha = 255
        self.alpha = self.base_alpha
        self.scale_factor = 1.0
        self.player = player
        self.speed = randint(100, 200)
        self.amplitude = randint(300, 400)
        self.frequency = randint(200, 400)
        self.movement_enabled = True  # Disabled during SHOW phase
        self.highlight_start = 0
        self.highlight_period = 600  # ms (300ms down, 300ms up) similar to death

    def set_highlight(self, active: bool):
        self.highlight = active
        # Use fade animation like death but looping; no scale or glow
        self.scale_factor = 1.0
        if active:
            self.highlight_start = pygame.time.get_ticks()

    def move(self, dt):
        # Pause movement during SHOW phase (controlled from main via flag)
        if not getattr(self, 'movement_enabled', True):
            return
        
        # If bee has a target_position (during SPAWNING), move to it instead of chasing
        if hasattr(self, 'target_position') and self.target_position:
            dx = self.target_position[0] - self.rect.centerx
            dy = self.target_position[1] - self.rect.centery
            distance = (dx**2 + dy**2)**0.5
            
            if distance > 5:  # Not yet at target
                move_speed = self.speed * 1.5  # Move faster during spawn-in
                self.rect.x += (dx / distance) * move_speed * dt
                self.rect.y += (dy / distance) * move_speed * dt
            else:
                # Reached target, clear it to enable chase behavior
                self.target_position = None
            return
        
        # Chase the player aggressively (normal INPUT phase behavior)
        if self.player and hasattr(self.player, 'rect'):
            # Calculate direction to player
            dx = self.player.rect.centerx - self.rect.centerx
            dy = self.player.rect.centery - self.rect.centery
            distance = (dx**2 + dy**2)**0.5
            
            if distance > 0:
                # Normalize and move toward player
                self.rect.x += (dx / distance) * self.speed * dt
                self.rect.y += (dy / distance) * self.speed * dt

    def animate(self, dt):
        # If dying, use base class fade-out logic
        if getattr(self, 'dying', False):
            return super().animate(dt)

        # Animate frames and apply death-like fade loop when highlighted
        self.frame_index += self.animation_speed * dt
        base_image = self.frames[int(self.frame_index) % len(self.frames)]
        img = base_image.copy()

        if self.highlight:
            now = pygame.time.get_ticks()
            elapsed = (now - self.highlight_start) % max(1, self.highlight_period)
            half = self.highlight_period / 2
            if elapsed <= half:
                # Fade out 255 -> 0 over first half
                alpha = int(255 * (1 - (elapsed / half)))
            else:
                # Fade in 0 -> 255 over second half
                alpha = int(255 * ((elapsed - half) / half))
            alpha = max(0, min(255, alpha))
            img.set_alpha(alpha)
        else:
            img.set_alpha(255)

        self.image = img

    def constraint(self):
        # Do not wrap or auto-kill; allow bees to roam the map and keep chasing
        # Intentionally left empty to avoid unintended respawn/wrap behavior when player moves far
        return

class Player(AnimatedSprite):
    def __init__(self, pos, groups, collision_sprites, frames, create_bullet):
        super().__init__(frames, pos, groups)
        self.flip = False
        self.create_bullet = create_bullet
        self.direction = pygame.Vector2()
        self.collision_sprites = collision_sprites
        self.speed = 300
        self.gravity = 50
        self.on_floor = False
        self.jump_count = 0
        self.max_jumps = 2
        self.jump_strength = -20
        self.space_pressed = False
        self.shoot_timer = Timer(200)
        self.hitbox_radius = 3
    
    def get_hitbox_center(self):
        return self.rect.center

    def input(self):
        mouse = pygame.mouse.get_pressed()[0]
        keys = pygame.key.get_pressed()
        self.direction.x = 0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
        if keys[pygame.K_LSHIFT]:
            self.speed = 150
        else:
            self.speed = 300
        if keys[pygame.K_SPACE]:
            if not self.space_pressed and self.jump_count < self.max_jumps:
                self.direction.y = self.jump_strength
                self.jump_count += 1
                self.space_pressed = True
        else:
            self.space_pressed = False
        if (keys[pygame.K_s] or mouse) and not self.shoot_timer:
            self.create_bullet(self.rect.center, -1 if self.flip else 1)
            self.shoot_timer.activate()

    def move(self, dt):
        self.rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.direction.y += self.gravity * dt
        self.rect.y += self.direction.y
        self.collision('vertical')

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.rect.right = sprite.rect.left
                    if self.direction.x < 0: self.rect.left = sprite.rect.right
                if direction == 'vertical':
                    if self.direction.y > 0: self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0: self.rect.top = sprite.rect.bottom
                    self.direction.y = 0

    def check_floor(self):
        bottom_rect = pygame.FRect((0,0), (self.rect.width, 2)).move_to(midtop = self.rect.midbottom)
        was_on_floor = self.on_floor
        self.on_floor = True if bottom_rect.collidelist([sprite.rect for sprite in self.collision_sprites]) >= 0 else False
        if self.on_floor and not was_on_floor:
            self.jump_count = 0

    def animate(self, dt):
        if self.direction.x:
            self.frame_index += self.animation_speed * dt
            self.flip = self.direction.x < 0
        else:
            self.frame_index = 0
        self.frame_index = 1 if not self.on_floor else self.frame_index
        self.image = self.frames[int(self.frame_index) % len(self.frames)]
        self.image = pygame.transform.flip(self.image, self.flip, False)

    def update(self, dt):
        self.shoot_timer.update()
        self.check_floor()
        self.input()
        self.move(dt)
        self.animate(dt)