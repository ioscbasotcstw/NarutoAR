import pygame


class Toggle:
    def __init__(self, x, y, width, height, starting_state=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.state = starting_state  # True = ON, False = OFF
        
        self.padding = 4
        self.radius = height // 2
        self.circle_radius = self.radius - self.padding
        self.circle_y = y + self.radius
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                return True
        return False

    def draw(self, surface):
        if self.state:
            bg_color = (76, 217, 100)  # Green
            circle_x = self.rect.right - self.radius
        else:
            bg_color = (150, 150, 150) # Gray
            circle_x = self.rect.left + self.radius
            
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (circle_x, self.circle_y), self.circle_radius)