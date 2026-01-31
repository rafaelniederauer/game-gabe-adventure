import pygame
from settings import *
from player import Player

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups, sprite_type):
        super().__init__(groups)
        self.sprite_type = sprite_type
        path = f'{TILE_ASSETS}/terrain_grass_block.png'
        if sprite_type == 'spikes': path = f'{TILE_ASSETS}/spikes.png'
        elif sprite_type == 'exit': path = f'{TILE_ASSETS}/flag_red_a.png'
        elif sprite_type == 'start': path = f'{TILE_ASSETS}/flag_green_a.png'
        
        try:
            self.image = pygame.image.load(path).convert_alpha()
        except:
            self.image = pygame.Surface((64, 64))
            self.image.fill(WHITE)
            
        self.rect = self.image.get_rect(topleft=pos)

class Box(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites):
        super().__init__(groups)
        self.sprite_type = 'box'
        self.image = pygame.image.load(f'{TILE_ASSETS}/block_planks.png').convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)
        self.obstacle_sprites = obstacle_sprites
        self.direction = pygame.math.Vector2()
        self.gravity = GRAVITY

    def push(self, direction):
        # Move box
        self.rect.x += direction.x * BOX_SPEED
        # Check for collisions with other obstacles
        for sprite in self.obstacle_sprites:
            if sprite != self and sprite.rect.colliderect(self.rect):
                if direction.x > 0: self.rect.right = sprite.rect.left
                if direction.x < 0: self.rect.left = sprite.rect.right
                return False
        return True

    def apply_gravity(self):
        self.direction.y += self.gravity
        self.rect.y += self.direction.y
        
        for sprite in self.obstacle_sprites:
            if sprite != self and sprite.rect.colliderect(self.rect):
                if self.direction.y > 0:
                    self.rect.bottom = sprite.rect.top
                    self.direction.y = 0
                elif self.direction.y < 0:
                    self.rect.top = sprite.rect.bottom
                    self.direction.y = 0

    def update(self):
        self.apply_gravity()

class Coin(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.frames = [
            pygame.image.load(f'{TILE_ASSETS}/coin_gold.png').convert_alpha(),
            pygame.image.load(f'{TILE_ASSETS}/coin_gold_side.png').convert_alpha()
        ]
        self.frame_index = 0
        self.animation_speed = 0.05
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))

    def animate(self):
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self):
        self.animate()

class Water(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.sprite_type = 'water'
        self.image = pygame.image.load(f'{TILE_ASSETS}/water_top.png').convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.level_width = 0
        self.level_height = 0

    def custom_draw(self, player):
        # Calculate offset based on player position
        self.offset.x = player.rect.centerx - self.display_surface.get_width() // 2
        self.offset.y = player.rect.centery - self.display_surface.get_height() // 2

        # Clamp offsets to prevent seeing the "void"
        # X clamping
        if self.level_width > self.display_surface.get_width():
            self.offset.x = max(0, min(self.offset.x, self.level_width - self.display_surface.get_width()))
        else:
            self.offset.x = (self.level_width - self.display_surface.get_width()) // 2

        # Y clamping
        if self.level_height > self.display_surface.get_height():
            self.offset.y = max(0, min(self.offset.y, self.level_height - self.display_surface.get_height()))
        else:
            self.offset.y = (self.level_height - self.display_surface.get_height()) // 2

        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)

