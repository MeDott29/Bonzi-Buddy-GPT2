# python library imports
import pygame
import sys

# my imports
from settings import Settings
from animations import Animation
from buttons import Button
from bonzi_input import InputBox
from bonzi_gpt import BonziGPT


class Bonzi:
    """Main class for the simplified BonziBUDDY program."""
    def __init__(self):
        """Initialize the program."""
        pygame.init()

        # Class instances
        self.settings = Settings()  # Look at settings.py to see options
        self.animations = Animation(self)
        self.chatbot = BonziGPT(self, "personality.txt")  # pass the text_file the GPT-2 model will be trained on

        # Create the main window
        self.window = pygame.display.set_mode((self.settings.window_width, self.settings.window_height))
        pygame.display.set_caption(self.settings.window_title)

        # Load background image and scale to window size
        self.background = pygame.image.load(self.settings.background_image)
        self.background = pygame.transform.scale(self.background, (self.settings.window_width, self.settings.window_height))

        # Boolean if program is running
        self.running = True

        # Boolean if exiting program
        self.shutting_down = False

        # Set boolean to True for startup animation
        self.startup = True

        # Create clock for frame rate
        self.clock = pygame.time.Clock()

        # Set current animation frame to 0
        self.current_frame = 0

        # Create buttons
        button_messages = ["Say Hello", "Do a Trick", "Be Cool"]
        self.buttons = [Button(self, msg) for msg in button_messages]

        # Adjust button and message positions
        for i, button in enumerate(self.buttons):
            button.rect.x = button.spacer_x + i * (button.width + button.spacer_x)
            button.prep_msg(button.msg)

        # Keep track of current animation Bonzi is doing
        self.current_animation = None

        # Create a user input box
        self.input_box = InputBox(self, 10, 10, self.settings.input_box_width, self.settings.input_box_height)

        # Initialize Bonzi's rect
        self.rect = None

        # Initialize chat bubble
        self.chat_bubble = None

        # Start a timer for last interaction for idle animation
        self.last_interaction = pygame.time.get_ticks()

    def run_program(self):
        """Runs the program."""
        while self.running:
            self.check_events()
            self.update_screen()
            self.clock.tick(8)

    def update_screen(self):
        """Update the screen to most recent changes."""
        # Redraw the screen
        self.window.blit(self.background, (0, 0))
        self.draw_bonzi(self.current_animation)
        self.input_box.draw_box()

        for button in self.buttons:
            button.draw_button()

        # Draw the chat bubble
        if self.chat_bubble:
            self.chat_bubble.draw_bubble()

        # Show changes
        pygame.display.flip()

    def check_events(self):
        """Check for events in the program."""
        for event in pygame.event.get():
            # Closes the window after Bonzi finishes leaving animation
            if event.type == pygame.QUIT:
                self.startup = False
                self.shutting_down = True
                self.current_frame = 0   # Stop current animation, begin goodbye animation
                self.current_animation = "goodbye"

            # Check for mouse click on buttons
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.check_button_click(mouse_pos)

                # Update last interaction time for any event
                self.last_interaction = pygame.time.get_ticks()

            # Check events for the input box
            self.input_box.handle_event(event)

    def check_button_click(self, mouse_pos):
        """Check if a button was clicked, does action displayed on button."""
        # Only process button clicks after the startup animation is done
        if not self.startup:
            for button in self.buttons:
                if button.rect.collidepoint(mouse_pos):
                    if button.msg == "Say Hello":
                        self.current_animation = "wave"
                    elif button.msg == "Do a Trick":
                        self.current_animation = "backflip"
                    elif button.msg == "Be Cool":
                        self.current_animation = "glasses"

                    # Reset the current frame counter to 0 when a button is clicked
                    self.current_frame = 0

    def draw_bonzi(self, animation_name=None):
        """Take Bonzi's animations and call the function to display them."""

        if self.startup:
            frames = self.animations.get_animation("arrive")
        elif animation_name:
            frames = self.animations.get_animation(animation_name)
        elif pygame.time.get_ticks() - self.last_interaction > 9000:
            frames = self.animations.get_animation("idle")
            self.current_animation = "idle"
        else:
            frames = self.animations.get_animation("nothing")
        self.execute_animation(frames)

    def execute_animation(self, frames):
        """Displays each frame in passed list from draw_bonzi()"""
        if self.current_frame >= len(frames):
            self.current_frame = 0  # Go back to the first frame

            if self.shutting_down:  # Let Bonzi finish his leaving animation before closing program
                sys.exit()

            if self.startup:  # Set False to stop startup animation
                self.startup = False

            # When the animation is finished, go to a neutral frame in between animations.
            default_frame = "idle/0999.bmp"
            self.load_bonzi_image(default_frame)

            if self.current_animation == "idle":
                self.last_interaction = pygame.time.get_ticks()

            self.current_animation = None

        else:
            frame = frames[self.current_frame]
            self.load_bonzi_image(frame)

            # If Bonzi is talking, loop through his speaking frames until he is done
            if self.input_box.processing_tts:
                if "0040.bmp" in frame:   # 0040.bmp is his last speaking frame, move back index if not done speaking
                    self.current_frame -= 5
                else:
                    self.current_frame += 1
            else:
                self.current_frame += 1

    def load_bonzi_image(self, image):
        """Load Bonzi's current image frame, set color key and rect, blit to window."""
        image = pygame.image.load(image)
        image.set_colorkey(self.settings.color_screen)
        self.rect = image.get_rect(center=(self.settings.window_width // 2, self.settings.window_height // 1.4))
        self.window.blit(image, self.rect)


# Run the program
if __name__ == '__main__':
    print("Welcome to BonziBUDDY! The program may take a moment to load.")
    bonzi = Bonzi()
    bonzi.run_program()

