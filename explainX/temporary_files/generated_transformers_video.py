
from manim import *

class Scene_WithErrors(Scene):
    def construct(self):
        # Title with missing closing parenthesis - syntax error)
        title = Text("Attention Mechanisms", font_size=36
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)
        
        # LaTeX error - missing closing brace
        eq = MathTex(r"e_t = (H W_a \cdot s_{t-1} \in \mathbb{R}^{B\times n}", font_size=32)
        eq.next_to(title, DOWN, buff=0.5)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
        
        # Runtime error - undefined variable
        explanation = Text("This equation computes attention energy", font_size=24)
        explanation.next_to(eq, DOWN, buff=0.3)
        self.play(Write(explanation), run_time=1.0)
        self.wait(0.8)
        
        # Using undefined variable
        attention_weights.shift(DOWN)  # This will cause a runtime error
        
        # Manim-specific error - invalid animation
        eq2 = MathTex(r"\alpha_{i,j} = \text{softmax}(\beta_{i,j})", font_size=28)
        eq2.next_to(explanation, DOWN, buff=0.3)
        self.play(eq2)  # Missing animation type
        self.wait(0.8)
