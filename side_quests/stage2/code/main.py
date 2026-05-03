from settings import * 
from sprites import * 
from groups import AllSprites
from support import * 
from timer import Timer
from theme_systems import *
from random import randint, sample
import sys
import math
import os

class Game:
    def __init__(self, display_surface=None, auto_return=False):
        if not pygame.get_init():
            pygame.init()
        self.owns_display = display_surface is None
        if self.owns_display:
            self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption('stage2')
        else:
            self.display_surface = display_surface
        self.clock = pygame.time.Clock()
        self.running = True
        self.done = False
        self.auto_return = auto_return
        self.auto_return_delay_ms = 1200
        self.completed_at = None

        # Base path rooted at side_quests/stage2
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Fonts and score
        self.score = 0
        self.win_sequence_level = 5
        try:
            self.font = pygame.font.Font(os.path.join(self.base_path, '..', 'fonts', '04B_30__.TTF'), 32)
            self.game_over_font = pygame.font.Font(os.path.join(self.base_path, '..', 'fonts', '04B_30__.TTF'), 64)
            self.title_font = pygame.font.Font(os.path.join(self.base_path, '..', 'fonts', '04B_30__.TTF'), 48)
        except:
            self.font = pygame.font.Font(None, 32)
            self.game_over_font = pygame.font.Font(None, 64)
            self.title_font = pygame.font.Font(None, 48)
        self.game_over = False

        # Sprite groups
        self.all_sprites = AllSprites(self.display_surface)
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        
        # Store worm spawn data for respawning
        self.worm_spawn_data = []

        # Assets and map setup
        self.load_assets()
        self.setup()

        # Sequence gameplay replaces timed spawns
        self.bee_timer = None

        # Player state
        self.max_lives = 3
        self.lives = 3
        self.stored_hearts = 0  # Extra hearts banked on level complete
        self.power = 1
        self.victory = False
        self.invulnerable_timer = Timer(2000)
        self.freeze_timer = Timer(1000)
        self.pending_game_over = False
        # Memory flash meter (continuous resource that drains while active)
        self.memory_flash_active = False
        self.memory_flash_capacity = 90.0  # seconds at 100% (slower drain)
        self.memory_flash_meter = 1.0      # 100% to start (~90s), refills +10% per level after completion

        # Theme Systems (disabled for pure sequence gameplay)
        self.cognitive_load = CognitiveLoadManager(start_load=0, max_load=999999)  # Effectively disabled
        self.overload_effect = OverloadVisualEffect()
        self.invisibility_manager = InvisibilityManager()
        self.memory_flash_effect = MemoryFlashEffect()

        # Pattern challenge (not used in sequence mode)
        self.pattern_challenge = None
        self.pattern_challenge_active = False
        self.waves_completed = 0

        # Sequence memory gameplay state
        self.sequence_mode = True
        self.sequence_level = 1
        self.sequence_bees = []  # list[SequenceBee]
        self.sequence_order = []  # list of indices (order to click)
        self.sequence_state = 'SPAWNING'  # SPAWNING -> SHOW -> INPUT -> NEXT
        self.sequence_show_index = 0
        self.sequence_show_delay = 0.8  # seconds per flash
        self.sequence_show_timer = 0
        self.sequence_input_index = 0
        self.sequence_feedback_timer = 0
        self.max_bees_on_screen = 6
        self.bee_target_positions = []  # Store final positions for spawning transition

        # initialize first level
        self.setup_sequence_level()

        # Player shooting enabled for sequence mode
    
    def create_bee(self):
        # Unused in sequence mode
        return

    def setup_sequence_level(self):
        """Spawn N bees off-screen (right side), then move them into position before SHOW"""
        # Clear only previous sequence bees, not worms
        for b in list(self.sequence_bees):
            b.kill()
        self.sequence_bees.clear()
        
        n = max(1, min(self.max_bees_on_screen, self.sequence_level))
        # Calculate target positions in a grid within the visible window
        margin = 120
        cols = min(3, n)
        rows = (n + cols - 1) // cols
        grid_w = WINDOW_WIDTH - 2 * margin
        grid_h = WINDOW_HEIGHT - 2 * margin
        col_spacing = grid_w // max(1, (cols - 1)) if cols > 1 else 0
        row_spacing = grid_h // max(1, (rows - 1)) if rows > 1 else 0
        
        target_positions = []
        for r in range(rows):
            for c in range(cols):
                target_positions.append((margin + c * col_spacing, margin + r * row_spacing))
        target_positions = target_positions[:n]
        
        # Randomize positions slightly to feel organic
        import random
        jitter = 50
        target_positions = [(x + random.randint(-jitter, jitter), y + random.randint(-jitter, jitter)) for x, y in target_positions]
        self.bee_target_positions = target_positions
        
        # Create bees OFF-SCREEN to the right, then they'll move into position
        for i in range(n):
            target_x, target_y = target_positions[i]
            # Spawn off-screen to the right
            spawn_x = WINDOW_WIDTH + 150 + (i * 100)
            spawn_y = target_y
            bee = SequenceBee(self.bee_frames, (spawn_x, spawn_y), (self.all_sprites, self.enemy_sprites), i, self.player)
            bee.set_highlight(False)
            bee.target_position = (target_x, target_y)
            bee.movement_enabled = True  # Enable movement to reach target
            self.sequence_bees.append(bee)
            
        # Choose order to flash/click
        self.sequence_order = list(range(n))
        random_order = sample(self.sequence_order, k=n)
        self.sequence_order = random_order
        
        # Reset state to SPAWNING (wait for bees to reach positions)
        self.sequence_state = 'SPAWNING'
        self.sequence_show_index = 0
        self.sequence_show_timer = 0
        self.sequence_input_index = 0

    def _get_clicked_bee_index(self, mouse_pos):
        for i, bee in enumerate(self.sequence_bees):
            if bee.alive() and bee.rect.collidepoint(mouse_pos):
                return i
        return None
            
    def create_bullet(self, pos, direction):
        x = pos[0] + direction * 34 if direction == 1 else pos[0] + direction * 34 - self.bullet_surf.get_width()
        Bullet(self.bullet_surf, (x, pos[1]), direction, (self.all_sprites, self.bullet_sprites))
        Fire(self.fire_surf, pos, self.all_sprites, self.player)
        self.audio['shoot'].play()

    def load_assets(self):
        self.player_frames = import_folder(os.path.join(self.base_path, 'images'), 'player')
        # Scale player frames down if needed
        try:
            scale = PLAYER_SCALE if 'PLAYER_SCALE' in globals() else 0.5
        except Exception:
            scale = 0.5
        if scale != 1.0 and self.player_frames:
            scaled_frames = []
            for surf in self.player_frames:
                w, h = surf.get_width(), surf.get_height()
                new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                scaled_frames.append(pygame.transform.smoothscale(surf, new_size))
            self.player_frames = scaled_frames
        self.bullet_surf = import_image(os.path.join(self.base_path, 'images'), 'gun', 'bullet')
        self.fire_surf = import_image(os.path.join(self.base_path, 'images'), 'gun', 'fire')
        
        self.bee_frames = import_folder(os.path.join(self.base_path, 'images'), 'enemies', 'bee')
        self.worm_frames = import_folder(os.path.join(self.base_path, 'images'), 'enemies', 'worm')
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        hearts_dir = os.path.join(base_dir, 'hearts')
        
        self.full_heart = pygame.image.load(os.path.join(hearts_dir, 'full_heart.png')).convert_alpha()
        self.empty_heart = pygame.image.load(os.path.join(hearts_dir, 'empety_heart.png')).convert_alpha()
        
        heart_size = (32, 32)
        self.full_heart = pygame.transform.scale(self.full_heart, heart_size)
        self.empty_heart = pygame.transform.scale(self.empty_heart, heart_size)

        self.audio = {
            'shoot': pygame.mixer.Sound(os.path.join(self.base_path, 'audio', 'shoot.wav')),
            'impact': pygame.mixer.Sound(os.path.join(self.base_path, 'audio', 'impact.ogg')),
            'music': pygame.mixer.Sound(os.path.join(self.base_path, 'audio', 'music.wav')),
        }
        
        for sound in self.audio.values():
            sound.set_volume(0.3)
            
        self.audio['music'].set_volume(0.2)
        self.audio['music'].play(loops=-1)

    def setup(self):
        tmx_map = load_pygame(os.path.join(self.base_path, 'data', 'maps', 'world.tmx'))
        self.level_width = tmx_map.width * tmx_map.tilewidth
        self.level_height = tmx_map.height * tmx_map.tileheight

        for x, y, image in tmx_map.get_layer_by_name('Main').tiles():
            Sprite((x * tmx_map.tilewidth, y * tmx_map.tileheight), image, (self.all_sprites, self.collision_sprites))

        # Optional non-colliding decoration layer (drawn above Main, below entities)
        try:
            for x, y, image in tmx_map.get_layer_by_name('Decoration').tiles():
                # Only add to all_sprites so these don't block movement
                Sprite((x * tmx_map.tilewidth, y * tmx_map.tileheight), image, self.all_sprites)
        except Exception:
            # If the decoration layer doesn't exist, skip gracefully
            pass

        for object in tmx_map.get_layer_by_name('Entities'):
            if object.name == 'Player':
                self.player = Player(pos=(object.x, object.y),
                                   groups=self.all_sprites,
                                   collision_sprites=self.collision_sprites,
                                   frames=self.player_frames,
                                   create_bullet=self.create_bullet)
                self.ground_level = object.y
            elif object.name == 'Worm':
                # Store worm spawn data for respawning
                worm_rect = pygame.FRect(object.x, object.y, object.width, object.height)
                self.worm_spawn_data.append(worm_rect)
                Worm(self.worm_frames, worm_rect, (self.all_sprites, self.enemy_sprites))
    
    def respawn_worms(self):
        """Respawn all worms at their original positions"""
        for worm_rect in self.worm_spawn_data:
            # Check if a worm already exists at this position
            worm_exists = False
            for sprite in self.enemy_sprites:
                if isinstance(sprite, Worm) and sprite.main_rect == worm_rect:
                    worm_exists = True
                    break
            
            # Only spawn if worm doesn't exist
            if not worm_exists:
                Worm(self.worm_frames, worm_rect.copy(), (self.all_sprites, self.enemy_sprites))

    def collision(self):
        # In sequence mode, use bullet collision to kill bees
        if self.bullet_sprites and self.enemy_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.audio['impact'].play()
                    for enemy in collision_sprites:
                        # In sequence mode, ONLY process kills during INPUT phase
                        if hasattr(enemy, 'index'):
                            # This is a sequence bee
                            if self.sequence_state == 'INPUT':
                                expected = self.sequence_order[self.sequence_input_index]
                                if enemy.index == expected:
                                    # Correct bee shot in order!
                                    self.score += (self.sequence_input_index + 1) * 10
                                    enemy.destroy()
                                    self.sequence_input_index += 1
                                    if self.sequence_input_index >= len(self.sequence_order):
                                        completed_level = self.sequence_level
                                        # Level complete: award health/stored heart, advance, and reset bullets/state
                                        if self.lives < self.max_lives:
                                            self.lives += 1
                                        else:
                                            self.stored_hearts += 1
                                        self.sequence_level += 1
                                        if completed_level >= self.win_sequence_level:
                                            self.victory = True
                                            self.game_over = True
                                            return
                                        # Restore 10% memory meter on level completion
                                        self.memory_flash_meter = min(1.0, self.memory_flash_meter + 0.10)
                                        # Respawn all worms
                                        self.respawn_worms()
                                        # Clear any remaining bullets to avoid instant hits on next level
                                        for b in list(self.bullet_sprites):
                                            b.kill()
                                        self.setup_sequence_level()
                                        return  # Exit collision processing this frame
                                else:
                                    # WRONG ORDER: Kill the bee but restart the level
                                    enemy.destroy()
                                    # Clear only sequence bees (not worms) and restart the same level
                                    for b in list(self.sequence_bees):
                                        b.kill()
                                    for b in list(self.bullet_sprites):
                                        b.kill()
                                    self.setup_sequence_level()  # Restart same level
                                    return  # Exit collision processing
                            # else: During SPAWNING or SHOW, bullets hit bees but don't kill them
                        else:
                            # Non-sequence enemy (like worms)
                            enemy.destroy()
                            self.score += 10
                    bullet.kill()
        
        # Player collision with enemies
        if not self.invulnerable_timer:
            collision_sprites = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask)
            if collision_sprites:
                self.player_hit()
        # In sequence mode, bees persist even during invulnerability
        # (so they can be shot in the correct order; no auto-destroy)
    
    def player_hit(self):
        self.lives -= 1
        self.invulnerable_timer.activate()
        self.freeze_timer.activate()  # Activate freeze effect
        self.audio['impact'].play()
        
        if self.lives <= 0:
            self.pending_game_over = True  # Mark for game over after freeze
    
    def activate_memory_flash(self):
        """Activate memory flash (now toggled via meter).
        Keeps visual effect only; numbers are no longer revealed."""
        if self.memory_flash_meter > 0:
            self.memory_flash_active = True
            self.memory_flash_effect.activate()
    
    def check_wave_completion(self):
        """Check if wave is complete and trigger pattern challenge"""
        if len(self.enemy_sprites) == 0 and not self.pattern_challenge_active:
            self.waves_completed += 1
            
            # Every 3 waves, trigger pattern challenge
            if self.waves_completed % 3 == 0:
                pattern_length = min(6, 3 + (self.waves_completed // 3))
                self.pattern_challenge = PatternMemoryChallenge(pattern_length=pattern_length)
                self.pattern_challenge.start()
                self.pattern_challenge_active = True

    def draw_score(self):
        score_text = self.font.render(f"Score: {self.score}", True, 'white')
        self.display_surface.blit(score_text, (10, 10))
        
        max_lives = self.max_lives
        heart_spacing = 40
        heart_y = 10
        heart_start_x = WINDOW_WIDTH - (max_lives * heart_spacing) - 10  
        
        for i in range(max_lives):
            heart_x = heart_start_x + (i * heart_spacing)
            if i < self.lives:
                self.display_surface.blit(self.full_heart, (heart_x, heart_y))
            else:
                self.display_surface.blit(self.empty_heart, (heart_x, heart_y))
        
        # Show stored hearts banked
        if self.stored_hearts > 0:
            stored_text = self.font.render(f"+{self.stored_hearts}", True, (255, 215, 0))
            stored_rect = stored_text.get_rect()
            stored_rect.topleft = (heart_start_x + (max_lives * heart_spacing) + 10, heart_y + 4)
            self.display_surface.blit(stored_text, stored_rect)
        
        power_text = self.font.render(f"Power: {self.power}", True, 'white')
        self.display_surface.blit(power_text, (10, 50))
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT]:
            pygame.draw.circle(self.display_surface, (255, 255, 255), 
                             self.player.get_hitbox_center(), self.player.hitbox_radius, 1)

    def draw_memory_flash_bar(self):
        """Draw a memory-flash usage bar at bottom-right that drains while active.
        Refills +10% on level completion (handled elsewhere)."""
        bar_width = 180
        bar_height = 16
        margin = 20
        x = WINDOW_WIDTH - margin - bar_width
        y = WINDOW_HEIGHT - margin - bar_height

        # Background
        pygame.draw.rect(self.display_surface, (30, 30, 40), (x, y, bar_width, bar_height))

        # Fill
        fill_ratio = max(0.0, min(1.0, self.memory_flash_meter))
        fill_width = int(bar_width * fill_ratio)
        fill_color = (0, 220, 220) if self.memory_flash_active else (0, 180, 180)
        pygame.draw.rect(self.display_surface, fill_color, (x, y, fill_width, bar_height))

        # Border
        pygame.draw.rect(self.display_surface, (200, 200, 200), (x, y, bar_width, bar_height), 2)

        # Label and percent
        label = self.font.render("MEMORY", True, (200, 255, 255))
        pct = int(fill_ratio * 100)
        pct_text = self.font.render(f"{pct}%", True, (220, 220, 220))
        self.display_surface.blit(label, (x - 10 - label.get_width(), y - 2))
        self.display_surface.blit(pct_text, (x + bar_width + 10, y - 2))

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.display_surface.blit(overlay, (0, 0))
        
        if self.victory:
            game_over_text = self.game_over_font.render("VICTORY!", True, (255, 215, 0))
            
            subtitle_text = self.title_font.render("stage2 Complete!", True, (100, 255, 100))
            subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 80))
            self.display_surface.blit(subtitle_text, subtitle_rect)
            
            victory_msg = self.font.render("The Queen Bee has been defeated!", True, (200, 255, 200))
            msg_rect = victory_msg.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40))
            self.display_surface.blit(victory_msg, msg_rect)
            
            if hasattr(self, 'boss') and self.boss and not self.boss.alive():
                boss_msg = self.font.render("Boss Battle Complete!", True, (255, 255, 100))
                boss_rect = boss_msg.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 10))
                self.display_surface.blit(boss_msg, boss_rect)
        else:
            game_over_text = self.game_over_font.render("GAME OVER", True, (255, 50, 50))
            
            defeat_msg = self.font.render("The Queen Bee proved too powerful...", True, (255, 150, 150))
            defeat_rect = defeat_msg.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40))
            self.display_surface.blit(defeat_msg, defeat_rect)
            
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 120))
        self.display_surface.blit(game_over_text, game_over_rect)
        
        final_score_text = self.title_font.render(f"Final Score: {self.score}", True, 'white')
        score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 40))
        self.display_surface.blit(final_score_text, score_rect)
        
        performance_text = self.font.render(f"Lives Remaining: {self.lives}", True, (200, 200, 255))
        perf_rect = performance_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 80))
        self.display_surface.blit(performance_text, perf_rect)
        
        restart_text = self.font.render("Press ESC to return to map", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 140))
        self.display_surface.blit(restart_text, restart_rect)
        
        quit_text = self.font.render("Press Q to quit", True, (200, 200, 200))
        quit_rect = quit_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 180))
        self.display_surface.blit(quit_text, quit_rect)

    def stop_audio(self):
        if "music" in self.audio:
            self.audio["music"].stop()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            self.done = True
            return
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and (event.mod & pygame.KMOD_CTRL):
            self.victory = True
            self.game_over = True
            self.done = True
            self.running = False
            return

        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            self.running = False
            self.done = True
            return

        if self.game_over:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.running = False
                self.done = True
            return

        if event.key == pygame.K_e:
            if self.memory_flash_active:
                self.memory_flash_active = False
            else:
                if self.memory_flash_meter > 0:
                    self.memory_flash_active = True
                    self.memory_flash_effect.activate()

        if self.pattern_challenge_active and not self.pattern_challenge.showing:
            if event.key == pygame.K_1:
                self.pattern_challenge.add_input(1)
            elif event.key == pygame.K_2:
                self.pattern_challenge.add_input(2)
            elif event.key == pygame.K_3:
                self.pattern_challenge.add_input(3)
            elif event.key == pygame.K_4:
                self.pattern_challenge.add_input(4)

    def step(self, dt):
        if not self.game_over:
            # No timed spawning in sequence mode
            self.invulnerable_timer.update()
            self.freeze_timer.update()

            # Check if game over should happen after freeze ends
            if self.pending_game_over and not self.freeze_timer:
                self.game_over = True
                self.pending_game_over = False

            # Check cognitive load game over (disabled in sequence mode)
            if (not self.sequence_mode) and self.cognitive_load.is_game_over():
                self.game_over = True
                self.pending_game_over = False

            # Memory flash ability removed per new design

            # Optional pattern challenge (kept but not used in sequence mode)
            if self.pattern_challenge_active:
                self.pattern_challenge.update(dt)
                if self.pattern_challenge.complete:
                    if self.pattern_challenge.success:
                        # Restore life and reduce load
                        if self.lives < 3:
                            self.lives += 1
                        self.cognitive_load.update_load(-30)
                    else:
                        # Increase load on failure
                        self.cognitive_load.update_load(20)
                    self.pattern_challenge_active = False
                    self.pattern_challenge = None

            # Only update game logic if not frozen and not in pattern challenge
            if not self.freeze_timer and not self.pattern_challenge_active:
                # Sequence state machine
                if self.sequence_state == 'SPAWNING':
                    # Wait for all bees to reach their target positions
                    all_in_position = True
                    for bee in self.sequence_bees:
                        if hasattr(bee, 'target_position') and bee.target_position:
                            all_in_position = False
                            break
                    if all_in_position:
                        # All bees are now on-screen, start SHOW phase
                        self.sequence_state = 'SHOW'
                        self.sequence_show_index = 0
                        self.sequence_show_timer = 0

                elif self.sequence_state == 'SHOW':
                    # Freeze bee movement while showing the sequence
                    for b in self.sequence_bees:
                        b.movement_enabled = False
                    self.sequence_show_timer += dt
                    if self.sequence_show_timer >= self.sequence_show_delay:
                        # Clear previous highlights
                        for b in self.sequence_bees:
                            b.set_highlight(False)
                        # Highlight current bee
                        if self.sequence_show_index < len(self.sequence_order):
                            idx = self.sequence_order[self.sequence_show_index]
                            if idx < len(self.sequence_bees) and self.sequence_bees[idx].alive():
                                self.sequence_bees[idx].set_highlight(True)
                            self.sequence_show_index += 1
                            self.sequence_show_timer = 0
                        else:
                            # End of show, go to input phase
                            for b in self.sequence_bees:
                                b.set_highlight(False)
                                b.movement_enabled = True  # Re-enable movement for chase
                            self.sequence_state = 'INPUT'
                            self.sequence_input_index = 0

                # In INPUT phase, actively highlight the current target bee
                if self.sequence_state == 'INPUT':
                    # Ensure only the expected bee is highlighted
                    for b in self.sequence_bees:
                        b.set_highlight(False)
                    if self.sequence_input_index < len(self.sequence_order):
                        idx = self.sequence_order[self.sequence_input_index]
                        if idx < len(self.sequence_bees) and self.sequence_bees[idx].alive():
                            self.sequence_bees[idx].set_highlight(True)

                # Cognitive load system disabled for pure sequence mode

                self.all_sprites.update(dt)
                self.collision()
                # No wave completion; progression handled by sequence manager

            # Update memory flash effect and drain meter when active
            self.memory_flash_effect.update(dt)
            if self.memory_flash_active:
                self.memory_flash_meter -= (dt / self.memory_flash_capacity)
                if self.memory_flash_meter <= 0:
                    self.memory_flash_meter = 0
                    self.memory_flash_active = False

            self.display_surface.fill(BG_COLOR)

            # No screen shake in sequence mode - stable camera
            camera_center = (self.player.rect.centerx, self.player.rect.centery)
            self.all_sprites.draw(camera_center)

            # Draw numbered indicators above bees when showing sequence or when memory flash is active
            if self.sequence_state == 'SHOW' or self.memory_flash_active:
                for i, bee in enumerate(self.sequence_bees):
                    if not bee.alive():
                        continue

                    # Find this bee's position in the kill order (1-indexed)
                    kill_order_pos = None
                    for order_idx, bee_idx in enumerate(self.sequence_order):
                        if bee_idx == i:
                            kill_order_pos = order_idx + 1
                            break
                    if kill_order_pos is None:
                        continue

                    # Screen-space position above bee
                    screen_x = bee.rect.centerx - camera_center[0] + WINDOW_WIDTH // 2
                    screen_y = bee.rect.top - camera_center[1] + WINDOW_HEIGHT // 2 - 30

                    # Box and number
                    box_size = 24
                    box_rect = pygame.Rect(screen_x - box_size//2, screen_y - box_size//2, box_size, box_size)
                    box_color = (255, 215, 0)
                    if self.sequence_state == 'INPUT' and self.memory_flash_active and self.sequence_input_index == kill_order_pos - 1:
                        box_color = (0, 255, 0)  # Highlight current target when flashing
                    pygame.draw.rect(self.display_surface, box_color, box_rect)
                    pygame.draw.rect(self.display_surface, (0, 0, 0), box_rect, 2)

                    num_surf = self.font.render(str(kill_order_pos), True, (0, 0, 0))
                    num_rect = num_surf.get_rect(center=box_rect.center)
                    self.display_surface.blit(num_surf, num_rect)

            # No memory trails needed in sequence mode

            # Enemy bullets disabled; nothing to draw

            self.draw_score()
            self.draw_memory_flash_bar()

            # Draw order tracker UI at top center only when memory flash is active (or during SHOW)
            if (self.memory_flash_active or self.sequence_state == 'SHOW') and len(self.sequence_order) > 0:
                tracker_y = 60
                tracker_text = "Kill Order: "
                for i in range(len(self.sequence_order)):
                    if i > 0:
                        tracker_text += " -> "
                    if self.sequence_state == 'INPUT' and i == self.sequence_input_index and self.memory_flash_active:
                        tracker_text += f"[{i+1}]"
                    elif self.sequence_state == 'INPUT' and i < self.sequence_input_index:
                        tracker_text += "ok"
                    else:
                        tracker_text += f"{i+1}"

                tracker_surf = self.font.render(tracker_text, True, (255, 255, 100))
                tracker_rect = tracker_surf.get_rect(center=(WINDOW_WIDTH // 2, tracker_y))

                bg_rect = tracker_rect.inflate(20, 10)
                bg_surf = pygame.Surface((bg_rect.width, bg_rect.height))
                bg_surf.set_alpha(180)
                bg_surf.fill((20, 20, 40))
                self.display_surface.blit(bg_surf, bg_rect.topleft)
                pygame.draw.rect(self.display_surface, (255, 215, 0), bg_rect, 2)

                self.display_surface.blit(tracker_surf, tracker_rect)

            # Draw sequence HUD (bottom-left, no memory load bar)
            hud_y = WINDOW_HEIGHT - 80
            level_text = self.font.render(f"Level: {self.sequence_level}", True, (255, 215, 0))
            self.display_surface.blit(level_text, (10, hud_y))

            step_text = self.font.render(f"Shoot: {self.sequence_input_index+1 if self.sequence_state=='INPUT' else 0}/{len(self.sequence_order)}", True, (200, 255, 200))
            self.display_surface.blit(step_text, (10, hud_y + 35))

            # Draw pattern challenge
            if self.pattern_challenge_active:
                self.pattern_challenge.draw(self.display_surface, self.font,
                                          (WINDOW_WIDTH//2, WINDOW_HEIGHT//2))

            # No overload effects in sequence mode

            # Add freeze effect overlay
            if self.freeze_timer:
                freeze_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                freeze_overlay.set_alpha(30)
                freeze_overlay.fill((150, 200, 255))  # Light blue freeze effect
                self.display_surface.blit(freeze_overlay, (0, 0))

            if self.invulnerable_timer and pygame.time.get_ticks() % 200 < 100:
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                overlay.set_alpha(50)
                overlay.fill((255, 0, 0))
                self.display_surface.blit(overlay, (0, 0))
        else:
            self.draw_game_over()

        if self.game_over and self.victory and self.auto_return:
            now_ms = pygame.time.get_ticks()
            if self.completed_at is None:
                self.completed_at = now_ms
            elif now_ms - self.completed_at >= self.auto_return_delay_ms:
                self.running = False
                self.done = True
        elif not self.game_over:
            self.completed_at = None

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000

            for event in pygame.event.get():
                self.handle_event(event)

            self.step(dt)

            if self.owns_display:
                pygame.display.update()

        if self.owns_display:
            pygame.quit()
 
if __name__ == '__main__':
    game = Game()
    game.run()
