import pygame
import sys
from menu import Menu
from game import Game

class DiceApp:
    def __init__(self):
        """
        Initialize the main application
        Sets up the pygame window and initializes game states
        """
        pygame.init()
        pygame.mixer.init()  # Initialize sound system
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Dice Game")
        self.FPS = 60  # Set consistent frame rate
        self.clock = pygame.time.Clock()
        
        # Add error handling for sound loading
        try:
            self.roll_sound = pygame.mixer.Sound('sounds/dice_roll.wav')
        except:
            print("Warning: Could not load sound file")
            self.roll_sound = None
        
        self.menu = Menu(self.screen)
        self.game = None
        self.current_state = "menu"  # Tracks whether we're in menu or game state

    def run(self):
        """
        Main application loop
        Handles switching between menu and game states
        """
        while True:
            dt = self.clock.tick(self.FPS) / 1000.0  # Get delta time in seconds

            # Handle game states
            if self.current_state == "menu":
                result = self.menu.update()  # Now returns (player_count, speed)
                self.menu.draw(self.screen)
                if result:  # If menu returns settings
                    player_count, speed = result
                    # Only pass sound if it loaded successfully
                    self.game = Game(self.screen, player_count, speed, self.roll_sound)
                    self.current_state = "game"
            elif self.current_state == "game":
                game_over = self.game.update(dt)  # Pass delta time to game
                self.game.draw(self.screen)
                if game_over:
                    self.current_state = "menu"

            pygame.display.flip()

if __name__ == "__main__":
    app = DiceApp()
    app.run() 