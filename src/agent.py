import random
import math
import pygame
from constants import *

class Agent:
    # A counter to assign unique IDs to agents
    _next_id = 0

    def __init__(self, x, y, agent_type, color, speed):
        self.id = Agent._next_id # Assign a unique ID
        Agent._next_id += 1

        self.x = x  # World X-coordinate
        self.y = y  # World Y-coordinate
        self.type = agent_type # 'prey' or 'predator'
        self.color = color
        self.radius = AGENT_RADIUS
        self.speed = speed

        # New: Agent's facing angle (radians)
        # 0 radians is typically right (positive X-axis)
        # pi/2 is up (positive Y-axis in math, but negative Y in Pygame screen coords)
        self.angle = random.uniform(0, 2 * math.pi) 
        
        # Timer for changing direction
        self.direction_change_timer = random.randint(0, DIRECTION_CHANGE_INTERVAL)

    def update_direction(self):
        """
        Randomly updates the agent's facing angle.
        This will be replaced by NN output later.
        """
        self.angle = random.uniform(0, 2 * math.pi)

    def move(self):
        """
        Updates the agent's position based on its speed and current facing angle.
        """
        # Calculate movement components based on angle
        # math.cos(angle) gives the x-component of a unit vector at that angle
        # math.sin(angle) gives the y-component
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, surface, camera_x, camera_y, zoom_level):
        """
        Draws the agent on the provided Pygame surface,
        converting its world coordinates to screen coordinates relative to the surface's content area.
        Also draws a small line to indicate facing direction.
        """
        # Convert world coordinates to screen coordinates relative to the surface's top-left (0,0)
        screen_x = int((self.x - camera_x) * zoom_level + SIM_CONTENT_WIDTH / 2)
        screen_y = int((self.y - camera_y) * zoom_level + (SCREEN_HEIGHT - 2 * SIM_AREA_PADDING) / 2) 
        
        # Scale the radius for drawing
        screen_radius = int(self.radius * zoom_level)
        
        # Only draw if the agent is somewhat visible within the simulation content area
        if -screen_radius < screen_x < SIM_CONTENT_WIDTH + screen_radius and \
           -screen_radius < screen_y < (SCREEN_HEIGHT - 2 * SIM_AREA_PADDING) + screen_radius:
            pygame.draw.circle(surface, self.color, (screen_x, screen_y), screen_radius)

            # if zoom is > 5, draw direction & cone
            if zoom_level > 5:
                line_length = screen_radius * 8 
                end_x = screen_x + int(line_length * math.cos(self.angle))
                end_y = screen_y + int(line_length * math.sin(self.angle))
                pygame.draw.line(surface, WHITE, (screen_x, screen_y), (end_x, end_y), 1)

            # if zoom is > 11, draw the agent's ID for debugging purposes
            if zoom_level > 11:
                id_text = str(self.id)
                font = pygame.font.Font(None, 16)  # Default font, size 16
                id_surface = font.render(id_text, True, WHITE)
                id_rect = id_surface.get_rect(center=(screen_x, screen_y))
                surface.blit(id_surface, id_rect)
