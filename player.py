import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites):
        super().__init__(groups)
        # Asset loading
        self.import_assets()
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.animations['idle'][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)
        
        # Hitbox (Kenney sprites have some empty space, so let's tighten the hitbox)
        self.hitbox = self.rect.inflate(-10, -5)
        
        self.obstacle_sprites = obstacle_sprites
        
        # Movement
        self.direction = pygame.math.Vector2()
        self.speed = WALK_SPEED
        self.gravity = GRAVITY
        self.jump_speed = JUMP_STRENGTH
        
        # Status
        self.status = 'idle'
        self.facing_right = True
        self.on_ground = False
        self.health = START_HEALTH
        self.is_hurt = False
        self.hurt_time = 0
        self.in_water = False
        self.climbing = False
        self.ladder_jump_timer = 0

    def import_assets(self):
        # We'll use the purple character for Gabe
        self.animations = {'idle': [], 'walk': [], 'jump': [], 'fall': [], 'climb': []}
        
        raw_assets = {
            'idle': ['character_purple_idle.png', 'character_purple_front.png'],
            'walk': ['character_purple_walk_a.png', 'character_purple_walk_b.png'],
            'jump': ['character_purple_jump.png'],
            'fall': ['character_purple_jump.png'],
            'climb': ['character_purple_climb_a.png', 'character_purple_climb_b.png']
        }
        
        for animation_name, files in raw_assets.items():
            for filename in files:
                image = pygame.image.load(f'{PLAYER_ASSETS}/{filename}').convert_alpha()
                # Scale down slightly to 96x96 (1.5x tile size)
                scaled_image = pygame.transform.scale(image, (96, 96))
                self.animations[animation_name].append(scaled_image)

    def animate(self):
        animation = self.animations[self.status]
        
        # Loop over frame index
        if self.status == 'climb' and self.direction.y == 0:
            # Don't advance animation if on ladder but not moving
            pass
        else:
            self.frame_index += self.animation_speed
            if self.frame_index >= len(animation):
                self.frame_index = 0
            
        image = animation[int(self.frame_index)]
        if self.facing_right:
            self.image = image
        else:
            self.image = pygame.transform.flip(image, True, False)

    def get_status(self):
        if self.climbing:
            self.status = 'climb'
        elif self.direction.y < 0:
            self.status = 'jump'
        elif self.direction.y > 1: # Some threshold for gravity
            self.status = 'fall'
        else:
            if self.direction.x != 0:
                self.status = 'walk'
            else:
                self.status = 'idle'

    def input(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.facing_right = True
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.facing_right = False
        else:
            self.direction.x = 0
            
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.speed = RUN_SPEED if not self.in_water else WATER_SPEED
        else:
            self.speed = WALK_SPEED if not self.in_water else WATER_SPEED

        if keys[pygame.K_SPACE]:
            if self.on_ground or self.climbing:
                self.jump()
            elif self.in_water:
                self.swim()
            
        if self.climbing and not (pygame.time.get_ticks() - self.ladder_jump_timer < 200):
            if keys[pygame.K_UP]:
                self.direction.y = -1
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
            else:
                self.direction.y = 0

    def apply_gravity(self):
        if self.climbing:
             self.rect.y += self.direction.y * 4
        else:
            gravity = self.gravity if not self.in_water else WATER_GRAVITY
            self.direction.y += gravity
            self.rect.y += self.direction.y

    def jump(self):
        if self.climbing:
            self.ladder_jump_timer = pygame.time.get_ticks()
            self.climbing = False
        self.direction.y = self.jump_speed

    def swim(self):
        # Regular swim
        self.direction.y = WATER_JUMP
        # Note: WATER_JUMP has been increased in settings.py to help exit water surfaces

    def horizontal_collisions(self):
        self.rect.x += self.direction.x * self.speed
        
        for sprite in self.obstacle_sprites:
            if sprite.rect.colliderect(self.rect):
                # Check for movable boxes
                if hasattr(sprite, 'sprite_type') and sprite.sprite_type == 'box':
                    # If player is pushing the box
                    if self.direction.x > 0: # Pushing right
                        if sprite.push(pygame.math.Vector2(1, 0)):
                            self.rect.right = sprite.rect.left
                        else:
                            self.rect.right = sprite.rect.left
                    elif self.direction.x < 0: # Pushing left
                        if sprite.push(pygame.math.Vector2(-1, 0)):
                            self.rect.left = sprite.rect.right
                        else:
                            self.rect.left = sprite.rect.right
                else:
                    if self.direction.x > 0: # Moving right
                        self.rect.right = sprite.rect.left
                    elif self.direction.x < 0: # Moving left
                        self.rect.left = sprite.rect.right

    def vertical_collisions(self):
        self.apply_gravity()
        
        for sprite in self.obstacle_sprites:
            if sprite.rect.colliderect(self.rect):
                if self.direction.y > 0: # Falling
                    self.rect.bottom = sprite.rect.top
                    self.direction.y = 0
                    self.on_ground = True
                elif self.direction.y < 0: # Jumping
                    self.rect.top = sprite.rect.bottom
                    self.direction.y = 0
                    if hasattr(sprite, 'hit'):
                        sprite.hit()
                else: # Standing still but overlapping (e.g., spawn)
                    if self.rect.centery < sprite.rect.centery:
                        self.rect.bottom = sprite.rect.top
                        self.on_ground = True
                    else:
                        self.rect.top = sprite.rect.bottom
                    
        if self.on_ground and (self.direction.y < 0 or self.direction.y > 1):
            self.on_ground = False

    def get_damage(self):
        if not self.is_hurt:
            self.health -= 1
            self.is_hurt = True
            self.hurt_time = pygame.time.get_ticks()
            # Knockback? (optional)
            self.direction.y = -10 

    def invincibility_timer(self):
        if self.is_hurt:
            current_time = pygame.time.get_ticks()
            if current_time - self.hurt_time >= HURT_COOLDOWN:
                self.is_hurt = False

    def flicker(self):
        if self.is_hurt:
            value = pygame.time.get_ticks() % 200
            if value < 100:
                self.image.set_alpha(0)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def update(self):
        self.input()
        self.invincibility_timer()
        self.flicker()
        self.get_status()
        self.animate()
        self.horizontal_collisions()
        self.vertical_collisions()
