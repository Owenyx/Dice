import pygame
import random
import math

class Die:
    # Class-level variables
    roll_sound = None
    speed_multiplier = 1.0  # Default speed multiplier
    
    def __init__(self, x, y):
        """
        Initialize a single die
        Args:
            x (int): X position on screen
            y (int): Y position on screen
        """
        self.size = 60
        self.x = x
        self.y = y
        self.value = 1  # Current face value of the die
        self.kept = False  # Whether the die has been kept for scoring
        self.rolling = False  # Whether the die is currently rolling
        self.roll_frames = 0  # Animation frame counter
        self.max_roll_frames = 90  # Base frames (will be adjusted by speed)
        # Add random extra frames between 0-120 (0-2 additional seconds)
        self.extra_frames = 0
        # 3D effect attributes
        self.scale = 1.0
        self.rotation = 0
        self.bounce_height = 0
        
        # Initialize sound if not already loaded
        if Die.roll_sound is None:
            try:
                Die.roll_sound = pygame.mixer.Sound('sounds/dice_roll.wav')
                Die.roll_sound.set_volume(0.3)
            except:
                print("Warning: Could not load dice roll sound")

    def roll(self):
        """Start the rolling animation if the die isn't kept"""
        if not self.kept:
            self.rolling = True
            self.roll_frames = 0
            self.extra_frames = random.randint(0, 120)  # 0-2 additional seconds
            if Die.roll_sound:
                Die.roll_sound.play()

    def update(self):
        """Update the die's animation state and value"""
        if self.rolling:
            if Die.speed_multiplier == float('inf'):
                # Instant mode - skip animation
                self.rolling = False
                self.value = random.randint(1, 6)
                self.scale = 1.0
                self.bounce_height = 0
                self.rotation = 0
            else:
                # Normal update with speed adjustment
                self.roll_frames += 1 * Die.speed_multiplier
                total_frames = self.max_roll_frames + self.extra_frames
                if self.roll_frames < total_frames:
                    # Animations
                    self.scale = 1.0 + 0.2 * abs(math.sin(self.roll_frames * 0.1))  # Adjusted frequency
                    self.bounce_height = 20 * abs(math.sin(self.roll_frames * 0.08))  # Adjusted frequency
                    self.rotation = self.roll_frames * 6  # Adjusted rotation speed
                    if self.roll_frames % 4 == 0:  # Change value more frequently
                        self.value = random.randint(1, 6)
                else:
                    self.rolling = False
                    self.scale = 1.0
                    self.bounce_height = 0
                    self.rotation = 0
        
    def draw(self, screen):
        """Draw the die with 3D effects"""
        # Calculate transformed size and position
        scaled_size = int(self.size * self.scale)
        x_offset = (scaled_size - self.size) // 2
        y_offset = (scaled_size - self.size) // 2
        
        # Apply bounce offset
        draw_y = self.y - self.bounce_height
        
        # Draw die background with perspective skew
        color = (200, 200, 200) if not self.kept else (150, 150, 150)
        center_x = self.x + self.size // 2
        center_y = draw_y + self.size // 2
        
        points = [
            (center_x - scaled_size//2, center_y - scaled_size//2),
            (center_x + scaled_size//2, center_y - scaled_size//2),
            (center_x + scaled_size//2, center_y + scaled_size//2),
            (center_x - scaled_size//2, center_y + scaled_size//2)
        ]
        
        # Rotate points around center
        angle_rad = math.radians(self.rotation)
        rotated_points = []
        for px, py in points:
            dx = px - center_x
            dy = py - center_y
            rotated_x = center_x + (dx * math.cos(angle_rad) - dy * math.sin(angle_rad))
            rotated_y = center_y + (dx * math.sin(angle_rad) + dy * math.cos(angle_rad))
            rotated_points.append((int(rotated_x), int(rotated_y)))
        
        pygame.draw.polygon(screen, color, rotated_points)
        
        # Draw dots with transformation
        if not self.rolling or self.roll_frames > self.max_roll_frames // 2:
            dot_color = (0, 0, 0)
            dot_radius = int(5 * self.scale)
            positions = self.get_dot_positions()
            
            for pos in positions[self.value - 1]:
                # Calculate position relative to die center
                dx = pos[0] - self.size//2
                dy = pos[1] - self.size//2
                
                # Apply rotation and scale transformations
                rotated_x = center_x + (dx * math.cos(angle_rad) - dy * math.sin(angle_rad)) * self.scale
                rotated_y = center_y + (dx * math.sin(angle_rad) + dy * math.cos(angle_rad)) * self.scale
                
                pygame.draw.circle(screen, dot_color, (int(rotated_x), int(rotated_y)), dot_radius)

    def _get_rotated_rect(self, x, y, width, height, angle):
        """Helper method to get rotated rectangle points"""
        angle_rad = math.radians(angle)
        points = [
            (x, y),
            (x + width * math.cos(angle_rad), y + width * math.sin(angle_rad)),
            (x + width * math.cos(angle_rad) - height * math.sin(angle_rad),
             y + width * math.sin(angle_rad) + height * math.cos(angle_rad)),
            (x - height * math.sin(angle_rad), y + height * math.cos(angle_rad))
        ]
        return [(int(px), int(py)) for px, py in points]

    def get_dot_positions(self):
        """
        Returns the positions of dots for each die value (1-6)
        Returns:
            list: List of coordinate lists for each die value
        """
        center = self.size // 2
        offset = self.size // 4
        
        return [
            # 1
            [(center, center)],
            # 2
            [(center - offset, center - offset), (center + offset, center + offset)],
            # 3
            [(center - offset, center - offset), (center, center), (center + offset, center + offset)],
            # 4
            [(center - offset, center - offset), (center + offset, center - offset),
             (center - offset, center + offset), (center + offset, center + offset)],
            # 5
            [(center - offset, center - offset), (center + offset, center - offset),
             (center, center),
             (center - offset, center + offset), (center + offset, center + offset)],
            # 6
            [(center - offset, center - offset), (center + offset, center - offset),
             (center - offset, center), (center + offset, center),
             (center - offset, center + offset), (center + offset, center + offset)]
        ]

    def contains_point(self, pos):
        """
        Check if a point (e.g., mouse click) is within the die's bounds
        Args:
            pos (tuple): (x, y) position to check
        Returns:
            bool: True if position is within die's bounds
        """
        return (self.x <= pos[0] <= self.x + self.size and 
                self.y <= pos[1] <= self.y + self.size) 