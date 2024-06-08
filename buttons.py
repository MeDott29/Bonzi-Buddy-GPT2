import pygame.font
import pygame


class Button:
    """Class for creating the buttons in the BonziBUDDY window."""

    def __init__(self, bonzi, msg):
        """Initialize button attributes."""
        self.window = bonzi.window
        self.window_rect = self.window.get_rect()

        # Button dimensions
        self.width, self.height = 100, 50
        self.button_color = (255, 255, 255)  # white
        self.text_color = (0, 0, 0)  # black
        self.font = pygame.font.SysFont(None, 24)  # default font, size 24

        # Build the button's rect object and align it
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.topleft = self.window_rect.topleft

        # Give some space from edge of window
        self.spacer_x = 10
        self.spacer_y = 10
        self.rect.x += self.spacer_x
        self.rect.y += self.spacer_y

        # Message for the button
        self.msg = msg  # store message parameter to use when looping through buttons
        self.prep_msg(msg)

    def prep_msg(self, msg):
        """Turn message into a rendered image and center text on the button."""
        self.msg_image = self.font.render(msg, True, self.text_color, self.button_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def draw_button(self):
        """Draw button and message to screen."""
        self.window.fill(self.button_color, self.rect)
        self.window.blit(self.msg_image, self.msg_image_rect)

