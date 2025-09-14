"""
Minimal Manim scene for T6 renderer tests.
Creates a simple, deterministic scene for testing render pipeline.
"""

from manim import *


class TestScene_Simple(Scene):
    """Simple test scene that renders quickly and deterministically."""

    def construct(self):
        # Create simple title text
        title = Text("Test Scene", font_size=48)
        self.play(Write(title), run_time=0.5)
        self.wait(0.5)

        # Add a simple mathematical expression
        formula = MathTex(r"E = mc^2")
        formula.next_to(title, DOWN, buff=1)
        self.play(Write(formula), run_time=0.5)
        self.wait(0.5)

        # Total duration: ~1.5 seconds


class TestScene_Quick(Scene):
    """Even quicker test scene for fast tests."""

    def construct(self):
        text = Text("Quick", font_size=36)
        self.add(text)
        self.wait(0.1)


class TestScene_WithGraph(Scene):
    """Test scene with a simple graph for testing 2D operations."""

    def construct(self):
        # Create axes
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 2, 1],
            x_length=6,
            y_length=4,
        )

        # Create a simple function
        graph = axes.plot(lambda x: x**2 - 1, color=BLUE)

        # Animate
        self.play(Create(axes), run_time=0.3)
        self.play(Create(graph), run_time=0.3)
        self.wait(0.2)


class TestScene_Long(Scene):
    """Longer test scene for timeout testing."""

    def construct(self):
        # Create multiple objects with longer animations
        for i in range(10):
            circle = Circle(radius=0.5 + i * 0.1, color=BLUE)
            circle.shift(RIGHT * i * 0.5)
            self.play(Create(circle), run_time=0.5)

        self.wait(2.0)
        # Total duration: ~7 seconds
