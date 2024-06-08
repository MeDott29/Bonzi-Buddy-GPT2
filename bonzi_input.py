import pygame
import textwrap
from chatbubble import ChatBubble


class InputBox:
    """A class for creating a user input box in the BonziBUDDY window."""
    def __init__(self, bonzi, x, y, width, height, text='Say something...'):
        """Initialize input box attributes."""
        self.bonzi = bonzi
        self.settings = bonzi.settings
        self.window = bonzi.window
        self.window_rect = self.window.get_rect()

        self.rect = pygame.Rect(x, y, width, height)
        self.color = (255, 255, 255)
        self.text = text
        self.text_color = (0, 0, 0)
        self.font = pygame.font.Font(None, 32)
        self.txt_surface = self.font.render(text, True, self.text_color)
        self.active = False
        self.processing_tts = False

        # Align with middle bottom of window, space by 10 pixels
        self.rect.midbottom = self.window_rect.midbottom
        self.rect.y -= 10

        # Character limit
        self.char_limit = 70

        # Set line character limit
        self.line_char_limit = 35

    def handle_event(self, event):
        """Handle events for the input box."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If user clicked on input box
            if self.rect.collidepoint(event.pos):
                # Clear input box, set to active
                self.text = ''
                self.active = not self.active
            else:
                self.text = "Say something..."
                self.active = False

            self.txt_surface = self.font.render(self.text, True, self.text_color)

            # Change the color of the input box when clicked
            if self.active:
                self.color = (200, 200, 200)
            else:
                self.color = (255, 255, 255)

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    # Only start a response if the TTS engine is finished
                    if not self.processing_tts:
                        self.processing_tts = True
                        self.bonzi.current_animation = "talking"
                        response = self.bonzi.chatbot.get_response(self.text)
                        self.bonzi.chat_bubble = ChatBubble(self, str(response))
                        self.text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(self.text) < self.char_limit:
                        self.text += event.unicode

                # Update text as user types
                self.txt_surface = self.font.render(self.text, True, self.text_color)

    def draw_box(self):
        """Draw the input box to the screen."""
        # Draw the box
        pygame.draw.rect(self.window, self.color, self.rect)

        # Wrap the text
        wrapped_text = textwrap.fill(self.text, self.line_char_limit)

        # Draw the text onto the box with a spacer
        lines = wrapped_text.split('\n')
        for i, line in enumerate(lines):
            self.window.blit(self.font.render(line, True, self.text_color),
                             (self.rect.x + 5, self.rect.y + 5 + i * 32))
