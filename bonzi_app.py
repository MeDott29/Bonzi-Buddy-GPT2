# bonzi_app.py
import os
import sys
import re
import threading
import textwrap
import pygame
import requests
from dotenv import load_dotenv
import pyttsx3

# Load API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file.")

### SETTINGS ###
class Settings:
    """Manage the settings for BonziBUDDY."""
    def __init__(self):
        # Pygame window dimensions
        self.window_width = 800
        self.window_height = 600

        # Window title
        self.window_title = "BonziBUDDY"

        # Instead of a background image, we’ll use a solid color.
        self.background_color = (0, 0, 0)  # Black

        # Color used for colorkey transparency in Bonzi images
        self.color_screen = "#04fcfc"

        # Input box dimensions
        self.input_box_width = 715
        self.input_box_height = 70

        # Voice settings for TTS
        self.rate = 225  # words per minute
        self.volume = 1.0  # 0.0 to 1.0

### ANIMATIONS ###
import glob
class Animation:
    """A class for Bonzi's animations."""
    def __init__(self, bonzi):
        self.bonzi = bonzi
        self.settings = bonzi.settings
        # Dictionary mapping animation names to sorted list of frame filenames.
        self.animations = {
            "idle": sorted(glob.glob("idle/*.bmp")),
            "arrive": sorted(glob.glob("arrive/*.bmp")),
            "goodbye": sorted(glob.glob("goodbye/*.bmp")),
            "backflip": sorted(glob.glob("backflip/*.bmp")),
            "glasses": sorted(glob.glob("glasses/*.bmp")),
            "wave": sorted(glob.glob("wave/*.bmp")),
            "nothing": ["idle/0999.bmp"],
            "talking": sorted(glob.glob("talking/*.bmp"))
        }

    def get_animation(self, command):
        """Return the list of frame filenames for the given animation command."""
        return self.animations.get(command)

### CHATBOT USING OPENAI API ###
class BonziChat:
    """A class for handling the chatbot logic using the OpenAI API via requests."""
    def __init__(self, bonzi):
        self.bonzi = bonzi
        self.api_key = OPENAI_API_KEY
        # The system prompt now includes the list of available animations.
        self.system_prompt = (
            "You are Bonzi Buddy, a friendly desktop assistant. "
            "Your available animations are: idle, arrive, goodbye, backflip, glasses, wave, talking. "
            "When you want to trigger an animation, output a command in the format /animation:<animation_name> "
            "with no extra text. Otherwise, provide a normal text response."
        )
        # Initialize text-to-speech engine.
        self.engine = pyttsx3.init()

    def get_response(self, user_text):
        """Get a response from the OpenAI API."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_text}
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Use the data structure as in the reference documentation.
        data = {
            "model": "o3-mini",
            "messages": messages
        }

        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
        except Exception as e:
            print("Error calling OpenAI API:", e)
            # Return the actual error response or exception message.
            return f"Error calling API: {e}"

        result = response.json()
        reply = result["choices"][0]["message"]["content"].strip()

        # Look for an animation command in the response
        anim_match = re.search(r"/animation:(\w+)", reply)
        if anim_match:
            animation_name = anim_match.group(1)
            # Set the current animation in Bonzi.
            self.bonzi.current_animation = animation_name
            # Return an empty string so nothing is shown in the chat bubble.
            return ""
        else:
            # If no animation command, return the text.
            return reply

    def text_to_speech(self, response_text):
        """Convert the response text into speech."""
        voices = self.engine.getProperty("voices")
        # Attempt to set voice to Microsoft David if available.
        for voice in voices:
            if "david" in voice.name.lower():
                self.engine.setProperty("voice", voice.id)
                break
        self.engine.setProperty("rate", self.bonzi.settings.rate)
        self.engine.setProperty("volume", self.bonzi.settings.volume)
        self.engine.say(response_text)
        self.engine.runAndWait()
        # Reset TTS processing flag
        self.bonzi.input_box.processing_tts = False

### INPUT BOX ###
class InputBox:
    """A class for handling user input in the Bonzi window."""
    def __init__(self, bonzi, x, y, width, height, text='Say something...'):
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

        # Align with middle bottom of window, with a 10-pixel margin.
        self.rect.midbottom = self.window_rect.midbottom
        self.rect.y -= 10

        self.char_limit = 70
        self.line_char_limit = 35

    def handle_event(self, event):
        """Process events for the input box."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.text = ''
                self.active = not self.active
            else:
                self.text = "Say something..."
                self.active = False

            self.txt_surface = self.font.render(self.text, True, self.text_color)
            self.color = (200, 200, 200) if self.active else (255, 255, 255)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                if not self.processing_tts:
                    self.processing_tts = True
                    self.bonzi.current_animation = "talking"
                    # Get response from the API via our BonziChat instance.
                    response = self.bonzi.chatbot.get_response(self.text)
                    # Start TTS in a separate thread.
                    t = threading.Thread(target=self.bonzi.chatbot.text_to_speech, args=(response,))
                    t.daemon = True
                    t.start()
                    # Create chat bubble only if there is response text.
                    if response:
                        self.bonzi.chat_bubble = ChatBubble(self.bonzi, response)
                    self.text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < self.char_limit:
                    self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, self.text_color)

    def draw_box(self):
        """Draw the input box on the screen."""
        pygame.draw.rect(self.window, self.color, self.rect)
        wrapped_text = textwrap.fill(self.text, self.line_char_limit)
        lines = wrapped_text.split('\n')
        for i, line in enumerate(lines):
            self.window.blit(self.font.render(line, True, self.text_color),
                             (self.rect.x + 5, self.rect.y + 5 + i * 32))

