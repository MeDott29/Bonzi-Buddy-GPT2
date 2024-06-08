class Settings:
    """A class to manage the settings for BonziBUDDY."""
    def __init__(self):
        """Initialize the program's settings."""
        # pygame window dimensions
        self.window_width = 800
        self.window_height = 600

        # window title
        self.window_title = "BonziBUDDY"

        # window color
        self.background_image = "images/bliss.jpg"

        # Color used for color keying Bonzi
        self.color_screen = "#04fcfc"

        # Input box dimensions
        self.input_box_width = 715
        self.input_box_height = 70

        # Voice settings
        self.rate = 225  # words per minute
        self.volume = 1.0  # range from 0.0 to 1.0


