import pygame, sys
from settings import *
from level import Level

class Game:
    def __init__(self, start_level=1):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Gabe Adventure')
        self.clock = pygame.time.Clock()
        
        # Level management
        self.current_level = start_level
        self.max_levels = 2 # We have level 1 and level 2
        self.level = Level('maps.txt', self.current_level)
        self.game_finished = False

    def reset_level(self):
        self.level = Level('maps.txt', self.current_level)

    def next_level(self):
        self.current_level += 1
        if self.current_level <= self.max_levels:
            self.level = Level('maps.txt', self.current_level)
        else:
            self.game_finished = True

    def draw_level_ready(self):
        font = pygame.font.SysFont('Arial', 24, bold=True)
        msg_surf = font.render('Press SPACE for Next Level', True, WHITE)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(msg_surf, msg_rect)

    def draw_restart_msg(self):
        font = pygame.font.SysFont('Arial', 24, bold=True)
        msg_surf = font.render('Press R to Restart', True, WHITE)
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(msg_surf, msg_rect)

    def draw_victory(self):
        font = pygame.font.SysFont('Arial', 48, bold=True)
        msg_surf = font.render('YOU CONQUERED ALL LEVELS!', True, (255, 215, 0)) # Gold
        msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        
        sub_font = pygame.font.SysFont('Arial', 24)
        sub_surf = sub_font.render('Gabe is a hero! Press Esc to Exit', True, WHITE)
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        
        self.screen.fill((20, 20, 40)) # Dark night sky
        self.screen.blit(msg_surf, msg_rect)
        self.screen.blit(sub_surf, sub_rect)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if self.game_finished:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                if event.type == pygame.KEYDOWN:
                    if not self.game_finished:
                        if self.level.game_over and event.key == pygame.K_r:
                            self.reset_level()
                        elif self.level.level_complete and event.key == pygame.K_SPACE:
                            self.next_level()

            self.screen.fill(BG_COLOR)
            
            if self.game_finished:
                self.draw_victory()
            else:
                self.level.run()
                if self.level.level_complete:
                    self.draw_level_ready()
                if self.level.game_over:
                    self.draw_restart_msg()

            pygame.display.update()
            self.clock.tick(FPS)

if __name__ == '__main__':
    game = Game()
    game.run()
