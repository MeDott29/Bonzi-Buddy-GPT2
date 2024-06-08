import glob


class Animation:
    """A class for Bonzi's animations."""
    def __init__(self, bonzi):
        """Initialize the things needed for animations."""
        self.bonzi = bonzi
        self.settings = bonzi.settings

        # Dictionary of lists, each one contains frames for each of Bonzi's animations
        # glob returns a list of all .bmp files in the specified directory, sorted puts them in numeric order
        self.animations = {
            "idle": sorted(glob.glob("animations/idle/*.bmp")),
            "arrive": sorted(glob.glob("animations/arrive/*.bmp")),
            "goodbye": sorted(glob.glob("animations/goodbye/*.bmp")),
            "backflip": sorted(glob.glob("animations/backflip/*.bmp")),
            "glasses": sorted(glob.glob("animations/glasses/*.bmp")),
            "laughing": sorted(glob.glob("animations/laughing/*.bmp")),
            "sleeping": sorted(glob.glob("animations/sleeping/*.bmp")),
            "thinking": sorted(glob.glob("animations/thinking/*.bmp")),
            "wave": sorted(glob.glob("animations/wave/*.bmp")),
            "nothing": ["animations/idle//0999.bmp"],
            "talking": sorted(glob.glob("animations/talking/*"))
        }

    def get_animation(self, command):
        """Takes a command and returns the list of frames for corresponding animation."""
        return self.animations.get(command)  # Returns list of frames for command