### BUTTONS ###
class Button:
    """A class for creating buttons in the Bonzi window."""
    def __init__(self, bonzi, msg):
        self.window = bonzi.window
        self.window_rect = self.window.get_rect()

        self.width, self.height = 100, 50
        self.button_color = (255, 255, 255)
        self.text_color = (0, 0, 0)
        self.font = pygame.font.SysFont(None, 24)

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.topleft = self.window_rect.topleft

        self.spacer_x = 10
        self.spacer_y = 10
        self.rect.x += self.spacer_x
        self.rect.y += self.spacer_y

        self.msg = msg
        self.prep_msg(msg)

    def prep_msg(self, msg):
        """Render the button's message."""
        self.msg_image = self.font.render(msg, True, self.text_color, self.button_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def draw_button(self):
        """Draw the button."""
        self.window.fill(self.button_color, self.rect)
        self.window.blit(self.msg_image, self.msg_image_rect)

### CHAT BUBBLE ###
class ChatBubble:
    """A class for drawing a chat bubble above Bonzi."""
    def __init__(self, bonzi, text):
        self.bonzi = bonzi
        self.text = text
        self.font = pygame.font.Font(None, 24)
        lines = self.wrap_text(self.text, 20)
        if lines:
            self.text_width, self.text_height = self.font.size(max(lines, key=len))
        else:
            self.text_width, self.text_height = self.font.size("")
        self.padding = 20
        self.text_surface = pygame.Surface(
            (self.text_width + 2 * self.padding, len(lines) * self.text_height + 2 * self.padding)
        )
        self.text_surface.fill("white")
        self.text_surface.set_colorkey("white")
        self.tail_surface = pygame.Surface((20, 20))
        self.tail_surface.set_colorkey((0, 0, 0))
        pygame.draw.polygon(self.tail_surface, (255, 255, 255), [(10, 0), (0, 20), (20, 20)])
        self.tail_surface = pygame.transform.rotate(self.tail_surface, 180)

    def wrap_text(self, text, max_width):
        wrapper = textwrap.TextWrapper(width=max_width)
        return wrapper.wrap(text)

    def draw_bubble(self):
        """Draw the chat bubble and tail above Bonzi."""
        lines = self.wrap_text(self.text, 20)
        for i, line in enumerate(lines):
            line_surface = self.font.render(line, True, (0, 0, 0))
            self.text_surface.blit(line_surface, (self.padding, self.padding + i * self.text_height))
        bubble_x = self.bonzi.rect.centerx - self.text_surface.get_width() // 2
        bubble_y = self.bonzi.rect.y - self.text_surface.get_height() - 180
        bubble_rect = pygame.draw.rect(self.bonzi.window, (255, 255, 255),
                                       (bubble_x, bubble_y, self.text_surface.get_width(),
                                        self.text_surface.get_height()))
        self.bonzi.window.blit(self.tail_surface, (bubble_rect.centerx - 10, bubble_rect.bottom))
        self.bonzi.window.blit(self.text_surface, bubble_rect.topleft)

### MAIN BONZI CLASS ###
class Bonzi:
    """The main BonziBUDDY application class."""
    def __init__(self):
        pygame.init()
        self.settings = Settings()
        self.window = pygame.display.set_mode((self.settings.window_width, self.settings.window_height))
        pygame.display.set_caption(self.settings.window_title)
        # Instead of a background image, use a solid color.
        self.background_color = self.settings.background_color

        self.running = True
        self.shutting_down = False
        self.startup = True
        self.clock = pygame.time.Clock()
        self.current_frame = 0

        # Initialize animations, chatbot (using OpenAI API), input box, buttons.
        self.animations = Animation(self)
        self.chatbot = BonziChat(self)
        self.input_box = InputBox(self, 10, 10, self.settings.input_box_width, self.settings.input_box_height)
        button_messages = ["Say Hello", "Do a Trick", "Be Cool"]
        self.buttons = [Button(self, msg) for msg in button_messages]
        for i, button in enumerate(self.buttons):
            button.rect.x = button.spacer_x + i * (button.width + button.spacer_x)
            button.prep_msg(button.msg)
        # current_animation is None unless explicitly set (by API call or button click).
        self.current_animation = None
        self.chat_bubble = None
        self.rect = None
        self.last_interaction = pygame.time.get_ticks()

    def run_program(self):
        """Main loop for the BonziBUDDY application."""
        while self.running:
            self.check_events()
            self.update_screen()
            self.clock.tick(8)

    def update_screen(self):
        """Update the screen with the current state."""
        self.window.fill(self.background_color)
        self.draw_bonzi()
        self.input_box.draw_box()
        for button in self.buttons:
            button.draw_button()
        if self.chat_bubble:
            self.chat_bubble.draw_bubble()
        pygame.display.flip()

    def check_events(self):
        """Check for and process events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.startup = False
                self.shutting_down = True
                self.current_frame = 0
                self.current_animation = "goodbye"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.check_button_click(mouse_pos)
                self.last_interaction = pygame.time.get_ticks()
            self.input_box.handle_event(event)

    def check_button_click(self, mouse_pos):
        """Perform actions based on button clicks."""
        if not self.startup:
            for button in self.buttons:
                if button.rect.collidepoint(mouse_pos):
                    if button.msg == "Say Hello":
                        self.current_animation = "wave"
                    elif button.msg == "Do a Trick":
                        self.current_animation = "backflip"
                    elif button.msg == "Be Cool":
                        self.current_animation = "glasses"
                    self.current_frame = 0

    def draw_bonzi(self):
        """Determine and execute the appropriate animation."""
        if self.startup:
            frames = self.animations.get_animation("arrive")
        # If an API call or button has set an animation (and it isn’t 'idle'),
        # use that animation to override the idle animation.
        elif self.current_animation and self.current_animation != "idle":
            frames = self.animations.get_animation(self.current_animation)
        # If there has been no interaction for a while, default to idle.
        elif pygame.time.get_ticks() - self.last_interaction > 9000:
            frames = self.animations.get_animation("idle")
            self.current_animation = "idle"
        else:
            frames = self.animations.get_animation("nothing")
        self.execute_animation(frames)

    def execute_animation(self, frames):
        """Cycle through frames of the given animation."""
        if self.current_frame >= len(frames):
            self.current_frame = 0
            if self.shutting_down:
                sys.exit()
            if self.startup:
                self.startup = False
            default_frame = "idle/0999.bmp"
            self.load_bonzi_image(default_frame)
            # Reset current_animation to None once a non-idle animation completes.
            if self.current_animation != "idle":
                self.current_animation = None
            if self.current_animation == "idle":
                self.last_interaction = pygame.time.get_ticks()
        else:
            frame = frames[self.current_frame]
            self.load_bonzi_image(frame)
            # For talking animation, loop until TTS is complete.
            if self.input_box.processing_tts:
                if "0040.bmp" in frame:
                    self.current_frame -= 5
                else:
                    self.current_frame += 1
            else:
                self.current_frame += 1

    def load_bonzi_image(self, image_path):
        """Load and display the current Bonzi image frame."""
        image = pygame.image.load(image_path)
        image.set_colorkey(self.settings.color_screen)
        self.rect = image.get_rect(center=(self.settings.window_width // 2, self.settings.window_height // 1.4))
        self.window.blit(image, self.rect)

if __name__ == '__main__':
    print("Welcome to BonziBUDDY! The program may take a moment to load.")
    bonzi = Bonzi()
    bonzi.run_program()
