import pygame
from dice import Die
import random

class Game:
    def __init__(self, screen, player_count, speed_multiplier=1.0, roll_sound=None, player_names=None):
        """
        Initialize the game state
        Args:
            screen: pygame display surface
            player_count (int): number of players
            speed_multiplier (float): speed multiplier for the game
            roll_sound: pygame mixer sound object for dice rolling sound
            player_names: list of player names
        """
        Die.speed_multiplier = speed_multiplier  # Set the class-level speed multiplier
        self.speed_multiplier = speed_multiplier
        self.screen = screen
        self.player_count = player_count
        self.scores = [0] * player_count 
        # Use provided names or defaults
        self.player_names = player_names if player_names else ["Owen", "Olivia", "Zoe", "Mike", "Jenn", "Eleanor"][:player_count]  # Take only needed names
        self.current_player = 0
        self.current_score = 0  # Score accumulated this turn
        self.turn_score = 0     # Total score for the turn
        self.dice = [Die(100 + i * 80, 250) for i in range(6)]  # Back to Y=250
        self.kept_dice = []  # Dice that have been scored this turn
        self.kept_dice_y = 150  # Back to Y=150
        self.font = pygame.font.Font(None, 36)
        self.roll_button = pygame.Rect(300, 400, 100, 50)
        self.keep_button = pygame.Rect(450, 400, 100, 50)
        self.end_turn_button = pygame.Rect(600, 400, 120, 50)  # Made wider (100->120)
        self.rolling = False
        self.must_roll = True  # True when player must roll (start of turn or after keeping dice)
        self.has_rolled = False  # Track if player has rolled at least once this turn
        self.available_dice_count = 6  # Track available dice for next player option
        self.can_take_previous_score = False  # Whether current player can take previous player's score
        self.can_keep = False  # New flag to control keep button visibility
        self.no_score_timer = 0  # Add timer for no-score animation
        self.no_score_delay = 2.0 / speed_multiplier  # Adjust delay based on speed
        self.show_no_score = False  # Flag to show no-score indication
        self.kept_slots = [False] * 6  # Track which slots are used for kept dice
        self.kept_dice_x = 100  # Starting X position for kept dice
        self.kept_dice_spacing = 80  # Space between kept dice slots
        self.previous_turn_score = 0  # Add this to track previous player's score
        self.previous_dice_count = 0  # Add this to track previous player's remaining dice
        self.take_score_button = pygame.Rect(300, 150, 300, 40)  # Made wider (250->300)
        self.show_bust = False
        self.bust_timer = 0
        self.bust_delay = 2.0 / speed_multiplier
        self.game_over = False
        self.winner = None
        self.menu_button = pygame.Rect(350, 300, 200, 50)
        self.roll_sound = roll_sound
        self.roll_sound_playing = False  # Add new flag
        self.is_rolling = False  # Add this line

    def update(self, dt):
        """Update game state"""
        # Adjust dt based on speed multiplier
        if self.speed_multiplier != float('inf'):
            dt *= self.speed_multiplier
        else:
            dt = float('inf')

        # Update dice animations and check rolling state
        any_rolling = False
        for die in self.dice:
            die.update()
            if die.rolling:
                any_rolling = True
        
        # Mute all sound if dice aren't rolling
        if not any_rolling:
            pygame.mixer.stop()
            self.roll_sound_playing = False
        
        # Check for no-score situation only after dice finish rolling
        if self.rolling and not any_rolling:
            self.rolling = False
            if not self.has_scoring_dice():
                self.show_no_score = True
                self.no_score_timer = self.no_score_delay
            else:
                # Check for potential bust after dice stop rolling
                if not self.check_potential_bust():
                    self.can_keep = True  # Enable keep button if no bust
        
        self.rolling = any_rolling
        self.is_rolling = any_rolling

        # Handle no-score timer using real time
        if self.show_no_score:
            self.no_score_timer -= dt
            if self.no_score_timer <= 0:
                self.show_no_score = False
                self.turn_score = 0
                self.end_turn()

        # Handle bust timer using real time
        if self.show_bust:
            self.bust_timer -= dt
            if self.bust_timer <= 0:
                self.show_bust = False

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True
            
            if not self.rolling:  # Only allow interaction when dice aren't rolling
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    
                    # Handle menu button if game is over
                    if self.game_over and self.menu_button.collidepoint(mouse_pos):
                        return True  # Signal to return to menu

                    # Handle taking previous score with button instead of key
                    if (self.take_score_button.collidepoint(mouse_pos) and 
                        self.must_roll and not self.has_rolled and 
                        self.scores[self.current_player] >= 1000 and 
                        self.previous_turn_score > 0 and
                        self.scores[self.current_player] + self.previous_turn_score < 10000):
                        # Take previous score and setup dice
                        self.turn_score = self.previous_turn_score
                        
                        # Restore kept dice exactly as they were
                        self.kept_dice = self.previous_kept_dice[:]
                        self.kept_slots = self.previous_kept_slots[:]
                        
                        # If previous player had all dice kept (6 kept, 0 active)
                        if len(self.previous_kept_dice) == 6:
                            self.dice = []  # No active dice to start
                        else:
                            # Keep only the number of active dice needed
                            while len(self.dice) > self.previous_dice_count:
                                self.dice.pop(random.randint(0, len(self.dice) - 1))
                            # Position active dice
                            x_offset = 100
                            for die in self.dice:
                                die.x = x_offset
                                die.y = 250
                                x_offset += 80

                        # Clear the previous score so next player starts fresh
                        self.previous_turn_score = 0
                        self.previous_dice_count = 0
                        self.previous_kept_dice = []
                        self.previous_kept_slots = [False] * 6
                        
                        # Set proper state for continuing turn
                        self.must_roll = True
                        self.has_rolled = False
                        self.can_keep = False

                    # Only allow dice selection if we've rolled and haven't kept yet
                    if self.has_rolled and self.can_keep:
                        for die in self.dice:
                            if die.contains_point(mouse_pos):
                                die.kept = not die.kept
                                # If dice were deselected, always allow
                                # If dice were selected, only allow if they make a valid score
                                if die.kept and not self.is_valid_selection():
                                    die.kept = False  # Revert the selection

                    # Handle buttons
                    if self.roll_button.collidepoint(mouse_pos) and self.must_roll:
                        self.roll_dice()
                    elif self.keep_button.collidepoint(mouse_pos) and self.has_rolled and self.can_keep:
                        if self.is_valid_selection():  # Only keep if selection is valid
                            self.keep_dice()
                    elif self.end_turn_button.collidepoint(mouse_pos) and self.has_rolled and self.kept_dice:
                        self.end_turn()

        # Debug print to check states
        print(f"Rolling: {self.is_rolling}, Sound Playing: {self.roll_sound_playing}")

        return False

    def draw(self, screen):
        """Draw game state"""
        screen.fill((50, 100, 50))
        
        # Draw active dice with red border if no score
        for die in self.dice:
            die.draw(self.screen)
            if self.show_no_score:
                # Draw red border around die
                pygame.draw.rect(self.screen, (255, 0, 0), 
                               (die.x - 2, die.y - 2, die.size + 4, die.size + 4), 
                               2)  # 2 pixel width border

        # Draw kept dice
        for die in self.kept_dice:
            die.draw(self.screen)

        # Draw section labels
        active_label = self.font.render("Active Dice", True, (255, 255, 255))
        kept_label = self.font.render("Kept Dice", True, (255, 255, 255))
        self.screen.blit(active_label, (100, 220))
        self.screen.blit(kept_label, (100, 120))

        # Draw buttons based on game state
        if self.must_roll:
            # Show Roll button
            pygame.draw.rect(self.screen, (200, 200, 200), self.roll_button)
            roll_text = self.font.render("Roll", True, (0, 0, 0))
            self.screen.blit(roll_text, (320, 415))
            
            # Only show End Turn if:
            # 1. Player has kept some dice AND
            # 2. Player hasn't rolled yet AND
            # 3. Player either has 1000+ points or will have 1000+ after this turn
            if (self.kept_dice and 
                (self.scores[self.current_player] >= 1000 or 
                 self.turn_score >= 1000)):
                pygame.draw.rect(self.screen, (200, 200, 200), self.end_turn_button)
                end_text = self.font.render("End Turn", True, (0, 0, 0))
                self.screen.blit(end_text, (610, 415))
        
        if self.has_rolled and self.can_keep:  # Only show Keep button during dice selection
            pygame.draw.rect(self.screen, (200, 200, 200), self.keep_button)
            keep_text = self.font.render("Keep", True, (0, 0, 0))
            self.screen.blit(keep_text, (470, 415))

        # Draw scores in bottom left
        for i in range(self.player_count):
            score_text = self.font.render(f"{self.player_names[i]}: {self.scores[i]}", True, (255, 255, 255))
            self.screen.blit(score_text, (50, self.screen.get_height() - 180 + i * 30))  # Start 180px from bottom

        # Draw current player
        current_text = self.font.render(f"Current Player: {self.player_names[self.current_player]}", True, (255, 255, 255))
        self.screen.blit(current_text, (300, 50))

        # Add display for current turn score
        turn_text = self.font.render(f"Turn Score: {self.turn_score}", True, (255, 255, 255))
        self.screen.blit(turn_text, (300, 100))

        # Show if player can take previous score
        if self.can_take_previous_score:
            prev_score_text = self.font.render(f"Can take previous score: {self.turn_score}", 
                                             True, (255, 255, 0))
            self.screen.blit(prev_score_text, (300, 150))

        # Show minimum score warning if needed
        if self.scores[self.current_player] < 1000:
            min_score_text = self.font.render("Need 1000 to keep score", True, (255, 100, 100))
            text_width = min_score_text.get_width()
            self.screen.blit(min_score_text, (self.screen.get_width() - text_width - 20, 20))

        # Show "No Score!" text when applicable
        if self.show_no_score:
            no_score_text = self.font.render("No Score!", True, (255, 0, 0))
            self.screen.blit(no_score_text, (350, 150)) 

        # Show option to take previous score if eligible
        if (self.must_roll and not self.has_rolled and 
            self.scores[self.current_player] >= 1000 and 
            self.previous_turn_score > 0):
            pygame.draw.rect(self.screen, (50, 50, 0), self.take_score_button)  # Dark yellow background
            take_score_text = self.font.render(
                f"Take previous score: {self.previous_turn_score}", 
                True, (255, 255, 0))  # Bright yellow text
            # Center the text on the button
            text_rect = take_score_text.get_rect(center=self.take_score_button.center)
            self.screen.blit(take_score_text, text_rect)

        # Draw red borders around dice when busting
        if self.show_bust:
            for die in self.dice:
                if die.kept:
                    pygame.draw.rect(self.screen, (255, 0, 0), 
                                   (die.x - 2, die.y - 2, die.size + 4, die.size + 4), 
                                   2)
            # Show "BUST!" text
            bust_text = self.font.render("BUST!", True, (255, 0, 0))
            self.screen.blit(bust_text, (350, 150))

        # Show winner and menu button if game is over
        if self.game_over and self.winner is not None:
            # Dim background
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            s.set_alpha(128)
            s.fill((0, 0, 0))
            self.screen.blit(s, (0, 0))

            # Show winner text
            winner_text = self.font.render(f"{self.player_names[self.winner]} wins!", True, (255, 255, 0))
            text_rect = winner_text.get_rect(center=(self.screen.get_width()//2, 200))
            self.screen.blit(winner_text, text_rect)

            # Draw menu button
            pygame.draw.rect(self.screen, (200, 200, 200), self.menu_button)
            menu_text = self.font.render("Back to Menu", True, (0, 0, 0))
            text_rect = menu_text.get_rect(center=self.menu_button.center)
            self.screen.blit(menu_text, text_rect)

    def roll_dice(self):
        """Handle dice rolling"""
        if not self.dice:  # If no dice left
            if len(self.kept_dice) == 6:  # All dice have been kept
                # Check if rolling all dice would force a bust
                if self.scores[self.current_player] + self.turn_score > 10000:
                    self.show_bust = True
                    self.bust_timer = self.bust_delay
                    self.turn_score = 0
                    self.end_turn()
                    return
                # Return all dice to active area
                self.dice = self.kept_dice
                self.kept_dice = []
                # Reset positions and slots
                self.kept_slots = [False] * 6  # Reset all slots
                x_offset = 100
                for die in self.dice:
                    die.kept = False
                    die.x = x_offset
                    die.y = 250
                    x_offset += 80
                # Only reset roll state, keep turn score
                self.has_rolled = False
            else:
                return

        # Roll available dice
        for die in self.dice:
            die.roll()
        self.must_roll = False
        self.has_rolled = True
        self.rolling = True
        self.can_keep = False  # Will be set to True after rolling animation if no bust

    def has_scoring_dice(self):
        """Check if there are any possible scoring combinations in current roll"""
        values = [die.value for die in self.dice]
        value_counts = {}
        for value in values:
            value_counts[value] = value_counts.get(value, 0) + 1

        # Check for three pairs
        if len(value_counts) == 3 and all(count == 2 for count in value_counts.values()):
            return True

        # Check for straight
        if len(values) == 6 and len(set(values)) == 6:
            return True

        # Check for three or more of a kind
        if any(count >= 3 for count in value_counts.values()):
            return True

        # Check for single 1's and 5's
        return 1 in values or 5 in values

    def is_valid_selection(self):
        """Check if currently selected dice form a valid scoring combination"""
        selected = [die for die in self.dice if die.kept]
        if not selected:
            return False
            
        # Get counts for both selected and all available dice
        all_values = [die.value for die in self.dice]
        all_value_counts = {}
        for value in all_values:
            all_value_counts[value] = all_value_counts.get(value, 0) + 1

        selected_values = [die.value for die in selected]
        selected_counts = {}
        for value in selected_values:
            selected_counts[value] = selected_counts.get(value, 0) + 1

        # Check for straight possibility (all dice different)
        if len(all_values) == 6 and len(set(all_values)) == 6:
            return True

        # Check for three pairs possibility
        pairs_possible = len([v for v, c in all_value_counts.items() if c >= 2]) >= 3
        if pairs_possible:
            return True

        # Check if each selected value belongs to a set of three or more
        for value, count in selected_counts.items():
            if all_value_counts[value] >= 3:
                # This value has three or more available, allow it
                continue
            elif value in [1, 5]:
                # 1's and 5's always allowed
                continue
            else:
                # This value doesn't have three available and isn't 1 or 5
                return False

        return True

    def keep_dice(self):
        """Handle keeping current dice selection"""
        kept = [die for die in self.dice if die.kept]
        if not kept:
            return

        potential_score = self.calculate_score(kept)
        if potential_score == 0:
            return

        # Check for bust
        if self.scores[self.current_player] + self.turn_score + potential_score > 10000:
            self.show_bust = True
            self.bust_timer = self.bust_delay
            self.turn_score = 0
            self.end_turn()
            return

        # Add score and move kept dice to kept area
        self.turn_score += potential_score
        
        # Find available slots and move dice to them
        for die in kept:
            # Find first empty slot
            for i in range(6):
                if not self.kept_slots[i]:
                    self.kept_slots[i] = True
                    die.kept = True
                    die.x = self.kept_dice_x + (i * self.kept_dice_spacing)
                    die.y = self.kept_dice_y
                    self.kept_dice.append(die)
                    self.dice.remove(die)
                    break

        # Reset selection state of remaining dice
        for die in self.dice:
            die.kept = False

        self.must_roll = True
        self.can_keep = False

    def end_turn(self):
        """Handle end of player's turn"""
        if self.has_rolled:
            # Store info for next player before resetting
            self.previous_turn_score = self.turn_score
            self.previous_dice_count = len(self.dice)
            # Store kept dice state
            self.previous_kept_dice = self.kept_dice[:]  # Make a copy
            self.previous_kept_slots = self.kept_slots[:]

            # Update score if over 1000 or already over 1000
            if self.scores[self.current_player] >= 1000 or self.turn_score >= 1000:
                self.scores[self.current_player] += self.turn_score
                # Check for winner
                if self.scores[self.current_player] >= 10000:
                    self.game_over = True
                    self.winner = self.current_player
                    return

            # Reset all dice and positions
            self.dice = []
            self.kept_dice = []  # Clear kept dice
            self.kept_slots = [False] * 6  # Reset slots
            x_offset = 100
            for i in range(6):
                die = Die(x_offset, 250)
                self.dice.append(die)
                x_offset += 80

            # Next player
            self.current_player = (self.current_player + 1) % self.player_count
            self.turn_score = 0
            self.must_roll = True
            self.has_rolled = False
            self.can_keep = False

    def calculate_score(self, dice_to_check=None):
        """Calculate score based on kept dice"""
        if dice_to_check is None:
            dice_to_check = [die for die in self.dice if die.kept]
        
        kept_dice = [die.value for die in dice_to_check]
        if not kept_dice:
            return 0

        score = 0
        value_counts = {}
        for value in kept_dice:
            value_counts[value] = value_counts.get(value, 0) + 1

        # Check for three pairs
        if len(value_counts) == 3 and all(count == 2 for count in value_counts.values()):
            return 1500

        # Check for straight (1-6)
        if len(kept_dice) == 6 and len(set(kept_dice)) == 6:
            return 1500

        # Handle three of a kind and extras
        for value, count in value_counts.items():
            if count >= 3:
                # Special case for three 1's
                if value == 1:
                    score += 1000 * (count - 2)  # 1000 for first three, then 1000 each
                else:
                    score += (value * 100) * (count - 2)  # value*100 for first three, then value*100 each

        # Add remaining single 1's and 5's
        for value, count in value_counts.items():
            remaining = count if count < 3 else 0
            if value == 1:
                score += 100 * remaining
            elif value == 5:
                score += 50 * remaining

        return score

    def draw_game_state(self):
        """Draw all game elements on the screen"""
        # Draw active dice with red border if no score
        for die in self.dice:
            die.draw(self.screen)
            if self.show_no_score:
                # Draw red border around die
                pygame.draw.rect(self.screen, (255, 0, 0), 
                               (die.x - 2, die.y - 2, die.size + 4, die.size + 4), 
                               2)  # 2 pixel width border

        # Draw kept dice
        for die in self.kept_dice:
            die.draw(self.screen)

        # Draw section labels
        active_label = self.font.render("Active Dice", True, (255, 255, 255))
        kept_label = self.font.render("Kept Dice", True, (255, 255, 255))
        self.screen.blit(active_label, (100, 220))
        self.screen.blit(kept_label, (100, 120))

        # Draw buttons based on game state
        if self.must_roll:
            # Show Roll button
            pygame.draw.rect(self.screen, (200, 200, 200), self.roll_button)
            roll_text = self.font.render("Roll", True, (0, 0, 0))
            self.screen.blit(roll_text, (320, 415))
            
            # Only show End Turn if:
            # 1. Player has kept some dice AND
            # 2. Player hasn't rolled yet AND
            # 3. Player either has 1000+ points or will have 1000+ after this turn
            if (self.kept_dice and 
                (self.scores[self.current_player] >= 1000 or 
                 self.turn_score >= 1000)):
                pygame.draw.rect(self.screen, (200, 200, 200), self.end_turn_button)
                end_text = self.font.render("End Turn", True, (0, 0, 0))
                self.screen.blit(end_text, (610, 415))
        
        if self.has_rolled and self.can_keep:  # Only show Keep button during dice selection
            pygame.draw.rect(self.screen, (200, 200, 200), self.keep_button)
            keep_text = self.font.render("Keep", True, (0, 0, 0))
            self.screen.blit(keep_text, (470, 415))

        # Draw scores
        for i in range(self.player_count):
            score_text = self.font.render(f"{self.player_names[i]}: {self.scores[i]}", True, (255, 255, 255))
            self.screen.blit(score_text, (50, self.screen.get_height() - 180 + i * 30))  # Start 180px from bottom

        # Draw current player
        current_text = self.font.render(f"Current Player: {self.player_names[self.current_player]}", True, (255, 255, 255))
        self.screen.blit(current_text, (300, 50))

        # Add display for current turn score
        turn_text = self.font.render(f"Turn Score: {self.turn_score}", True, (255, 255, 255))
        self.screen.blit(turn_text, (300, 100))

        # Show if player can take previous score
        if self.can_take_previous_score:
            prev_score_text = self.font.render(f"Can take previous score: {self.turn_score}", 
                                             True, (255, 255, 0))
            self.screen.blit(prev_score_text, (300, 150))

        # Show minimum score warning if needed
        if self.scores[self.current_player] < 1000:
            min_score_text = self.font.render("Need 1000 to keep score", True, (255, 100, 100))
            text_width = min_score_text.get_width()
            self.screen.blit(min_score_text, (self.screen.get_width() - text_width - 20, 20))

        # Show "No Score!" text when applicable
        if self.show_no_score:
            no_score_text = self.font.render("No Score!", True, (255, 0, 0))
            self.screen.blit(no_score_text, (350, 150)) 

    def check_potential_bust(self):
        """Check if keeping all possible scoring dice would cause a bust"""
        # Get all dice that could be kept
        potential_kept = []
        for die in self.dice:
            die.kept = True
            if self.is_valid_selection():
                potential_kept.append(die)
            die.kept = False

        # Calculate potential score
        potential_score = self.calculate_score(potential_kept)
        if self.scores[self.current_player] + self.turn_score + potential_score > 10000:
            self.show_bust = True
            self.bust_timer = self.bust_delay
            self.turn_score = 0
            self.end_turn()
            return True
        return False 

    def start_roll(self):
        self.roll_sound.play()
        # ... existing roll code ... 