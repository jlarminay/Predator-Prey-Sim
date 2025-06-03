import pygame
import random
from constants import *
from agent import Agent

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Predator-Prey Simulation")
        self.clock = pygame.time.Clock()
        self.running = True

        # Camera state
        self.camera_x = 0
        self.camera_y = 0
        self.zoom_level = MIN_ZOOM_LEVEL # Start at the new max zoom-out level

        # Variables for click-and-drag panning
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        self.mouse_world_x = 0 # New: Stores mouse X position in world coordinates
        self.mouse_world_y = 0 # New: Stores mouse Y position in world coordinates

        # Font for metadata display
        self.font = pygame.font.Font(None, 20) # Default font, size 24

        # Speed control state
        self.current_speed_index = INITIAL_SPEED_INDEX
        self.current_speed_multiplier = SPEED_MULTIPLIERS[self.current_speed_index]
        self.show_grid = False # New: Toggle for grid display
        
        # Speed control button properties
        self.speed_button_rect = pygame.Rect(
            SIM_TOTAL_DISPLAY_WIDTH, # Center button in panel
            SCREEN_HEIGHT - 30 - 16, # 50 pixels from bottom
            109, 30 # Button width and height
        )
        self.grid_button_rect = pygame.Rect(
            SIM_TOTAL_DISPLAY_WIDTH + 117, # Offset to the right of speed button
            SCREEN_HEIGHT - 30 - 16, # Same vertical position as speed button
            109, 30 # Button width and height
        )

        self.agents = []
        self.selected_agent = None
        self.initialize_agents()
        self.clamp_camera() # Clamp camera position immediately after initialization

    def initialize_agents(self):
        """
        Places agents randomly on the 128x128 map.
        The map ranges from -MAP_SIZE/2 to +MAP_SIZE/2 for both X and Y.
        """
        # Reset agent ID counter for fresh simulations
        Agent._next_id = 0 
        for _ in range(PREY_COUNT):
            x = random.uniform(-MAP_SIZE / 2, MAP_SIZE / 2)
            y = random.uniform(-MAP_SIZE / 2, MAP_SIZE / 2)
            self.agents.append(Agent(x, y, 'prey', GREEN, PREY_SPEED))

        for _ in range(PREDATOR_COUNT):
            x = random.uniform(-MAP_SIZE / 2, MAP_SIZE / 2)
            y = random.uniform(-MAP_SIZE / 2, MAP_SIZE / 2)
            self.agents.append(Agent(x, y, 'predator', RED, PREDATOR_SPEED))

    def clamp_camera(self):
        """
        Clamps the camera's position to prevent panning outside the map boundaries.
        The camera's center should not allow the visible area to go beyond the map edges.
        """
        # Calculate half the visible world width/height on screen, based on content area
        half_visible_world_width = (SIM_CONTENT_WIDTH / 2) / self.zoom_level
        half_visible_world_height = ((SCREEN_HEIGHT - 2 * SIM_AREA_PADDING) / 2) / self.zoom_level 

        # Calculate min/max camera X bounds
        x_min_bound = -MAP_SIZE / 2 + half_visible_world_width
        x_max_bound = MAP_SIZE / 2 - half_visible_world_width

        # Calculate min/max camera Y bounds
        y_min_bound = -MAP_SIZE / 2 + half_visible_world_height
        y_max_bound = MAP_SIZE / 2 - half_visible_world_height

        # If the visible area is wider/taller than the map, center the camera
        if x_min_bound > x_max_bound: # Map is smaller than visible area horizontally
            self.camera_x = 0
        else:
            self.camera_x = max(x_min_bound, min(self.camera_x, x_max_bound))

        if y_min_bound > y_max_bound: # Map is smaller than visible area vertically
            self.camera_y = 0
        else:
            self.camera_y = max(y_min_bound, min(self.camera_y, y_max_bound))

    def handle_input(self):
        """
        Processes user input for camera movement (click-and-drag) and zoom.
        Also updates mouse world position and handles button clicks.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: # Press ESC to quit
                    self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if click is within the padded simulation area
                if event.pos[0] < SIM_TOTAL_DISPLAY_WIDTH:
                    if event.button == 1:  # Left mouse button for dragging
                        self.dragging = True
                        self.last_mouse_pos = event.pos # Store current mouse position
                    elif event.button == 3:  # Right mouse button
                        self.select_agent(event.pos)
                
                # Mouse wheel for zooming (applies regardless of where the mouse is)
                if event.button == 4:  # Scroll up (zoom in)
                    self.zoom_level *= ZOOM_FACTOR
                elif event.button == 5:  # Scroll down (zoom out)
                    self.zoom_level /= ZOOM_FACTOR
                
                # Clamp zoom level to prevent extreme values
                self.zoom_level = max(MIN_ZOOM_LEVEL, min(self.zoom_level, MAX_ZOOM_LEVEL))
                # Re-clamp camera position after zoom, as bounds change
                self.clamp_camera() 

                # Check for speed button click
                if self.speed_button_rect.collidepoint(event.pos):
                    self.current_speed_index = (self.current_speed_index + 1) % len(SPEED_MULTIPLIERS)
                    self.current_speed_multiplier = SPEED_MULTIPLIERS[self.current_speed_index]

                # Check for grid toggle button click
                if self.grid_button_rect.collidepoint(event.pos):
                    self.show_grid = not self.show_grid

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button released
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                # Update mouse world position regardless of dragging state
                mouse_x_screen, mouse_y_screen = event.pos

                # Only convert if mouse is within the simulation area
                if mouse_x_screen >= SIM_AREA_PADDING and \
                   mouse_x_screen < SIM_TOTAL_DISPLAY_WIDTH - SIM_AREA_PADDING and \
                   mouse_y_screen >= SIM_AREA_PADDING and \
                   mouse_y_screen < SCREEN_HEIGHT - SIM_AREA_PADDING:
                    
                    # Convert screen coordinates (relative to padded content area) to world coordinates
                    # 1. Adjust for padding offset
                    adjusted_mouse_x = mouse_x_screen - SIM_AREA_PADDING
                    adjusted_mouse_y = mouse_y_screen - SIM_AREA_PADDING

                    # 2. Adjust for screen center offset (relative to SIM_CONTENT_WIDTH/SCREEN_HEIGHT)
                    relative_x = adjusted_mouse_x - SIM_CONTENT_WIDTH / 2
                    relative_y = adjusted_mouse_y - (SCREEN_HEIGHT - 2 * SIM_AREA_PADDING) / 2

                    # 3. Scale by zoom level
                    self.mouse_world_x = relative_x / self.zoom_level + self.camera_x
                    self.mouse_world_y = relative_y / self.zoom_level + self.camera_y
                else:
                    self.mouse_world_x = float('nan') # Set to NaN if outside sim area
                    self.mouse_world_y = float('nan')

                if self.dragging:
                    current_mouse_pos = event.pos
                    # Calculate difference in screen pixels
                    dx_screen = current_mouse_pos[0] - self.last_mouse_pos[0]
                    dy_screen = current_mouse_pos[1] - self.last_mouse_pos[1]

                    # Convert screen pixel difference to world units and update camera
                    self.camera_x -= dx_screen / self.zoom_level
                    self.camera_y -= dy_screen / self.zoom_level
                    
                    self.last_mouse_pos = current_mouse_pos # Update last mouse position
                    self.clamp_camera() # Clamp camera position after panning

    def select_agent(self, mouse_pos):
        """
        Selects an agent based on mouse position.
        This is a placeholder for future functionality.
        """
        # Convert mouse position to world coordinates
        mouse_x, mouse_y = mouse_pos
        relative_x = (mouse_x - SIM_CONTENT_WIDTH / 2) / self.zoom_level + self.camera_x
        relative_y = (mouse_y - (SCREEN_HEIGHT - 2 * SIM_AREA_PADDING) / 2) / self.zoom_level + self.camera_y
        click_range = 30 / self.zoom_level  # Click range scales with zoom level

        # Check if any agent is close to the clicked position
        for agent in self.agents:
            # check distance to agent's position
            distance = ((agent.x - relative_x) ** 2 + (agent.y - relative_y) ** 2) ** 0.5
            if distance < click_range:
                self.selected_agent = agent
                return
        
        self.selected_agent = None  # Reset selection if no agent is close enough

    def update(self):
        """
        Updates the state of all agents, including movement, direction changes, and boundary looping.
        """
        for agent in self.agents:
            # Update direction periodically
            agent.direction_change_timer -= 1
            if agent.direction_change_timer <= 0:
                agent.update_direction()
                agent.direction_change_timer = DIRECTION_CHANGE_INTERVAL

            agent.move()

            # Implement toroidal (looping) boundaries
            # If agent goes beyond right edge, wrap to left
            if agent.x > MAP_SIZE / 2:
                agent.x = -MAP_SIZE / 2
            # If agent goes beyond left edge, wrap to right
            elif agent.x < -MAP_SIZE / 2:
                agent.x = MAP_SIZE / 2
            
            # If agent goes beyond top edge, wrap to bottom
            if agent.y > MAP_SIZE / 2:
                agent.y = -MAP_SIZE / 2
            # If agent goes beyond bottom edge, wrap to top
            elif agent.y < -MAP_SIZE / 2:
                agent.y = MAP_SIZE / 2

    def draw(self):
        """
        Clears the screen and draws all agents and map boundaries,
        then draws the metadata panel.
        """
        # Clear the entire screen first with the background color for the simulation panel
        self.screen.fill(BACKGROUND_COLOR) 

        self.draw_panel()
        self.draw_simulation() # Draw the simulation area with agents
        self.draw_grid() # Draw grid if enabled 

        pygame.display.flip() # Update the full display Surface to the screen

    def draw_simulation(self):
        """
        Draws the simulation area, including agents and map boundaries.
        This method is called within the main draw loop.
        """
        # Create a surface for the simulation content (map and agents)
        simulation_content_surface = pygame.Surface((SIM_CONTENT_WIDTH, SCREEN_HEIGHT - 2 * SIM_AREA_PADDING)) # Adjusted height for padding
        simulation_content_surface.fill(BLACK) # Fill background of the content area

        # Draw agents on the simulation_content_surface
        for agent in self.agents:
            # Pass the content surface for drawing, and the camera/zoom info
            # Agent's draw method now correctly assumes surface's (0,0) is its top-left
            agent.draw(simulation_content_surface, self.camera_x, self.camera_y, self.zoom_level)

            # if an agent is selected, draw a border around it
            if self.selected_agent and agent.id == self.selected_agent.id:
                # Draw a border around the selected agent
                screen_x = int((agent.x - self.camera_x) * self.zoom_level + SIM_CONTENT_WIDTH / 2)
                screen_y = int((agent.y - self.camera_y) * self.zoom_level + (SCREEN_HEIGHT - 2 * SIM_AREA_PADDING) / 2)
                screen_radius = int(agent.radius * self.zoom_level)
                pygame.draw.circle(simulation_content_surface, GOLD, (screen_x, screen_y), screen_radius + 2, 2)
        
        # Blit (copy) the simulation_content_surface onto the main screen, offset by padding
        self.screen.blit(simulation_content_surface, (SIM_AREA_PADDING, SIM_AREA_PADDING))

    def draw_panel(self):
        """
        Draws the metadata panel on the right side of the screen.
        """
        metadata_padding = 16 # Padding for the metadata panel content
        metadata_panel_rect = pygame.Rect(SIM_TOTAL_DISPLAY_WIDTH, 0, METADATA_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, BACKGROUND_COLOR, metadata_panel_rect)

        # Draw an inner rectangle with padding for content within the metadata panel
        metadata_inner_rect = pygame.Rect(
            SIM_TOTAL_DISPLAY_WIDTH, # Offset by total simulation width + padding
            metadata_padding,
            METADATA_PANEL_WIDTH - 2 * metadata_padding,
            SCREEN_HEIGHT - 2 * metadata_padding
        )

        # --- Render Metadata Text ---
        # Calculate text positions within the metadata_inner_rect
        text_start_x = metadata_inner_rect.x
        text_start_y = metadata_inner_rect.y
        line_height = 20
        current_line = 0

        # Current Runtime
        # Get elapsed time in milliseconds
        total_milliseconds = pygame.time.get_ticks()
        # Convert to hh:mm:ss:ms format
        hours = total_milliseconds // 3600000
        minutes = (total_milliseconds % 3600000) // 60000
        seconds = (total_milliseconds % 60000) // 1000
        milliseconds = total_milliseconds % 1000
        runtime_text = self.font.render(f"Runtime: {hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}", True, WHITE)
        self.screen.blit(runtime_text, (text_start_x, text_start_y + current_line * line_height))
        current_line += 1

        # Current Zoom Level
        zoom_text = self.font.render(f"Zoom: {self.zoom_level:.2f}x", True, WHITE)
        self.screen.blit(zoom_text, (text_start_x, text_start_y + current_line * line_height))
        current_line += 1

        # Mouse Position (World Coordinates)
        mouse_pos_text = self.font.render(f"Mouse: ({self.mouse_world_x:.1f}, {self.mouse_world_y:.1f})", True, WHITE)
        self.screen.blit(mouse_pos_text, (text_start_x, text_start_y + current_line * line_height))
        current_line += 1
        current_line += 1 # Add an extra line for spacing

        # Total Agent Count
        total_agents = len(self.agents)
        total_text = self.font.render(f"Total Agents: {total_agents}", True, WHITE)
        self.screen.blit(total_text, (text_start_x, text_start_y + current_line * line_height))
        current_line += 1

        # Count of Prey
        prey_count = sum(1 for agent in self.agents if agent.type == 'prey')
        prey_text = self.font.render(f"Prey: {prey_count}", True, GREEN)
        self.screen.blit(prey_text, (text_start_x, text_start_y + current_line * line_height))
        current_line += 1

        # Count of Predators
        predator_count = sum(1 for agent in self.agents if agent.type == 'predator')
        predator_text = self.font.render(f"Predators: {predator_count}", True, RED)
        self.screen.blit(predator_text, (text_start_x, text_start_y + current_line * line_height))
        current_line += 1
        current_line += 1

        # Selected Agent Info
        if self.selected_agent:
            selected_text = self.font.render(f"ID: {self.selected_agent.id}", True, WHITE)
            self.screen.blit(selected_text, (text_start_x, text_start_y + current_line * line_height))
            current_line += 1

            # Display selected agent's type and position
            agent_type_text = self.font.render(f"Type: {self.selected_agent.type.capitalize()}", True, WHITE)
            self.screen.blit(agent_type_text, (text_start_x, text_start_y + current_line * line_height))
            current_line += 1

            position_text = self.font.render(f"Pos: ({self.selected_agent.x:.2f}, {self.selected_agent.y:.2f})", True, WHITE)
            self.screen.blit(position_text, (text_start_x, text_start_y + current_line * line_height))
            current_line += 1

            speed_text = self.font.render(f"Speed: {self.selected_agent.speed:.2f}", True, WHITE)
            self.screen.blit(speed_text, (text_start_x, text_start_y + current_line * line_height))
            current_line += 1

            angle_text = self.font.render(f"Angle: {self.selected_agent.angle:.2f} rad", True, WHITE)
            self.screen.blit(angle_text, (text_start_x, text_start_y + current_line * line_height))
            current_line += 1
            current_line += 1
        else:
            no_selection_text = self.font.render("No agent selected", True, WHITE)
            self.screen.blit(no_selection_text, (text_start_x, text_start_y + current_line * line_height))
            current_line += 1
            no_selection_text = self.font.render("Right click to select agent", True, WHITE)
            self.screen.blit(no_selection_text, (text_start_x, text_start_y + current_line * line_height))
            current_line += 1
            current_line += 1
            current_line += 1
            current_line += 1
            current_line += 1

        # --- Draw NN Stuff ---
        angle_text = self.font.render(f"NN Stuff", True, WHITE)
        self.screen.blit(angle_text, (text_start_x, text_start_y + current_line * line_height))
        current_line += 1

        # --- Draw Speed Control Button ---
        mouse_pos = pygame.mouse.get_pos()
        button_color = BUTTON_HOVER_COLOR if self.speed_button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, button_color, self.speed_button_rect)
        speed_button_text = self.font.render(f"{self.current_speed_multiplier}x Speed", True, WHITE)
        speed_text_rect = speed_button_text.get_rect(center=self.speed_button_rect.center)
        self.screen.blit(speed_button_text, speed_text_rect)

        # --- Draw Grid Toggle Button ---
        grid_button_color = BUTTON_HOVER_COLOR if self.grid_button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(self.screen, grid_button_color, self.grid_button_rect)
        grid_button_text = self.font.render("Toggle Grid", True, WHITE)
        grid_text_rect = grid_button_text.get_rect(center=self.grid_button_rect.center)
        self.screen.blit(grid_button_text, grid_text_rect)

    def draw_grid(self):
        """
        Draws a grid overlay on the simulation area if enabled.
        The grid is drawn relative to the camera position and zoom level.
        """
        if not self.show_grid:
            return
        
        grid_surface = pygame.Surface((SIM_CONTENT_WIDTH, SCREEN_HEIGHT - 2 * SIM_AREA_PADDING), pygame.SRCALPHA)
        color = (255, 255, 255, 20)
        grid_spacing = 16

        # add vertical grid lines
        for x in range(int(-MAP_SIZE / 2), int(MAP_SIZE / 2) + grid_spacing, grid_spacing):
            screen_x = int((x - self.camera_x) * self.zoom_level + SIM_CONTENT_WIDTH / 2)
            pygame.draw.line(grid_surface, color, (screen_x, 0), (screen_x, SCREEN_HEIGHT - 2 * SIM_AREA_PADDING))

        # add horizontal grid lines
        for y in range(int(-MAP_SIZE / 2), int(MAP_SIZE / 2) + grid_spacing, grid_spacing):
            screen_y = int((y - self.camera_y) * self.zoom_level + (SCREEN_HEIGHT - 2 * SIM_AREA_PADDING) / 2)
            pygame.draw.line(grid_surface, color, (0, screen_y), (SIM_CONTENT_WIDTH, screen_y))

        # add to screen
        self.screen.blit(grid_surface, (SIM_AREA_PADDING, SIM_AREA_PADDING))

    def run(self):
        """
        Main game loop.
        """
        while self.running:
            # pause if the speed multiplier is 0
            if self.current_speed_multiplier == 0:
                self.handle_input()
                continue
            
            self.handle_input()
            self.update()
            # The clock.tick() call is now scaled by the current_speed_multiplier
            self.clock.tick(FPS * self.current_speed_multiplier) 
            self.draw()

        pygame.quit()
