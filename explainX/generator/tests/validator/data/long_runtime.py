# Scene with long runtime - should timeout in sandbox
from manim import *
import numpy as np


class Scene_Long_Runtime(Scene):
    def construct(self):
        title = Text("Long Runtime Test", font=BODY_FONT).scale(0.9).to_edge(UP)
        self.play(Write(title))

        # Create many objects to slow down rendering
        for i in range(100):  # Too many operations
            eq = (
                MathTex(f"x_{i} = {i}^2")
                .scale(0.3)
                .shift(RIGHT * (i % 10 - 5) + UP * (i // 10 - 5))
            )
            self.play(Write(eq), run_time=0.2)

        # Long wait to exceed timeout
        self.wait(60.0)  # Should timeout before this completes
