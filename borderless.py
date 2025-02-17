#!/usr/bin/env python3
import os
import sys
import glob
import re
import threading
import textwrap
import requests
from dotenv import load_dotenv
import pyttsx3

from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout)

# Load API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file.")

### SETTINGS ###
class Settings:
    """Manage settings for BonziBUDDY."""
    def __init__(self):
        self.window_width = 400   # smaller window for the floating assistant
        self.window_height = 500
        self.background_color = QColor(0, 0, 0, 0)  # fully transparent
        self.color_screen = "#04fcfc"  # color key if needed
        # Voice settings for TTS
        self.rate = 225  
        self.volume = 1.0  

### ANIMATIONS ###
class Animation:
    """Handles Bonzi's animations by loading BMP frames from folders."""
    def __init__(self):
        # Mapping animation names to sorted list of frame filenames.
        self.animations = {
            "idle": sorted(glob.glob("idle/*.bmp")),
            "arrive": sorted(glob.glob("arrive/*.bmp")),
            "goodbye": sorted(glob.glob("goodbye/*.bmp")),
            "backflip": sorted(glob.glob("backflip/*.bmp")),
            "glasses": sorted(glob.glob("glasses/*.bmp")),
            "wave": sorted(glob.glob("wave/*.bmp")),
            "talking": sorted(glob.glob("talking/*.bmp")),
            "nothing": ["idle/0999.bmp"]
        }

    def get_animation(self, command):
        """Return list of frame file paths for a given animation."""
        return self.animations.get(command, self.animations["idle"])

