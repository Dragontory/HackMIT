from manim import *

class Scene_WithErrors(Scene):
    def construct(self):
        # Title with fixed syntax
        title = Text("Attention Mechanisms", font_size=36)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)
        
        # LaTeX with fixed brace
        eq = MathTex(r"e_t = H W_a \cdot s_{{t-1}} \in \mathbb{{R}}^{{B 	imes n}}", font_size=32)
        eq.next_to(title, DOWN, buff=0.5)
        self.play(Write(eq), run_time=1.2)
        self.wait(0.8)
        
        # Explanation
        explanation = Text("This equation computes attention energy", font_size=24)
        explanation.next_to(eq, DOWN, buff=0.3)
        self.play(Write(explanation), run_time=1.0)
        self.wait(0.8)
        
        # Fixed animation
        eq2 = MathTex(r"lpha_{{i,j}} = 	ext{{softmax}}(eta_{{i,j}})", font_size=28)
        eq2.next_to(explanation, DOWN, buff=0.3)
        self.play(Write(eq2), run_time=1.0)
        self.wait(0.8)
