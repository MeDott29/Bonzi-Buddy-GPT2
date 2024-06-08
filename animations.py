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
            "idle": sorted(glob.glob("idle/*.bmp")),
            "arrive": sorted(glob.glob("arrive/*.bmp")),
            "goodbye": sorted(glob.glob("goodbye/*.bmp")),
            "backflip": sorted(glob.glob("backflip/*.bmp")),
            "glasses": sorted(glob.glob("glasses/*.bmp")),
            "wave": sorted(glob.glob("wave/*.bmp")),
            "nothing": ["idle/0999.bmp"],
            "talking": sorted(glob.glob("talking/*"))
        }

    def get_animation(self, command):
        """Takes a command and returns the list of frames for corresponding animation."""
        return self.animations.get(command)  # Returns list of frames for command
