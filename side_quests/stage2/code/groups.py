from settings import * 

class AllSprites(pygame.sprite.Group):
    def __init__(self, display_surface=None):
        super().__init__()
        self.display_surface = display_surface or pygame.display.get_surface()
        self.offset = pygame.Vector2()

    def set_surface(self, surface):
        self.display_surface = surface

    def draw(self, target_pos):
        self.offset.x = -(target_pos[0] - WINDOW_WIDTH / 2)
        self.offset.y = -(target_pos[1] - WINDOW_HEIGHT / 2)

        for sprite in self:
            self.display_surface.blit(sprite.image, sprite.rect.topleft + self.offset)