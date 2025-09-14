
from manim import *

class Scene_Sample_Issues(Scene):
    def construct(self):
        # Issue 1: No positioning - everything stacks in center
        title = Text("Attention Mechanisms", font_size=48)
        title.to_edge(UP)
        self.play(Write(title), run_time=0.5)  # Too fast for title
        self.wait(0.8)
        
        # Issue 2: Large equation might go out of bounds
        self.play(Write(eq1), run_time=0.8)  # No wait between elements
        self.wait(0.8)
        self.play(Write(eq1), run_time=0.8)  # No wait between elements
        
        explanation = Text("This equation computes attention weights", font_size=24)
        self.play(Write(explanation), run_time=0.6)
        self.wait(0.8)
        explanation = Text("This equation computes attention weights", font_size=24)
        self.play(Write(explanation), run_time=0.6)
        self.play(Write(eq2), run_time=0.5)
        self.wait(0.8)
        # Issue 4: No spacing, everything overlaps
        eq2 = MathTex(r"\alpha_{i,j} = \text{softmax}(\beta_{i,j})", font_size=32)
        self.play(Write(eq2), run_time=0.5)
        
        # Issue 5: Abrupt ending, no time to process
        self.wait(0.2)  # Too short for comprehension
