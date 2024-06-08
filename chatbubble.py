import pygame
import textwrap


class ChatBubble:
    """A class for creating chat bubbles above Bonzi."""

    def __init__(self, bonzi, text):
        self.bonzi = bonzi
        self.text = text

        # Create a font object to render the text, None is the default font
        self.font = pygame.font.Font(None, 24)

        # Wrap the text so chat bubble looks nicer
        lines = self.wrap_text(self.text, 20)

        # Get width and height of text render
        if lines:
            self.text_width, self.text_height = self.font.size(max(lines, key=len))
        else:
            self.text_width, self.text_height = self.font.size("")

        # Create a Surface to display text on with the dimensions of the text plus some padding
        self.padding = 20
        self.text_surface = pygame.Surface(
            (self.text_width + 2 * self.padding, len(lines) * self.text_height + 2 * self.padding))

        # Set surface color to white
        self.text_surface.fill("white")

        # Color-key white so it's transparent
        self.text_surface.set_colorkey("white")

        # Create a separate surface for the tail
        self.tail_surface = pygame.Surface((20, 20))

        # Make the background of the tail surface transparent
        self.tail_surface.set_colorkey((0, 0, 0))

        # Draw the chat bubble tail on the tail surface
        pygame.draw.polygon(self.tail_surface, (255, 255, 255), [(10, 0), (0, 20), (20, 20)])

        # Rotate the tail surface by 180 degrees
        self.tail_surface = pygame.transform.rotate(self.tail_surface, 180)

    def wrap_text(self, text, max_width):
        """Wrap text to fit within a certain width."""
        # Wrap the text to fit within the specified width
        wrapper = textwrap.TextWrapper(width=max_width)
        wrapped_text = wrapper.wrap(text)

        return wrapped_text

    def draw_bubble(self):
        """Draw the chat bubble box and tail with the text above Bonzi."""
        # Render each line and blit onto text surface
        lines = self.wrap_text(self.text, 20)
        for i, line in enumerate(lines):
            line_surface = self.font.render(line, True, (0, 0, 0))
            self.text_surface.blit(line_surface, (self.padding, self.padding + i * self.text_height))

        # Get x and y positions for the chat bubble, centered above Bonzi
        bubble_x = self.bonzi.rect.centerx - self.text_surface.get_width() // 2
        bubble_y = self.bonzi.rect.y - self.text_surface.get_height() - 180

        # Draw the chat bubble rectangle in white
        bubble_rect = pygame.draw.rect(self.bonzi.window, (255, 255, 255),
                                       (bubble_x, bubble_y, self.text_surface.get_width(),
                                        self.text_surface.get_height()))

        # Blit the tail surface onto the window
        self.bonzi.window.blit(self.tail_surface, (bubble_rect.centerx - 10, bubble_rect.bottom))

        # Blit the Surface object onto the chat bubble
        self.bonzi.window.blit(self.text_surface, bubble_rect.topleft)
