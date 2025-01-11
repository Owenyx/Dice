import pygame
import sys
from game import Game

class Menu:
    def __init__(self, screen):
        """
        Initialize the menu screen
        Args:
            screen: pygame display surface to draw the menu on
        """
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.player_count = 2  # Default number of players
        self.speed_multiplier = 1.0  # Default speed
        self.player_names = ["Owen", "Olivia", "Zoe", "Mike", "Jenn", "Eleanor"]  # Available names
        self.selected_names = ["Owen", "Olivia"]  # Default selected names
        self.name_buttons = []  # Will store rect and current name for each player
        self.name_button_start_x = 50
        self.name_button_start_y = screen.get_height() - 250  # Start 250px from bottom
        self.name_button_spacing = 40
        self.update_name_buttons()
        # Define clickable button areas
        self.buttons = {
            'decrease': pygame.Rect(300, 250, 30, 30),  # "-" button
            'increase': pygame.Rect(470, 250, 30, 30),  # "+" button
            'speed_left': pygame.Rect(300, 300, 30, 30),   # New speed buttons
            'speed_right': pygame.Rect(600, 300, 30, 30),
            'start': pygame.Rect(300, 400, 200, 50)        # Moved down
        }
        self.speed_options = [1.0, 1.5, 2.0, 4.0, float('inf')]  # inf for instant
        self.current_speed_index = 0

    def update_name_buttons(self):
        self.name_buttons = []
        for i in range(self.player_count):
            button_rect = pygame.Rect(
                self.name_button_start_x, 
                self.name_button_start_y + (i * self.name_button_spacing), 
                200, 30)
            self.name_buttons.append({
                'rect': button_rect,
                'name': self.selected_names[i],
                'player': i
            })

    def update(self):
        """Handle menu logic, return (player_count, speed) if game should start"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if self.buttons['decrease'].collidepoint(mouse_pos):
                    self.player_count = max(2, self.player_count - 1)
                    self.selected_names = self.selected_names[:self.player_count]
                    self.update_name_buttons()
                elif self.buttons['increase'].collidepoint(mouse_pos):
                    self.player_count = min(6, self.player_count + 1)
                    self.selected_names.append(self.player_names[self.player_count - 1])
                    self.update_name_buttons()
                elif self.buttons['speed_left'].collidepoint(mouse_pos):
                    self.current_speed_index = (self.current_speed_index - 1) % len(self.speed_options)
                elif self.buttons['speed_right'].collidepoint(mouse_pos):
                    self.current_speed_index = (self.current_speed_index + 1) % len(self.speed_options)
                elif self.buttons['start'].collidepoint(mouse_pos):
                    return (self.player_count, self.speed_options[self.current_speed_index])

                # Handle name selection buttons
                for button in self.name_buttons:
                    if button['rect'].collidepoint(mouse_pos):
                        # Cycle to next name
                        current_index = self.player_names.index(button['name'])
                        next_index = (current_index + 1) % len(self.player_names)
                        button['name'] = self.player_names[next_index]
                        self.selected_names[button['player']] = self.player_names[next_index]

        return None

    def draw(self, screen):
        """Draw menu state"""
        screen.fill((50, 100, 50))  # Green background
        
        # Draw title
        title = self.font.render("Dice Game", True, (255, 255, 255))
        screen.blit(title, (350, 100))

        # Draw player count selector
        pygame.draw.rect(screen, (200, 200, 200), self.buttons['decrease'])
        pygame.draw.rect(screen, (200, 200, 200), self.buttons['increase'])
        
        # Draw speed selector
        pygame.draw.rect(screen, (200, 200, 200), self.buttons['speed_left'])
        pygame.draw.rect(screen, (200, 200, 200), self.buttons['speed_right'])
        
        # Draw start button
        pygame.draw.rect(screen, (200, 200, 200), self.buttons['start'])

        # Draw text
        player_text = self.font.render(f"Players: {self.player_count}", True, (255, 255, 255))
        minus = self.font.render("-", True, (0, 0, 0))
        plus = self.font.render("+", True, (0, 0, 0))
        
        # Speed text
        current_speed = self.speed_options[self.current_speed_index]
        speed_text = "Instant" if current_speed == float('inf') else f"{current_speed}x"
        speed_label = self.font.render(f"Game Speed: {speed_text}", True, (255, 255, 255))
        left = self.font.render("<", True, (0, 0, 0))
        right = self.font.render(">", True, (0, 0, 0))
        
        start = self.font.render("Start Game", True, (0, 0, 0))

        # Position text
        screen.blit(player_text, (350, 255))
        screen.blit(minus, (310, 255))
        screen.blit(plus, (480, 255))
        screen.blit(speed_label, (350, 305))
        screen.blit(left, (310, 305))
        screen.blit(right, (610, 305))
        screen.blit(start, (340, 415)) 

        # Draw name selection section
        name_section_label = self.font.render("Player Names", True, (255, 255, 255))
        click_label = self.font.render("(click to change)", True, (200, 200, 200))  # Lighter color
        screen.blit(name_section_label, (self.name_button_start_x, self.name_button_start_y - 60))
        screen.blit(click_label, (self.name_button_start_x, self.name_button_start_y - 30))
        
        for i, button in enumerate(self.name_buttons):
            pygame.draw.rect(screen, (200, 200, 200), button['rect'])
            name_text = self.font.render(button['name'], True, (0, 0, 0))
            text_rect = name_text.get_rect(center=button['rect'].center)
            screen.blit(name_text, text_rect)

    def start_game(self):
        # Create game instance with selected names
        return Game(self.screen, self.player_count, self.speed_options[self.current_speed_index], 
                   self.roll_sound, player_names=self.selected_names) 