class Level:
    def __init__(self, map_file, level_number):
        # Display surface
        self.display_surface = pygame.display.get_surface()
        self.level_number = level_number
        
        # Sprite groups
        self.visible_sprites = CameraGroup()
        self.active_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()
        self.coin_sprites = pygame.sprite.Group()
        self.hazard_sprites = pygame.sprite.Group()
        self.water_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group()
        
        # UI & State
        self.level_complete = False
        self.game_over = False
        self.score = 0
        self.font = pygame.font.SysFont('Arial', 32, bold=True)
        self.coin_gui_image = pygame.image.load(f'{TILE_ASSETS}/hud_coin.png').convert_alpha()
        self.heart_image = pygame.image.load(f'{TILE_ASSETS}/hud_heart.png').convert_alpha()
        self.heart_empty_image = pygame.image.load(f'{TILE_ASSETS}/hud_heart_empty.png').convert_alpha()
        
        # Setup level
        self.create_map(map_file)
        
    def create_map(self, map_file):
        try:
            with open(map_file, 'r') as f:
                lines = f.readlines()
                
            # Find level section
            header = f"level {self.level_number}:"
            start_index = -1
            for i, line in enumerate(lines):
                if header in line.lower():
                    start_index = i + 1
                    break
            
            if start_index == -1:
                print(f"Level {self.level_number} not found in {map_file}")
                return

            # Find end of level (next level header or EOF)
            end_index = len(lines)
            for i in range(start_index, len(lines)):
                if "level " in lines[i].lower() and ":" in lines[i]:
                    end_index = i
                    break

            # map_data might have empty lines or trailing spaces
            map_data = [line.removesuffix('\n') for line in lines[start_index:end_index]]
            
            # Calculate Level Dimensions
            self.level_height = len(map_data) * TILE_SIZE
            self.level_width = max([len(line) for line in map_data]) * TILE_SIZE
            self.visible_sprites.level_width = self.level_width
            self.visible_sprites.level_height = self.level_height

            for row_index, row in enumerate(map_data):
                for col_index, cell in enumerate(row):
                    x = col_index * TILE_SIZE
                    y = row_index * TILE_SIZE
                    if cell == '-':
                        Tile((x, y), [self.visible_sprites, self.obstacle_sprites], 'ground')
                    elif cell == 'B':
                        Box((x, y), [self.visible_sprites, self.active_sprites, self.obstacle_sprites], self.obstacle_sprites)
                    elif cell == 'C':
                        Coin((x, y), [self.visible_sprites, self.coin_sprites, self.active_sprites])
                    elif cell == 'S':
                        Tile((x, y), [self.visible_sprites, self.hazard_sprites], 'spikes')
                    elif cell == 'W':
                        Water((x, y), [self.visible_sprites, self.water_sprites])
                    elif cell == '1':
                        Tile((x, y), [self.visible_sprites], 'start')
                        self.spawn_pos = (x, y)
                    elif cell == 'E':
                        Tile((x, y), [self.visible_sprites, self.exit_sprites], 'exit')
            
            # Place Player at a starting position
            if hasattr(self, 'spawn_pos'):
                spawn_pos = self.spawn_pos
            else:
                # Fallback to old logic if '1' not found
                spawn_pos = (100, 100)
                floor_platforms = [s for s in self.obstacle_sprites if s.rect.x < 200]
                if floor_platforms:
                    lowest = max(floor_platforms, key=lambda s: s.rect.y)
                    spawn_pos = (lowest.rect.x, lowest.rect.y - 100)

            self.player = Player(spawn_pos, [self.visible_sprites, self.active_sprites], self.obstacle_sprites)
            
        except FileNotFoundError:
            print(f"File {map_file} not found")

    def coin_collision(self):
        collided_coins = pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
        if collided_coins:
            self.score += len(collided_coins)

    def hazard_collision(self):
        if pygame.sprite.spritecollide(self.player, self.hazard_sprites, False):
            self.player.get_damage()
            
    def water_collision(self):
        if pygame.sprite.spritecollide(self.player, self.water_sprites, False):
            self.player.in_water = True
        else:
            self.player.in_water = False

    def check_win(self):
        if pygame.sprite.spritecollide(self.player, self.exit_sprites, False):
            self.level_complete = True

    def draw_ui(self):
        # Draw coin image
        self.display_surface.blit(self.coin_gui_image, (20, 20))
        # Draw score text
        score_surf = self.font.render(f'x {self.score}', True, (0, 0, 0))
        self.display_surface.blit(score_surf, (80, 25))
        
        # Draw hearts
        for i in range(START_HEALTH):
            x = 20 + i * 50
            if i < self.player.health:
                self.display_surface.blit(self.heart_image, (x, 70))
            else:
                self.display_surface.blit(self.heart_empty_image, (x, 70))
        
        # Draw Win Message
        if self.level_complete:
            win_surf = self.font.render('LEVEL COMPLETE!', True, (255, 255, 255))
            win_rect = win_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            # Draw overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.display_surface.blit(overlay, (0,0))
            self.display_surface.blit(win_surf, win_rect)

    def boundary_check(self):
        # Keep player within level width
        if self.player.rect.left < 0:
            self.player.rect.left = 0
        if self.player.rect.right > self.level_width:
            self.player.rect.right = self.level_width
            
        # If player falls below the level, he is hurt or dies
        # For now, let's keep him from falling into the "void" at the bottom
        # if the user doesn't want void, we might block him or kill him
        if self.player.rect.top > self.level_height:
            self.player.health = 0
            self.game_over = True
        
        if self.player.health <= 0:
            self.game_over = True

    def run(self):
        # Run the level logic
        if not self.level_complete and self.player.health > 0:
            self.active_sprites.update()
            self.coin_collision()
            self.hazard_collision()
            self.water_collision()
            self.boundary_check()
            self.check_win()
            
        self.visible_sprites.custom_draw(self.player)
        self.draw_ui()
        
        if self.player.health <= 0:
            self.draw_game_over()

    def draw_game_over(self):
        death_surf = self.font.render('GAME OVER', True, (255, 0, 0))
        death_rect = death_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.display_surface.blit(overlay, (0,0))
        self.display_surface.blit(death_surf, death_rect)