### CHATBOT USING OPENAI API ###
class BonziChat:
    """Handles chatbot logic via the OpenAI API."""
    def __init__(self, parent):
        self.parent = parent  # reference to BonziWindow
        self.api_key = OPENAI_API_KEY
        self.system_prompt = (
            "You are Bonzi Buddy, a friendly desktop assistant. "
            "Your available animations are: idle, arrive, goodbye, backflip, glasses, wave, talking. "
            "When you want to trigger an animation, output a command in the format /animation:<animation_name> "
            "with no extra text. Otherwise, provide a normal text response."
        )
        self.engine = pyttsx3.init()

    def get_response(self, user_text):
        """Call the OpenAI API and return the response text."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_text}
        ]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "o3-mini",
            "messages": messages
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
        except Exception as e:
            print("Error calling OpenAI API:", e)
            return f"Error calling API: {e}"
        result = response.json()
        reply = result["choices"][0]["message"]["content"].strip()

        # Check for an animation command in the response.
        anim_match = re.search(r"/animation:(\w+)", reply)
        if anim_match:
            animation_name = anim_match.group(1)
            self.parent.set_animation(animation_name)
            # Return empty text (chat bubble not shown)
            return ""
        else:
            return reply

    def text_to_speech(self, response_text):
        """Perform text-to-speech conversion."""
        voices = self.engine.getProperty("voices")
        # Attempt to use Microsoft David if available
        for voice in voices:
            if "david" in voice.name.lower():
                self.engine.setProperty("voice", voice.id)
                break
        self.engine.setProperty("rate", self.parent.settings.rate)
        self.engine.setProperty("volume", self.parent.settings.volume)
        self.engine.say(response_text)
        self.engine.runAndWait()
        # Mark TTS as done.
        self.parent.processing_tts = False

### CHAT BUBBLE (Overlay Text) ###
class ChatBubble(QWidget):
    """Displays a chat bubble with text above Bonzi."""
    def __init__(self, parent, text):
        super().__init__(parent)
        self.text = text
        self.padding = 10
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: rgba(255,255,255,200); border-radius: 10px;")
        self.label = QLabel(text, self)
        self.label.setStyleSheet("color: black;")
        self.label.setWordWrap(True)
        self.adjustSize()

    def update_text(self, text):
        self.text = text
        self.label.setText(text)
        self.adjustSize()

### MAIN WINDOW ###
class BonziWindow(QMainWindow):
    """Main window for the floating Bonzi assistant."""
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.setFixedSize(self.settings.window_width, self.settings.window_height)
        # Frameless, transparent, always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Variables for dragging the window
        self.drag_position = QPoint()

        # Animation and state
        self.animation_manager = Animation()
        self.current_animation = "arrive"
        self.frames = self.animation_manager.get_animation(self.current_animation)
        self.current_frame_index = 0
        self.processing_tts = False

        # Set up chatbot
        self.chatbot = BonziChat(self)

        # Central widget holds the Bonzi image, input field, and buttons.
        self.central_widget = QWidget(self)
        self.central_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setCentralWidget(self.central_widget)

        # Layouts
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.main_layout.addStretch()

        # Label for Bonzi animation
        self.image_label = QLabel(self)
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.image_label, alignment=Qt.AlignHCenter)

        # Chat bubble (initially hidden)
        self.chat_bubble = None

        # Input field and buttons container
        self.control_container = QWidget(self)
        self.control_layout = QHBoxLayout(self.control_container)
        self.control_layout.setContentsMargins(5, 5, 5, 5)

        # Text input for chat
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Say something...")
        self.input_field.returnPressed.connect(self.handle_input)
        self.control_layout.addWidget(self.input_field)

        # Example buttons
        self.btn_hello = QPushButton("Say Hello", self)
        self.btn_trick = QPushButton("Do a Trick", self)
        self.btn_cool = QPushButton("Be Cool", self)
        self.btn_hello.clicked.connect(lambda: self.set_animation("wave"))
        self.btn_trick.clicked.connect(lambda: self.set_animation("backflip"))
        self.btn_cool.clicked.connect(lambda: self.set_animation("glasses"))
        self.control_layout.addWidget(self.btn_hello)
        self.control_layout.addWidget(self.btn_trick)
        self.control_layout.addWidget(self.btn_cool)

        self.main_layout.addWidget(self.control_container)

        # Timer to update animation frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(120)  # adjust frame rate (milliseconds)

    def set_animation(self, anim_name):
        """Set the current animation and reset frame index."""
        self.current_animation = anim_name
        self.frames = self.animation_manager.get_animation(anim_name)
        self.current_frame_index = 0

    def update_animation(self):
        """Cycle through animation frames and update the image."""
        if not self.frames:
            return

        # Loop frames for "talking" animation until TTS is done.
        if self.current_animation == "talking" and self.processing_tts:
            frame_path = self.frames[self.current_frame_index]
            # Example: if a certain frame name is reached, loop back a few frames.
            if "0040.bmp" in frame_path and self.current_frame_index > 0:
                self.current_frame_index -= 1
            else:
                self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
        else:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)

        frame_path = self.frames[self.current_frame_index]
        if os.path.exists(frame_path):
            pixmap = QPixmap(frame_path)
            # Set the color key if needed (you might have to adjust for your images)
            # Here we assume the images already have transparent backgrounds.
            self.image_label.setPixmap(pixmap)
            self.image_label.setFixedSize(pixmap.size())
        else:
            self.image_label.clear()

        # Update chat bubble if it exists.
        if self.chat_bubble:
            self.chat_bubble.move(self.image_label.x(), self.image_label.y() - self.chat_bubble.height() - 10)
            self.chat_bubble.raise_()

    def handle_input(self):
        """Handle when the user presses Enter in the input field."""
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        # Set talking animation.
        self.set_animation("talking")
        self.processing_tts = True

        # Start API call and TTS in a separate thread.
        def process_text():
            response = self.chatbot.get_response(text)
            if response:
                # Show chat bubble with the response.
                self.show_chat_bubble(response)
            self.chatbot.text_to_speech(response)
            # After TTS, revert to idle animation.
            self.set_animation("idle")

        threading.Thread(target=process_text, daemon=True).start()

    def show_chat_bubble(self, text):
        """Display a chat bubble above Bonzi with the given text."""
        if self.chat_bubble is None:
            self.chat_bubble = ChatBubble(self, text)
        else:
            self.chat_bubble.update_text(text)
        # Position the bubble above the Bonzi image.
        self.chat_bubble.adjustSize()
        bubble_x = self.image_label.x() + (self.image_label.width() - self.chat_bubble.width()) // 2
        bubble_y = self.image_label.y() - self.chat_bubble.height() - 10
        self.chat_bubble.move(bubble_x, bubble_y)
        self.chat_bubble.show()

    # Allow dragging the window.
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    # Optional: paint a transparent background (not strictly necessary)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.settings.background_color)

def main():
    app = QApplication(sys.argv)
    bonzi = BonziWindow()
    bonzi.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    print("Starting BonziBUDDY... Enjoy your new desktop companion!")
    main()
