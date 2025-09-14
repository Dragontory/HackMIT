# Bad scene with dangerous imports - should be rejected
from manim import *
import os  # UNSAFE - should be caught by safety checks
import sys  # UNSAFE - should be caught by safety checks
import subprocess  # UNSAFE - should be caught by safety checks


class Scene_Bad_Import(Scene):
    def construct(self):
        # Attempting unsafe operations
        title = Text("Bad Import Test", font=BODY_FONT).scale(0.9)
        self.play(Write(title))

        # Try to access dangerous functions
        current_dir = os.getcwd()  # Should be blocked
        python_path = sys.path  # Should be blocked

        self.wait(1.0)
