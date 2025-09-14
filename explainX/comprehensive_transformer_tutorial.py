# Comprehensive Manim CE tutorial for "Attention Is All You Need" (Transformer)
# Extensive educational walkthrough with detailed animations and mathematical derivations
# Requires: Manim Community Edition 0.18+, LaTeX installed for MathTex, FFmpeg

from manim import *
import numpy as np

# ----------------------------
# Enhanced styling and helpers
# ----------------------------

ACCENT = BLUE_C
SECONDARY = GREY_B
HIGHLIGHT = YELLOW
ERROR_COLOR = RED
SUCCESS_COLOR = GREEN
BG = WHITE
TEXT = BLACK


class Style:
    title_scale = 1.0
    subtitle_scale = 0.8
    text_scale = 0.75
    eq_scale = 0.9
    small_eq_scale = 0.7
    default_wait = 0.3
    animation_time = 1.0


def title_block(scene: Scene, title: str, subtitle: str | None = None):
    t = Text(title, color=TEXT, font="Arial").scale(Style.title_scale).to_edge(UP)
    scene.play(Write(t), run_time=Style.animation_time)
    if subtitle:
        s = (
            Text(subtitle, color=SECONDARY, font="Arial")
            .scale(Style.subtitle_scale)
            .next_to(t, DOWN)
        )
        scene.play(FadeIn(s, shift=UP * 0.2), run_time=Style.animation_time)
        scene.wait(Style.default_wait)
        return t, s
    scene.wait(Style.default_wait)
    return t, None


def bullet_list(lines: list[str], width=10.0, color=TEXT):
    items = VGroup(
        *[
            Tex(r"$\bullet$\\ \ \ " + line, substrings_to_isolate=["$\\bullet$"]).scale(
                Style.text_scale
            )
            for line in lines
        ]
    )
    items.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
    for it in items:
        it.set_color(color)
    return items.set_max_width(width)


def labeled_block(label: str, color=ACCENT, width=2.8, height=1.2, fill_opacity=0.3):
    rect = RoundedRectangle(
        corner_radius=0.15,
        width=width,
        height=height,
        color=color,
        fill_opacity=fill_opacity,
    )
    txt = Text(label, font="Arial").scale(0.6).move_to(rect.get_center())
    g = VGroup(rect, txt)
    return g


def connect(
    scene: Scene, a: Mobject, b: Mobject, text: str | None = None, color=ACCENT, **kw
):
    arr = Arrow(a.get_right(), b.get_left(), buff=0.1, color=color, **kw)
    scene.play(Create(arr), run_time=0.5)
    if text:
        lab = Text(text, font="Arial").scale(0.5).next_to(arr, UP * 0.7)
        scene.play(FadeIn(lab, shift=UP * 0.2), run_time=0.5)
        return arr, lab
    return arr, None


def highlight_equation_part(
    scene: Scene, equation: MathTex, part_indices: list, color=HIGHLIGHT
):
    """Highlight specific parts of a mathematical equation"""
    highlights = []
    for idx in part_indices:
        highlight = SurroundingRectangle(equation[idx], color=color, buff=0.1)
        highlights.append(highlight)
        scene.play(Create(highlight), run_time=0.3)
    return highlights


# ----------------------------
# 1) Enhanced Introduction with Historical Context
# ----------------------------
class Scene_Intro(Scene):
    def construct(self):
        self.camera.background_color = BG
        title, sub = title_block(
            self,
            "The Transformer Revolution",
            "Attention Is All You Need (Vaswani et al., 2017)",
        )
        self.wait(1)

        # Part 1: The Problem with Sequential Models
        problem_title = (
            Text("The Sequential Modeling Problem", font="Arial")
            .scale(0.8)
            .set_color(ERROR_COLOR)
        )
        problem_title.to_edge(UP, buff=1.5)

        self.play(Transform(title, problem_title))
        self.clear()

        # RNN sequential processing visualization
        rnn_title = (
            Text("Traditional RNN Processing", font="Arial")
            .scale(0.7)
            .to_edge(UP, buff=1.0)
        )
        self.play(Write(rnn_title))

        # Sequential tokens
        tokens = ["The", "cat", "sat", "on", "mat"]
        token_objects = VGroup(
            *[
                VGroup(
                    RoundedRectangle(
                        width=1.2, height=0.8, color=SECONDARY, fill_opacity=0.3
                    ),
                    Text(token, font="Arial").scale(0.5),
                )
                for token in tokens
            ]
        )

        for i, token_obj in enumerate(token_objects):
            token_obj[1].move_to(token_obj[0])

        token_objects.arrange(RIGHT, buff=1.5).center()

        # RNN cells
        rnn_cells = VGroup(
            *[
                VGroup(
                    Circle(radius=0.4, color=BLUE, fill_opacity=0.5),
                    Text(f"h{i}", font="Arial").scale(0.4),
                )
                for i in range(len(tokens))
            ]
        )

        for i, cell in enumerate(rnn_cells):
            cell[1].move_to(cell[0])
            cell.next_to(token_objects[i], UP, buff=0.8)

        # Show sequential bottleneck
        self.play(
            LaggedStart(*[FadeIn(token) for token in token_objects], lag_ratio=0.3)
        )

        for i, (token, cell) in enumerate(zip(token_objects, rnn_cells)):
            self.play(FadeIn(cell))
            arrow_up = Arrow(token.get_top(), cell.get_bottom(), buff=0.1)
            self.play(Create(arrow_up))

            if i > 0:
                # Sequential dependency arrow
                seq_arrow = Arrow(
                    rnn_cells[i - 1].get_right(),
                    cell.get_left(),
                    buff=0.1,
                    color=ERROR_COLOR,
                    stroke_width=3,
                )
                self.play(Create(seq_arrow))
                self.wait(0.3)

        # Highlight the problem
        bottleneck_text = (
            Text("Sequential Bottleneck!", font="Arial")
            .scale(0.8)
            .set_color(ERROR_COLOR)
        )
        bottleneck_text.next_to(rnn_cells, UP, buff=0.5)
        self.play(Write(bottleneck_text))

        problems = bullet_list(
            [
                "Cannot parallelize training",
                "Vanishing gradients over long sequences",
                "Limited context window",
                "Slow inference due to sequential dependencies",
            ],
            color=ERROR_COLOR,
            width=8.0,
        )
        problems.to_edge(DOWN, buff=1.0)
        self.play(FadeIn(problems, lag_ratio=0.2))
        self.wait(2)
        self.clear()

        # Part 2: Timeline of sequence modeling evolution
        timeline_title = (
            Text("Evolution of Sequence Modeling", font="Arial")
            .scale(0.9)
            .set_color(ACCENT)
        )
        timeline_title.to_edge(UP, buff=1.0)
        self.play(Write(timeline_title))

        timeline = VGroup()
        milestones = [
            ("RNNs", "1986", "First recurrent networks"),
            ("LSTMs", "1997", "Long-term memory"),
            ("GRU", "2014", "Simpler gating"),
            ("Seq2Seq", "2014", "Encoder-decoder"),
            ("Attention", "2015", "Alignment mechanism"),
            ("Transformer", "2017", "Pure attention"),
        ]

        for i, (name, year, desc) in enumerate(milestones):
            milestone = VGroup(
                Circle(radius=0.3, color=ACCENT, fill_opacity=0.7),
                Text(name, font="Arial").scale(0.45),
                Text(year, font="Arial").scale(0.35).set_color(SECONDARY),
                Text(desc, font="Arial").scale(0.3).set_color(TEXT),
            )
            milestone[1].move_to(milestone[0])
            milestone[2].next_to(milestone[0], DOWN, buff=0.2)
            milestone[3].next_to(milestone[2], DOWN, buff=0.2)
            timeline.add(milestone)

        timeline.arrange(RIGHT, buff=1.2).center()

        # Animate timeline with detailed explanations
        for i, milestone in enumerate(timeline):
            self.play(FadeIn(milestone), run_time=1.0)
            if i < len(timeline) - 1:
                arrow = Arrow(
                    milestone[0].get_right(), timeline[i + 1][0].get_left(), buff=0.1
                )
                self.play(Create(arrow), run_time=0.5)
            self.wait(0.5)

        # Highlight Transformer breakthrough
        transformer_highlight = SurroundingRectangle(
            timeline[-1], color=SUCCESS_COLOR, buff=0.3
        )
        self.play(Create(transformer_highlight))

        breakthrough_text = (
            Text("The Breakthrough!", font="Arial").scale(0.8).set_color(SUCCESS_COLOR)
        )
        breakthrough_text.next_to(timeline[-1], UP, buff=0.8)
        self.play(Write(breakthrough_text))
        self.wait(2)
        self.clear()

        # Part 3: Key innovations detailed
        innovations_title = (
            Text("Revolutionary Innovations", font="Arial").scale(0.9).set_color(ACCENT)
        )
        innovations_title.to_edge(UP, buff=1.0)
        self.play(Write(innovations_title))

        # Create detailed innovation cards
        innovation_cards = VGroup()

        innovations_data = [
            ("Self-Attention", "Global context in O(1) steps", BLUE),
            ("Multi-Head", "Parallel attention patterns", GREEN),
            ("Positional Encoding", "Order without recurrence", PURPLE),
            ("Layer Normalization", "Training stability", ORANGE),
            ("Parallelization", "Efficient GPU utilization", RED),
        ]

        for title, desc, color in innovations_data:
            card = VGroup(
                RoundedRectangle(width=2.5, height=1.8, color=color, fill_opacity=0.2),
                Text(title, font="Arial").scale(0.6).set_color(color),
                Text(desc, font="Arial").scale(0.4).set_color(TEXT),
            )
            card[1].next_to(card[0].get_top(), DOWN, buff=0.3)
            card[2].next_to(card[1], DOWN, buff=0.3)
            innovation_cards.add(card)

        innovation_cards.arrange_in_grid(rows=2, cols=3, buff=0.8).center()

        for card in innovation_cards:
            self.play(FadeIn(card, shift=UP * 0.3), run_time=0.8)

        self.wait(1)

        # Part 4: Performance comparison with detailed metrics
        self.clear()
        comparison_title = (
            Text("Performance Revolution", font="Arial")
            .scale(0.9)
            .set_color(SUCCESS_COLOR)
        )
        comparison_title.to_edge(UP, buff=1.0)
        self.play(Write(comparison_title))

        # Detailed comparison table
        comparison_data = [
            ["Metric", "RNN/LSTM", "Transformer", "Improvement"],
            ["Training Time", "Days", "Hours", "10x faster"],
            ["BLEU Score (EN-DE)", "25.2", "28.4", "+3.2 points"],
            ["Parallelization", "None", "Full", "Complete"],
            ["Memory Efficiency", "Poor", "Good", "Better"],
            ["Long Dependencies", "Limited", "Global", "Unlimited"],
        ]

        table = VGroup()
        for i, row in enumerate(comparison_data):
            row_group = VGroup()
            for j, cell in enumerate(row):
                if i == 0:  # Header
                    cell_obj = Text(cell, font="Arial").scale(0.5).set_color(ACCENT)
                elif j == 3 and i > 0:  # Improvement column
                    cell_obj = (
                        Text(cell, font="Arial").scale(0.5).set_color(SUCCESS_COLOR)
                    )
                else:
                    cell_obj = Text(cell, font="Arial").scale(0.5).set_color(TEXT)

                cell_bg = Rectangle(
                    width=2.5,
                    height=0.6,
                    color=WHITE,
                    fill_opacity=0.1,
                    stroke_color=SECONDARY,
                )
                cell_group = VGroup(cell_bg, cell_obj)
                row_group.add(cell_group)

            row_group.arrange(RIGHT, buff=0.1)
            table.add(row_group)

        table.arrange(DOWN, buff=0.1).center()

        for i, row in enumerate(table):
            self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.7)
            if i == 0:
                self.wait(0.5)  # Pause after header

        self.wait(2)

        # Impact numbers with animation
        impact_title = (
            Text("Global Impact by Numbers", font="Arial")
            .scale(0.8)
            .set_color(HIGHLIGHT)
        )
        impact_title.to_edge(DOWN, buff=2.5)
        self.play(Write(impact_title))

        impact_stats = VGroup()
        stats_data = [
            ("50,000+", "Citations"),
            ("1000+", "Implementations"),
            ("90%", "Cost Reduction"),
            ("10x", "Speed Increase"),
        ]

        for number, label in stats_data:
            stat = VGroup(
                Text(number, font="Arial").scale(1.2).set_color(SUCCESS_COLOR),
                Text(label, font="Arial").scale(0.6).set_color(TEXT),
            )
            stat.arrange(DOWN, buff=0.2)
            impact_stats.add(stat)

        impact_stats.arrange(RIGHT, buff=1.5).next_to(impact_title, DOWN, buff=0.5)

        for stat in impact_stats:
            self.play(FadeIn(stat, shift=UP * 0.5), run_time=0.8)

        self.wait(3)


# ----------------------------
# 2) Mathematical Foundation of Attention
# ----------------------------
class Scene_AttentionMath(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(self, "Mathematical Foundation", "Scaled Dot-Product Attention")
        self.wait(1)

        # Part 1: Intuitive introduction to attention
        intuition_title = (
            Text("What is Attention?", font="Arial").scale(0.9).set_color(ACCENT)
        )
        intuition_title.to_edge(UP, buff=1.0)
        self.play(Write(intuition_title))

        # Human attention analogy
        analogy_text = Text("Like human attention when reading:", font="Arial").scale(
            0.7
        )
        analogy_text.next_to(intuition_title, DOWN, buff=0.8)
        self.play(Write(analogy_text))

        sentence = "The cat sat on the warm, comfortable mat."
        words = sentence.split()
        word_objects = VGroup(*[Text(word, font="Arial").scale(0.6) for word in words])
        word_objects.arrange(RIGHT, buff=0.5).next_to(analogy_text, DOWN, buff=0.8)

        self.play(LaggedStart(*[FadeIn(word) for word in word_objects], lag_ratio=0.1))

        # Focus on "cat" - what does it relate to?
        focus_word = word_objects[1]  # "cat"
        focus_highlight = SurroundingRectangle(focus_word, color=ACCENT, buff=0.1)
        self.play(Create(focus_highlight))

        # Show attention connections
        attention_weights = [0.1, 0.2, 0.15, 0.1, 0.05, 0.15, 0.15, 0.1]
        connections = VGroup()

        for i, (word, weight) in enumerate(zip(word_objects, attention_weights)):
            if i == 1:  # Skip self
                continue
            connection = Arrow(
                focus_word.get_bottom(),
                word.get_bottom(),
                buff=0.1,
                color=ACCENT,
                stroke_width=weight * 20,
                stroke_opacity=0.3 + weight * 2,
            )
            connections.add(connection)

        self.play(LaggedStart(*[Create(conn) for conn in connections], lag_ratio=0.1))

        explanation = Text(
            "'cat' attends to related words with different strengths", font="Arial"
        ).scale(0.6)
        explanation.to_edge(DOWN, buff=1.0)
        self.play(Write(explanation))
        self.wait(2)
        self.clear()

        # Part 2: Mathematical formulation - step by step derivation
        math_title = (
            Text("Mathematical Formulation", font="Arial").scale(0.9).set_color(ACCENT)
        )
        math_title.to_edge(UP, buff=1.0)
        self.play(Write(math_title))

        # Start with the problem: how to compute attention?
        problem_text = Text(
            "Problem: How to compute attention weights?", font="Arial"
        ).scale(0.7)
        problem_text.next_to(math_title, DOWN, buff=0.8)
        self.play(Write(problem_text))

        # Step 1: Similarity function
        step1_title = (
            Text("Step 1: Measure Similarity", font="Arial").scale(0.7).set_color(BLUE)
        )
        step1_eq = MathTex(r"e_{ij} = \text{similarity}(q_i, k_j)").scale(0.8)
        step1_group = VGroup(step1_title, step1_eq).arrange(DOWN, buff=0.3)
        step1_group.next_to(problem_text, DOWN, buff=0.8)

        self.play(Write(step1_title))
        self.play(Write(step1_eq))

        # Why dot product?
        why_dot = bullet_list(
            [
                "Dot product measures similarity/alignment",
                "Computationally efficient (matrix multiplication)",
                "Differentiable for gradient-based learning",
            ],
            width=8.0,
        )
        why_dot.next_to(step1_group, DOWN, buff=0.5)
        self.play(FadeIn(why_dot, lag_ratio=0.2))
        self.wait(2)
        self.clear()

        # Step 2: Introduce QKV matrices
        math_title = (
            Text("Query-Key-Value Paradigm", font="Arial").scale(0.9).set_color(ACCENT)
        )
        math_title.to_edge(UP, buff=1.0)
        self.play(Write(math_title))

        # Detailed QKV explanation
        qkv_explanation = VGroup()

        # Query explanation
        q_title = (
            Text("Queries (Q): 'What am I looking for?'", font="Arial")
            .scale(0.7)
            .set_color(BLUE)
        )
        q_math = MathTex(r"Q = XW^Q, \quad Q \in \mathbb{R}^{n \times d_k}").scale(0.7)
        q_desc = (
            Text("Each row is a query vector for one position", font="Arial")
            .scale(0.5)
            .set_color(SECONDARY)
        )
        q_group = VGroup(q_title, q_math, q_desc).arrange(
            DOWN, buff=0.2, aligned_edge=LEFT
        )

        # Key explanation
        k_title = (
            Text("Keys (K): 'What do I contain?'", font="Arial")
            .scale(0.7)
            .set_color(GREEN)
        )
        k_math = MathTex(r"K = XW^K, \quad K \in \mathbb{R}^{m \times d_k}").scale(0.7)
        k_desc = (
            Text("Each row is a key vector describing content", font="Arial")
            .scale(0.5)
            .set_color(SECONDARY)
        )
        k_group = VGroup(k_title, k_math, k_desc).arrange(
            DOWN, buff=0.2, aligned_edge=LEFT
        )

        # Value explanation
        v_title = (
            Text("Values (V): 'What information do I carry?'", font="Arial")
            .scale(0.7)
            .set_color(PURPLE)
        )
        v_math = MathTex(r"V = XW^V, \quad V \in \mathbb{R}^{m \times d_v}").scale(0.7)
        v_desc = (
            Text("Each row contains the actual information", font="Arial")
            .scale(0.5)
            .set_color(SECONDARY)
        )
        v_group = VGroup(v_title, v_math, v_desc).arrange(
            DOWN, buff=0.2, aligned_edge=LEFT
        )

        qkv_explanation.add(q_group, k_group, v_group)
        qkv_explanation.arrange(DOWN, buff=0.8, aligned_edge=LEFT)
        qkv_explanation.center()

        for group in qkv_explanation:
            self.play(FadeIn(group, shift=RIGHT * 0.3), run_time=1.2)
            self.wait(0.5)

        self.wait(2)
        self.clear()

        # Part 3: Step-by-step attention computation with visual matrix operations
        computation_title = (
            Text("Attention Computation Steps", font="Arial")
            .scale(0.9)
            .set_color(ACCENT)
        )
        computation_title.to_edge(UP, buff=1.0)
        self.play(Write(computation_title))

        # Main attention equation - build it step by step
        main_eq = MathTex(
            r"\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V"
        ).scale(0.9)
        main_eq.next_to(computation_title, DOWN, buff=0.8)
        self.play(Write(main_eq), run_time=2.0)

        # Visual matrix dimensions
        matrices_demo = VGroup()

        # Show Q matrix
        q_matrix = Matrix(
            [
                ["q_{11}", "q_{12}", "\\cdots", "q_{1d}"],
                ["q_{21}", "q_{22}", "\\cdots", "q_{2d}"],
                ["\\vdots", "\\vdots", "\\ddots", "\\vdots"],
                ["q_{n1}", "q_{n2}", "\\cdots", "q_{nd}"],
            ],
            bracket_h_buff=0.1,
        )
        q_matrix.scale(0.6)
        q_label = Text("Q (n×d)", font="Arial").scale(0.5).set_color(BLUE)
        q_group = VGroup(q_label, q_matrix).arrange(DOWN, buff=0.3)

        # Show K^T matrix
        kt_matrix = Matrix(
            [
                ["k_{11}", "k_{21}", "\\cdots", "k_{m1}"],
                ["k_{12}", "k_{22}", "\\cdots", "k_{m2}"],
                ["\\vdots", "\\vdots", "\\ddots", "\\vdots"],
                ["k_{1d}", "k_{2d}", "\\cdots", "k_{md}"],
            ],
            bracket_h_buff=0.1,
        )
        kt_matrix.scale(0.6)
        kt_label = Text("K^T (d×m)", font="Arial").scale(0.5).set_color(GREEN)
        kt_group = VGroup(kt_label, kt_matrix).arrange(DOWN, buff=0.3)

        # Show result matrix
        result_matrix = Matrix(
            [
                ["s_{11}", "s_{12}", "\\cdots", "s_{1m}"],
                ["s_{21}", "s_{22}", "\\cdots", "s_{2m}"],
                ["\\vdots", "\\vdots", "\\ddots", "\\vdots"],
                ["s_{n1}", "s_{n2}", "\\cdots", "s_{nm}"],
            ],
            bracket_h_buff=0.1,
        )
        result_matrix.scale(0.6)
        result_label = Text("QK^T (n×m)", font="Arial").scale(0.5).set_color(ACCENT)
        result_group = VGroup(result_label, result_matrix).arrange(DOWN, buff=0.3)

        matrices_demo.add(q_group, kt_group, result_group)
        matrices_demo.arrange(RIGHT, buff=1.0)
        matrices_demo.next_to(main_eq, DOWN, buff=1.0)

        # Animate matrix multiplication
        self.play(FadeIn(q_group))
        self.wait(0.5)
        self.play(FadeIn(kt_group))

        # Show multiplication
        mult_symbol = MathTex(r"\times").scale(1.2)
        mult_symbol.move_to(VGroup(q_group, kt_group))
        self.play(Write(mult_symbol))

        # Show result
        equals_symbol = MathTex(r"=").scale(1.2)
        equals_symbol.move_to(VGroup(kt_group, result_group))
        self.play(Write(equals_symbol))
        self.play(FadeIn(result_group))

        self.wait(2)
        self.clear()

        # Part 4: Detailed step-by-step computation
        steps_title = (
            Text("Detailed Computation Steps", font="Arial")
            .scale(0.9)
            .set_color(ACCENT)
        )
        steps_title.to_edge(UP, buff=1.0)
        self.play(Write(steps_title))

        # Step 1: Compatibility scores with explanation
        step1_title = (
            Text("Step 1: Compute Compatibility Scores", font="Arial")
            .scale(0.7)
            .set_color(BLUE)
        )
        step1_eq = MathTex(r"S = QK^T \in \mathbb{R}^{n \times m}").scale(0.8)
        step1_detail = MathTex(r"s_{ij} = \sum_{k=1}^{d} q_{ik} \cdot k_{jk}").scale(
            0.7
        )
        step1_meaning = (
            Text("Each s_ij measures how much query i attends to key j", font="Arial")
            .scale(0.5)
            .set_color(SECONDARY)
        )

        step1_group = VGroup(step1_title, step1_eq, step1_detail, step1_meaning)
        step1_group.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        step1_group.next_to(steps_title, DOWN, buff=0.8)

        for item in step1_group:
            self.play(Write(item), run_time=1.0)
            self.wait(0.3)

        self.wait(1)

        # Step 2: Scaling with mathematical justification
        step2_title = (
            Text("Step 2: Scale for Gradient Stability", font="Arial")
            .scale(0.7)
            .set_color(GREEN)
        )
        step2_eq = MathTex(r"S' = \frac{S}{\sqrt{d_k}}").scale(0.8)
        step2_detail = MathTex(r"s'_{ij} = \frac{s_{ij}}{\sqrt{d_k}}").scale(0.7)

        step2_group = VGroup(step2_title, step2_eq, step2_detail)
        step2_group.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        step2_group.next_to(step1_group, DOWN, buff=0.8)

        for item in step2_group:
            self.play(Write(item), run_time=1.0)
            self.wait(0.3)

        # Why scaling - mathematical proof
        why_scaling = VGroup()
        why_title = (
            Text("Why √d_k scaling?", font="Arial").scale(0.6).set_color(HIGHLIGHT)
        )

        proof_steps = [
            r"\text{If } q_i, k_j \sim \mathcal{N}(0, 1) \text{ independently}",
            r"\text{then } q_i \cdot k_j = \sum_{l=1}^{d_k} q_{il} k_{jl}",
            r"\mathbb{E}[q_i \cdot k_j] = 0, \quad \text{Var}[q_i \cdot k_j] = d_k",
            r"\text{Large } d_k \Rightarrow \text{Large variance} \Rightarrow \text{Softmax saturation}",
            r"\text{Scaling by } \sqrt{d_k} \text{ normalizes variance to 1}",
        ]

        proof_eqs = VGroup(*[MathTex(step).scale(0.5) for step in proof_steps])
        proof_eqs.arrange(DOWN, buff=0.2, aligned_edge=LEFT)

        why_scaling.add(why_title, proof_eqs)
        why_scaling.arrange(DOWN, buff=0.3)
        why_scaling.next_to(step2_group, DOWN, buff=0.5)

        self.play(Write(why_title))
        for eq in proof_eqs:
            self.play(Write(eq), run_time=0.8)

        self.wait(2)
        self.clear()

        # Part 5: Softmax and final computation
        softmax_title = (
            Text("Step 3: Softmax & Final Computation", font="Arial")
            .scale(0.9)
            .set_color(ACCENT)
        )
        softmax_title.to_edge(UP, buff=1.0)
        self.play(Write(softmax_title))

        # Softmax explanation
        softmax_eq = MathTex(
            r"A = \text{softmax}(S') = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)"
        ).scale(0.8)
        softmax_eq.next_to(softmax_title, DOWN, buff=0.8)
        self.play(Write(softmax_eq))

        # Softmax formula per row
        softmax_detail = MathTex(
            r"A_{ij} = \frac{\exp(s'_{ij})}{\sum_{k=1}^{m} \exp(s'_{ik})}"
        ).scale(0.8)
        softmax_detail.next_to(softmax_eq, DOWN, buff=0.5)
        self.play(Write(softmax_detail))

        # Properties of softmax
        softmax_properties = bullet_list(
            [
                r"Row-wise normalization: $\sum_j A_{ij} = 1$ for all $i$",
                r"Non-negative: $A_{ij} \geq 0$ for all $i,j$",
                r"Probability distribution over keys for each query",
                r"Differentiable: enables gradient-based learning",
            ],
            width=10.0,
        )
        softmax_properties.next_to(softmax_detail, DOWN, buff=0.8)

        for prop in softmax_properties:
            self.play(Write(prop), run_time=1.0)

        self.wait(2)

        # Final step: weighted combination
        final_title = (
            Text("Step 4: Weighted Value Combination", font="Arial")
            .scale(0.7)
            .set_color(PURPLE)
        )
        final_eq = MathTex(r"\text{Output} = AV").scale(0.8)
        final_detail = MathTex(
            r"\text{output}_i = \sum_{j=1}^{m} A_{ij} \cdot v_j"
        ).scale(0.7)
        final_meaning = (
            Text("Each output is a weighted average of all values", font="Arial")
            .scale(0.6)
            .set_color(SECONDARY)
        )

        final_group = VGroup(final_title, final_eq, final_detail, final_meaning)
        final_group.arrange(DOWN, buff=0.3)
        final_group.to_edge(DOWN, buff=1.0)

        for item in final_group:
            self.play(Write(item), run_time=1.0)

        # Summary equation
        complete_eq = (
            MathTex(
                r"\boxed{\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V}"
            )
            .scale(1.0)
            .set_color(SUCCESS_COLOR)
        )
        complete_eq.move_to(ORIGIN)

        self.play(Write(complete_eq), run_time=2.0)
        self.wait(3)

        # Part 6: Numerical example with concrete values
        self.clear()
        numerical_title = (
            Text("Numerical Example", font="Arial").scale(0.9).set_color(ACCENT)
        )
        numerical_title.to_edge(UP, buff=1.0)
        self.play(Write(numerical_title))

        # Simple 2x2 example
        example_text = Text(
            "Simple 2×2 Example: Two words attending to each other", font="Arial"
        ).scale(0.7)
        example_text.next_to(numerical_title, DOWN, buff=0.8)
        self.play(Write(example_text))

        # Input matrices
        q_vals = Matrix([["1.0", "0.5"], ["0.2", "1.5"]], bracket_h_buff=0.1).scale(0.8)
        k_vals = Matrix([["0.8", "0.3"], ["1.2", "0.7"]], bracket_h_buff=0.1).scale(0.8)
        v_vals = Matrix([["2.0", "1.0"], ["0.5", "3.0"]], bracket_h_buff=0.1).scale(0.8)

        q_label = Text("Q =", font="Arial").scale(0.7)
        k_label = Text("K =", font="Arial").scale(0.7)
        v_label = Text("V =", font="Arial").scale(0.7)

        matrices_row = VGroup(
            VGroup(q_label, q_vals).arrange(RIGHT, buff=0.3),
            VGroup(k_label, k_vals).arrange(RIGHT, buff=0.3),
            VGroup(v_label, v_vals).arrange(RIGHT, buff=0.3),
        ).arrange(RIGHT, buff=1.0)
        matrices_row.next_to(example_text, DOWN, buff=0.8)

        self.play(
            LaggedStart(*[FadeIn(group) for group in matrices_row], lag_ratio=0.5)
        )

        # Compute QK^T step by step
        computation_steps = VGroup()

        step1_text = (
            Text("Step 1: Compute QK^T", font="Arial").scale(0.7).set_color(BLUE)
        )
        qkt_calc = MathTex(
            r"QK^T = \begin{pmatrix} 1.0 & 0.5 \\ 0.2 & 1.5 \end{pmatrix} \begin{pmatrix} 0.8 & 1.2 \\ 0.3 & 0.7 \end{pmatrix} = \begin{pmatrix} 0.95 & 1.55 \\ 0.61 & 1.29 \end{pmatrix}"
        ).scale(0.6)

        step2_text = (
            Text("Step 2: Scale by √d_k = √2 ≈ 1.41", font="Arial")
            .scale(0.7)
            .set_color(GREEN)
        )
        scaled_calc = MathTex(
            r"S' = \frac{1}{1.41} \begin{pmatrix} 0.95 & 1.55 \\ 0.61 & 1.29 \end{pmatrix} = \begin{pmatrix} 0.67 & 1.10 \\ 0.43 & 0.91 \end{pmatrix}"
        ).scale(0.6)

        step3_text = (
            Text("Step 3: Apply softmax row-wise", font="Arial")
            .scale(0.7)
            .set_color(PURPLE)
        )
        softmax_calc = MathTex(
            r"A = \text{softmax}(S') = \begin{pmatrix} 0.35 & 0.65 \\ 0.38 & 0.62 \end{pmatrix}"
        ).scale(0.6)

        step4_text = (
            Text("Step 4: Multiply by V", font="Arial").scale(0.7).set_color(ORANGE)
        )
        final_calc = MathTex(
            r"\text{Output} = AV = \begin{pmatrix} 0.35 & 0.65 \\ 0.38 & 0.62 \end{pmatrix} \begin{pmatrix} 2.0 & 1.0 \\ 0.5 & 3.0 \end{pmatrix} = \begin{pmatrix} 1.03 & 2.30 \\ 1.07 & 2.24 \end{pmatrix}"
        ).scale(0.6)

        computation_steps.add(
            VGroup(step1_text, qkt_calc).arrange(DOWN, buff=0.3),
            VGroup(step2_text, scaled_calc).arrange(DOWN, buff=0.3),
            VGroup(step3_text, softmax_calc).arrange(DOWN, buff=0.3),
            VGroup(step4_text, final_calc).arrange(DOWN, buff=0.3),
        )
        computation_steps.arrange(DOWN, buff=0.8, aligned_edge=LEFT)
        computation_steps.next_to(matrices_row, DOWN, buff=1.0)

        for step in computation_steps:
            self.play(FadeIn(step, shift=RIGHT * 0.3), run_time=1.5)
            self.wait(1)

        self.wait(3)


# ----------------------------
# 3) Attention Visualization with Concrete Example
# ----------------------------
class Scene_AttentionVisualization(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(
            self, "Attention in Action", "Visual Understanding Through Examples"
        )
        self.wait(1)

        # Part 1: Self-Attention vs Cross-Attention
        attention_types_title = (
            Text("Types of Attention", font="Arial").scale(0.9).set_color(ACCENT)
        )
        attention_types_title.to_edge(UP, buff=1.0)
        self.play(Write(attention_types_title))

        # Self-attention explanation
        self_attn_title = (
            Text("Self-Attention", font="Arial").scale(0.8).set_color(BLUE)
        )
        self_attn_desc = Text(
            "Each position attends to all positions in the same sequence", font="Arial"
        ).scale(0.6)

        # Cross-attention explanation
        cross_attn_title = (
            Text("Cross-Attention", font="Arial").scale(0.8).set_color(GREEN)
        )
        cross_attn_desc = Text(
            "Positions in one sequence attend to positions in another", font="Arial"
        ).scale(0.6)

        # Visual demonstration
        seq1_words = ["The", "cat", "sleeps"]
        seq2_words = ["Le", "chat", "dort"]

        seq1_objects = VGroup(
            *[
                VGroup(
                    RoundedRectangle(
                        width=1.0, height=0.6, color=BLUE, fill_opacity=0.3
                    ),
                    Text(word, font="Arial").scale(0.5),
                )
                for word in seq1_words
            ]
        )

        seq2_objects = VGroup(
            *[
                VGroup(
                    RoundedRectangle(
                        width=1.0, height=0.6, color=GREEN, fill_opacity=0.3
                    ),
                    Text(word, font="Arial").scale(0.5),
                )
                for word in seq2_words
            ]
        )

        for seq in [seq1_objects, seq2_objects]:
            for item in seq:
                item[1].move_to(item[0])

        seq1_objects.arrange(RIGHT, buff=0.8)
        seq2_objects.arrange(RIGHT, buff=0.8)

        sequences = VGroup(seq1_objects, seq2_objects).arrange(DOWN, buff=2.0).center()

        # Labels
        seq1_label = Text("English", font="Arial").scale(0.6).set_color(BLUE)
        seq1_label.next_to(seq1_objects, LEFT, buff=0.5)
        seq2_label = Text("French", font="Arial").scale(0.6).set_color(GREEN)
        seq2_label.next_to(seq2_objects, LEFT, buff=0.5)

        self.play(FadeIn(seq1_label), FadeIn(seq1_objects))
        self.play(FadeIn(seq2_label), FadeIn(seq2_objects))

        # Show self-attention connections
        self_attn_connections = VGroup()
        for i, word1 in enumerate(seq1_objects):
            for j, word2 in enumerate(seq1_objects):
                if i != j:
                    conn = Line(
                        word1.get_center(),
                        word2.get_center(),
                        color=BLUE,
                        stroke_width=2,
                        stroke_opacity=0.5,
                    )
                    self_attn_connections.add(conn)

        self_attn_annotation = (
            Text("Self-attention within English", font="Arial")
            .scale(0.5)
            .set_color(BLUE)
        )
        self_attn_annotation.next_to(seq1_objects, UP, buff=0.5)

        self.play(Write(self_attn_annotation))
        self.play(Create(self_attn_connections))
        self.wait(1)

        # Show cross-attention connections
        cross_attn_connections = VGroup()
        for word1 in seq1_objects:
            for word2 in seq2_objects:
                conn = Line(
                    word1.get_center(),
                    word2.get_center(),
                    color=PURPLE,
                    stroke_width=2,
                    stroke_opacity=0.7,
                )
                cross_attn_connections.add(conn)

        cross_attn_annotation = (
            Text("Cross-attention: English → French", font="Arial")
            .scale(0.5)
            .set_color(PURPLE)
        )
        cross_attn_annotation.move_to(VGroup(seq1_objects, seq2_objects))

        self.play(Write(cross_attn_annotation))
        self.play(Create(cross_attn_connections))
        self.wait(2)
        self.clear()

        # Part 2: Detailed example with real sentence
        detailed_title = (
            Text("Detailed Attention Example", font="Arial")
            .scale(0.9)
            .set_color(ACCENT)
        )
        detailed_title.to_edge(UP, buff=1.0)
        self.play(Write(detailed_title))

        # Longer, more interesting sentence
        sentence = "The quick brown fox jumps over the lazy dog"
        words = sentence.split()
        word_objects = VGroup(
            *[
                VGroup(
                    RoundedRectangle(
                        width=len(word) * 0.15 + 0.4,
                        height=0.8,
                        color=SECONDARY,
                        fill_opacity=0.2,
                    ),
                    Text(word, font="Arial").scale(0.5),
                )
                for word in words
            ]
        )

        for item in word_objects:
            item[1].move_to(item[0])

        word_objects.arrange(RIGHT, buff=0.3).next_to(detailed_title, DOWN, buff=1.0)

        self.play(LaggedStart(*[FadeIn(word) for word in word_objects], lag_ratio=0.1))

        # Interactive attention visualization - focus on different words
        focus_examples = [
            (3, "fox", [0.05, 0.1, 0.2, 0.15, 0.25, 0.1, 0.05, 0.05, 0.05]),  # fox
            (
                4,
                "jumps",
                [0.05, 0.05, 0.05, 0.3, 0.15, 0.25, 0.05, 0.05, 0.05],
            ),  # jumps
            (7, "lazy", [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.15, 0.5]),  # lazy
        ]

        for focus_idx, focus_word_str, weights in focus_examples:
            focus_word = word_objects[focus_idx]

            # Highlight current focus
            focus_highlight = SurroundingRectangle(focus_word, color=ACCENT, buff=0.1)
            focus_label = (
                Text(f"Query: '{focus_word_str}'", font="Arial")
                .scale(0.6)
                .set_color(ACCENT)
            )
            focus_label.next_to(focus_word, UP, buff=0.5)

            self.play(Create(focus_highlight), Write(focus_label))

            # Show attention weights
            attention_arrows = VGroup()
            weight_labels = VGroup()

            for i, (target, weight) in enumerate(zip(word_objects, weights)):
                if i == focus_idx:  # Skip self for clarity
                    continue

                arrow = Arrow(
                    focus_word.get_bottom(),
                    target.get_bottom(),
                    buff=0.1,
                    color=ACCENT,
                    stroke_width=weight * 20,
                    stroke_opacity=0.3 + weight * 1.5,
                )

                if weight > 0.15:  # Only show significant weights
                    weight_text = Text(f"{weight:.2f}", font="Arial").scale(0.35)
                    weight_text.next_to(arrow.get_center(), DOWN, buff=0.1)
                    weight_labels.add(weight_text)

                attention_arrows.add(arrow)

            self.play(
                LaggedStart(
                    *[Create(arrow) for arrow in attention_arrows], lag_ratio=0.05
                )
            )
            if len(weight_labels) > 0:
                self.play(
                    LaggedStart(
                        *[FadeIn(label) for label in weight_labels], lag_ratio=0.05
                    )
                )

            # Highlight strongest connections
            max_weight_idx = weights.index(max(weights))
            if max_weight_idx != focus_idx:
                strongest_connection = SurroundingRectangle(
                    word_objects[max_weight_idx], color=SUCCESS_COLOR, buff=0.1
                )
                self.play(Create(strongest_connection))

                relationship_text = Text(
                    f"'{focus_word_str}' attends most to '{words[max_weight_idx]}'",
                    font="Arial",
                ).scale(0.5)
                relationship_text.to_edge(DOWN, buff=1.5)
                self.play(Write(relationship_text))

            self.wait(2)

            # Clear for next example
            self.play(
                FadeOut(focus_highlight),
                FadeOut(focus_label),
                FadeOut(attention_arrows),
                FadeOut(weight_labels),
                *(
                    [FadeOut(strongest_connection), FadeOut(relationship_text)]
                    if max_weight_idx != focus_idx
                    else []
                ),
            )

        self.wait(1)
        self.clear()

        # Part 3: Attention patterns analysis
        patterns_title = (
            Text("Common Attention Patterns", font="Arial").scale(0.9).set_color(ACCENT)
        )
        patterns_title.to_edge(UP, buff=1.0)
        self.play(Write(patterns_title))

        # Pattern 1: Syntactic dependencies
        pattern1_title = (
            Text("Pattern 1: Syntactic Dependencies", font="Arial")
            .scale(0.7)
            .set_color(BLUE)
        )
        pattern1_example = Text(
            "'dogs' attends to 'bark' (subject-verb)", font="Arial"
        ).scale(0.6)
        pattern1_group = VGroup(pattern1_title, pattern1_example).arrange(
            DOWN, buff=0.3
        )

        # Pattern 2: Semantic relationships
        pattern2_title = (
            Text("Pattern 2: Semantic Relationships", font="Arial")
            .scale(0.7)
            .set_color(GREEN)
        )
        pattern2_example = Text(
            "'king' attends to 'queen', 'crown', 'palace'", font="Arial"
        ).scale(0.6)
        pattern2_group = VGroup(pattern2_title, pattern2_example).arrange(
            DOWN, buff=0.3
        )

        # Pattern 3: Positional relationships
        pattern3_title = (
            Text("Pattern 3: Positional Relationships", font="Arial")
            .scale(0.7)
            .set_color(PURPLE)
        )
        pattern3_example = Text("Words attend to nearby positions", font="Arial").scale(
            0.6
        )
        pattern3_group = VGroup(pattern3_title, pattern3_example).arrange(
            DOWN, buff=0.3
        )

        # Pattern 4: Task-specific patterns
        pattern4_title = (
            Text("Pattern 4: Task-Specific Patterns", font="Arial")
            .scale(0.7)
            .set_color(ORANGE)
        )
        pattern4_example = Text(
            "In translation: source words → target words", font="Arial"
        ).scale(0.6)
        pattern4_group = VGroup(pattern4_title, pattern4_example).arrange(
            DOWN, buff=0.3
        )

        patterns = VGroup(
            pattern1_group, pattern2_group, pattern3_group, pattern4_group
        )
        patterns.arrange(DOWN, buff=0.8, aligned_edge=LEFT)
        patterns.next_to(patterns_title, DOWN, buff=1.0)

        for pattern in patterns:
            self.play(FadeIn(pattern, shift=RIGHT * 0.3), run_time=1.2)
            self.wait(0.5)

        self.wait(2)

        # Part 4: Matrix visualization with heatmap
        self.clear()
        matrix_title = (
            Text("Attention Matrix Visualization", font="Arial")
            .scale(0.9)
            .set_color(ACCENT)
        )
        matrix_title.to_edge(UP, buff=1.0)
        self.play(Write(matrix_title))

        # Create sentence for matrix
        matrix_sentence = "The cat sat on the mat"
        matrix_words = matrix_sentence.split()

        # Word labels
        word_labels_h = VGroup(
            *[Text(word, font="Arial").scale(0.4) for word in matrix_words]
        )
        word_labels_h.arrange(RIGHT, buff=0.6)

        word_labels_v = VGroup(
            *[Text(word, font="Arial").scale(0.4) for word in matrix_words]
        )
        word_labels_v.arrange(DOWN, buff=0.6)

        # Create attention matrix with realistic values
        attention_matrix_values = [
            [0.4, 0.1, 0.1, 0.1, 0.2, 0.1],  # The
            [0.1, 0.3, 0.1, 0.1, 0.1, 0.3],  # cat
            [0.1, 0.2, 0.4, 0.1, 0.1, 0.1],  # sat
            [0.1, 0.1, 0.2, 0.3, 0.2, 0.1],  # on
            [0.3, 0.1, 0.1, 0.1, 0.3, 0.1],  # the
            [0.1, 0.3, 0.1, 0.1, 0.1, 0.3],  # mat
        ]

        # Create matrix visualization
        matrix_grid = VGroup()
        cell_size = 0.6

        for i in range(len(matrix_words)):
            for j in range(len(matrix_words)):
                weight = attention_matrix_values[i][j]

                # Color intensity based on attention weight
                cell = Square(
                    side_length=cell_size,
                    fill_color=BLUE,
                    fill_opacity=weight,
                    stroke_color=WHITE,
                    stroke_width=1,
                )

                # Add weight text
                weight_text = Text(f"{weight:.1f}", font="Arial").scale(0.3)
                if weight > 0.2:
                    weight_text.set_color(WHITE)
                else:
                    weight_text.set_color(BLACK)

                cell_group = VGroup(cell, weight_text)
                cell_group.move_to([j * cell_size, -i * cell_size, 0])
                matrix_grid.add(cell_group)

        # Position everything
        matrix_grid.center()
        word_labels_h.next_to(matrix_grid, UP, buff=0.3)
        word_labels_v.next_to(matrix_grid, LEFT, buff=0.3)

        # Animate matrix construction
        self.play(FadeIn(word_labels_h), FadeIn(word_labels_v))
        self.play(LaggedStart(*[FadeIn(cell) for cell in matrix_grid], lag_ratio=0.02))

        # Add axis labels
        query_label = Text("Query →", font="Arial").scale(0.5).set_color(SECONDARY)
        query_label.next_to(word_labels_v, LEFT, buff=0.3).rotate(PI / 2)

        key_label = Text("Key →", font="Arial").scale(0.5).set_color(SECONDARY)
        key_label.next_to(word_labels_h, UP, buff=0.3)

        self.play(Write(query_label), Write(key_label))

        # Highlight interesting patterns
        self.wait(1)

        # Highlight cat-mat relationship
        cat_mat_highlight = SurroundingRectangle(
            matrix_grid[5], color=SUCCESS_COLOR, buff=0.1
        )  # cat row, mat column
        mat_cat_highlight = SurroundingRectangle(
            matrix_grid[31], color=SUCCESS_COLOR, buff=0.1
        )  # mat row, cat column

        relationship_note = (
            Text("Strong bidirectional attention: cat ↔ mat", font="Arial")
            .scale(0.6)
            .set_color(SUCCESS_COLOR)
        )
        relationship_note.to_edge(DOWN, buff=1.0)

        self.play(Create(cat_mat_highlight), Create(mat_cat_highlight))
        self.play(Write(relationship_note))

        self.wait(3)


# ----------------------------
# 4) Multi-Head Attention Deep Dive
# ----------------------------
class Scene_MultiHeadDetailed(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(
            self, "Multi-Head Attention", "Parallel Attention in Different Subspaces"
        )

        # Mathematical formulation
        eq_group = VGroup()

        main_eq = MathTex(
            r"\text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O"
        ).scale(Style.eq_scale)

        head_eq = MathTex(
            r"\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)"
        ).scale(Style.eq_scale)

        eq_group.add(main_eq, head_eq)
        eq_group.arrange(DOWN, buff=0.5)
        eq_group.to_edge(UP, buff=1.0)

        self.play(Write(main_eq), run_time=1.5)
        self.play(Write(head_eq), run_time=1.5)

        # Visualization of parallel heads
        input_rep = labeled_block(
            "Input\n(d_model)", width=2.5, height=1.5, color=SECONDARY
        )
        input_rep.to_edge(LEFT, buff=1.0).shift(DOWN * 0.5)
        self.play(FadeIn(input_rep))

        # Multiple attention heads
        num_heads = 4
        heads = VGroup()

        for i in range(num_heads):
            head = VGroup()

            # Projection matrices
            wq = labeled_block(f"W^Q_{i+1}", width=1.5, height=0.8, color=BLUE)
            wk = labeled_block(f"W^K_{i+1}", width=1.5, height=0.8, color=GREEN)
            wv = labeled_block(f"W^V_{i+1}", width=1.5, height=0.8, color=PURPLE)

            projections = VGroup(wq, wk, wv).arrange(DOWN, buff=0.2)

            # Attention computation
            attention = labeled_block(
                f"Attention\nHead {i+1}", width=2.0, height=1.2, color=ACCENT
            )

            head.add(projections, attention)
            head.arrange(RIGHT, buff=0.8)
            heads.add(head)

        heads.arrange(DOWN, buff=0.6)
        heads.next_to(input_rep, RIGHT, buff=1.5)

        # Animate heads one by one
        for i, head in enumerate(heads):
            # Input to projections
            for proj in head[0]:
                arrow = Arrow(input_rep.get_right(), proj.get_left(), buff=0.1)
                self.play(Create(arrow), FadeIn(proj), run_time=0.5)

            # Projections to attention
            attention_arrows = VGroup()
            for proj in head[0]:
                arr = Arrow(proj.get_right(), head[1].get_left(), buff=0.1)
                attention_arrows.add(arr)

            self.play(Create(attention_arrows), FadeIn(head[1]), run_time=0.8)

        # Concatenation and output projection
        concat = labeled_block("Concatenate", width=2.5, height=1.0, color=HIGHLIGHT)
        output_proj = labeled_block("W^O", width=2.0, height=1.0, color=SUCCESS_COLOR)
        final_output = labeled_block(
            "Output\n(d_model)", width=2.5, height=1.5, color=SECONDARY
        )

        output_flow = VGroup(concat, output_proj, final_output)
        output_flow.arrange(RIGHT, buff=0.8)
        output_flow.next_to(heads, RIGHT, buff=1.2)

        # Connect heads to concatenation
        for head in heads:
            arrow = Arrow(head[1].get_right(), concat.get_left(), buff=0.1)
            self.play(Create(arrow), run_time=0.3)

        self.play(FadeIn(concat))

        # Final projection
        concat_arrow = Arrow(concat.get_right(), output_proj.get_left(), buff=0.1)
        self.play(Create(concat_arrow), FadeIn(output_proj))

        output_arrow = Arrow(output_proj.get_right(), final_output.get_left(), buff=0.1)
        self.play(Create(output_arrow), FadeIn(final_output))

        # Benefits explanation
        benefits_title = (
            Text("Why Multiple Heads?", font="Arial").scale(0.8).set_color(ACCENT)
        )
        benefits = bullet_list(
            [
                "Each head can focus on different types of relationships",
                "Some heads capture syntactic patterns, others semantic",
                "Increased model capacity without increasing computation per head",
                "Different heads can attend to different positions simultaneously",
            ],
            width=11.0,
            color=TEXT,
        )

        benefits_group = VGroup(benefits_title, benefits)
        benefits_group.arrange(DOWN, buff=0.5)
        benefits_group.to_edge(DOWN, buff=0.5)

        self.play(Write(benefits_title))
        self.play(FadeIn(benefits, lag_ratio=0.3))
        self.wait(2)


# ----------------------------
# 5) Positional Encoding Deep Dive
# ----------------------------
class Scene_PositionalEncodingDetailed(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(self, "Positional Encoding", "Injecting Order Without Recurrence")

        # Mathematical formulation
        eq1 = MathTex(
            r"PE_{(pos,2i)} = \sin\left(\frac{pos}{10000^{2i/d_{model}}}\right)"
        ).scale(Style.eq_scale)
        eq2 = MathTex(
            r"PE_{(pos,2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{model}}}\right)"
        ).scale(Style.eq_scale)

        equations = VGroup(eq1, eq2).arrange(DOWN, buff=0.4)
        equations.to_edge(UP, buff=1.0)

        self.play(Write(eq1), run_time=1.5)
        self.play(Write(eq2), run_time=1.5)

        # Visualization of sine/cosine waves at different frequencies
        axes = Axes(
            x_range=[0, 20, 5],
            y_range=[-1.5, 1.5, 0.5],
            tips=False,
            axis_config={"color": SECONDARY},
        ).scale(0.8)
        axes.to_edge(LEFT, buff=0.5).shift(DOWN * 1.0)

        self.play(Create(axes))

        # Plot multiple frequencies
        frequencies = [1, 0.5, 0.25, 0.125]
        colors = [RED, BLUE, GREEN, PURPLE]
        functions = []
        labels = VGroup()

        for i, (freq, color) in enumerate(zip(frequencies, colors)):
            if i % 2 == 0:  # Sine for even dimensions
                func = axes.plot(lambda x, f=freq: np.sin(x * f), color=color)
                label_text = f"sin(pos/{int(1/freq)})"
            else:  # Cosine for odd dimensions
                func = axes.plot(lambda x, f=freq: np.cos(x * f), color=color)
                label_text = f"cos(pos/{int(1/freq)})"

            functions.append(func)
            label = Text(label_text, font="Arial").scale(0.4).set_color(color)
            labels.add(label)

        # Animate functions
        for func in functions:
            self.play(Create(func), run_time=1.0)

        # Add legend
        labels.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        labels.next_to(axes, RIGHT, buff=0.5)
        self.play(FadeIn(labels))

        # Position encoding matrix visualization
        pe_title = Text("PE Matrix Structure", font="Arial").scale(0.7)
        pe_title.to_edge(RIGHT, buff=1.0).shift(UP * 1.5)
        self.play(Write(pe_title))

        # Create a heatmap-style visualization
        pe_matrix = VGroup()
        matrix_rows, matrix_cols = 8, 12  # positions x dimensions
        cell_size = 0.25

        for pos in range(matrix_rows):
            for dim in range(matrix_cols):
                # Calculate actual PE value
                if dim % 2 == 0:  # sine
                    freq = 10000 ** (dim / matrix_cols)
                    value = np.sin(pos / freq)
                else:  # cosine
                    freq = 10000 ** ((dim - 1) / matrix_cols)
                    value = np.cos(pos / freq)

                # Map to color intensity
                intensity = (value + 1) / 2  # Normalize to [0,1]
                cell = Square(
                    side_length=cell_size,
                    color=BLUE,
                    fill_opacity=intensity,
                    stroke_width=0.5,
                )
                cell.move_to([dim * cell_size, -pos * cell_size, 0])
                pe_matrix.add(cell)

        pe_matrix.next_to(pe_title, DOWN, buff=0.3)
        self.play(FadeIn(pe_matrix, lag_ratio=0.02))

        # Add axis labels
        pos_label = (
            Text("Position", font="Arial")
            .scale(0.5)
            .next_to(pe_matrix, LEFT, buff=0.3)
            .rotate(PI / 2)
        )
        dim_label = (
            Text("Dimension", font="Arial")
            .scale(0.5)
            .next_to(pe_matrix, DOWN, buff=0.3)
        )
        self.play(Write(pos_label), Write(dim_label))

        # Properties explanation
        properties_title = (
            Text("Key Properties", font="Arial").scale(0.8).set_color(ACCENT)
        )
        properties = bullet_list(
            [
                "Deterministic: Same position always gets same encoding",
                "Relative positions: PE(pos+k) can be expressed as linear function of PE(pos)",
                "Bounded: All values in [-1, 1] range",
                "Unique: Each position gets a unique encoding pattern",
                "Extrapolation: Can handle longer sequences than seen in training",
            ],
            width=10.0,
            color=TEXT,
        )

        properties_group = VGroup(properties_title, properties)
        properties_group.arrange(DOWN, buff=0.4)
        properties_group.to_edge(DOWN, buff=0.5)

        self.play(Write(properties_title))
        self.play(FadeIn(properties, lag_ratio=0.3))
        self.wait(2)


# ----------------------------
# 6) Complete Transformer Architecture
# ----------------------------
class Scene_FullArchitecture(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(
            self,
            "Complete Transformer Architecture",
            "Encoder-Decoder with All Components",
        )

        # Left side: Encoder stack
        encoder_title = Text("Encoder", font="Arial").scale(0.8).set_color(ACCENT)
        encoder_stack = VGroup()

        for i in range(3):  # Show 3 layers for clarity
            layer = VGroup()

            # Multi-head self-attention
            mha = labeled_block(
                "Multi-Head\nSelf-Attention", width=3.0, height=1.0, color=BLUE
            )
            add_norm1 = labeled_block(
                "Add & Norm", width=3.0, height=0.6, color=SECONDARY
            )

            # Feed-forward network
            ffn = labeled_block(
                "Feed Forward\nNetwork", width=3.0, height=1.0, color=GREEN
            )
            add_norm2 = labeled_block(
                "Add & Norm", width=3.0, height=0.6, color=SECONDARY
            )

            layer.add(mha, add_norm1, ffn, add_norm2)
            layer.arrange(DOWN, buff=0.2)
            encoder_stack.add(layer)

        encoder_stack.arrange(DOWN, buff=0.5)
        encoder_group = VGroup(encoder_title, encoder_stack)
        encoder_group.arrange(DOWN, buff=0.3)
        encoder_group.to_edge(LEFT, buff=0.5)

        # Right side: Decoder stack
        decoder_title = Text("Decoder", font="Arial").scale(0.8).set_color(ACCENT)
        decoder_stack = VGroup()

        for i in range(3):
            layer = VGroup()

            # Masked multi-head self-attention
            masked_mha = labeled_block(
                "Masked Multi-Head\nSelf-Attention", width=3.2, height=1.0, color=PURPLE
            )
            add_norm1 = labeled_block(
                "Add & Norm", width=3.2, height=0.6, color=SECONDARY
            )

            # Multi-head cross-attention
            cross_mha = labeled_block(
                "Multi-Head\nCross-Attention", width=3.2, height=1.0, color=RED
            )
            add_norm2 = labeled_block(
                "Add & Norm", width=3.2, height=0.6, color=SECONDARY
            )

            # Feed-forward network
            ffn = labeled_block(
                "Feed Forward\nNetwork", width=3.2, height=1.0, color=GREEN
            )
            add_norm3 = labeled_block(
                "Add & Norm", width=3.2, height=0.6, color=SECONDARY
            )

            layer.add(masked_mha, add_norm1, cross_mha, add_norm2, ffn, add_norm3)
            layer.arrange(DOWN, buff=0.2)
            decoder_stack.add(layer)

        decoder_stack.arrange(DOWN, buff=0.5)
        decoder_group = VGroup(decoder_title, decoder_stack)
        decoder_group.arrange(DOWN, buff=0.3)
        decoder_group.to_edge(RIGHT, buff=0.5)

        # Animate architecture construction
        self.play(Write(encoder_title))
        for layer in encoder_stack:
            self.play(FadeIn(layer, shift=UP * 0.3), run_time=1.0)

        self.play(Write(decoder_title))
        for layer in decoder_stack:
            self.play(FadeIn(layer, shift=UP * 0.3), run_time=1.0)

        # Add cross-connections
        cross_connections = VGroup()
        for enc_layer, dec_layer in zip(encoder_stack, decoder_stack):
            # Connect encoder output to decoder cross-attention
            arrow = Arrow(
                enc_layer.get_right(),
                dec_layer[2].get_left(),  # Cross-attention block
                buff=0.1,
                color=YELLOW,
                stroke_width=3,
            )
            cross_connections.add(arrow)

        self.play(
            LaggedStart(*[Create(arrow) for arrow in cross_connections], lag_ratio=0.3)
        )

        # Input/Output flow
        # Encoder input
        enc_input = labeled_block(
            "Input Embeddings\n+ Positional Encoding",
            width=3.5,
            height=1.0,
            color=HIGHLIGHT,
        )
        enc_input.next_to(encoder_stack, DOWN, buff=0.8)
        enc_input_arrow = Arrow(
            enc_input.get_top(), encoder_stack[-1].get_bottom(), buff=0.1
        )

        self.play(FadeIn(enc_input), Create(enc_input_arrow))

        # Decoder input/output
        dec_input = labeled_block(
            "Output Embeddings\n+ Positional Encoding",
            width=3.5,
            height=1.0,
            color=HIGHLIGHT,
        )
        dec_input.next_to(decoder_stack, DOWN, buff=0.8)
        dec_input_arrow = Arrow(
            dec_input.get_top(), decoder_stack[-1].get_bottom(), buff=0.1
        )

        linear_softmax = labeled_block(
            "Linear + Softmax", width=3.2, height=0.8, color=SUCCESS_COLOR
        )
        linear_softmax.next_to(decoder_stack, UP, buff=0.8)
        output_arrow = Arrow(
            decoder_stack[0].get_top(), linear_softmax.get_bottom(), buff=0.1
        )

        self.play(FadeIn(dec_input), Create(dec_input_arrow))
        self.play(FadeIn(linear_softmax), Create(output_arrow))

        # Final output
        output_probs = labeled_block(
            "Output Probabilities", width=3.2, height=0.8, color=SUCCESS_COLOR
        )
        output_probs.next_to(linear_softmax, UP, buff=0.3)
        final_arrow = Arrow(
            linear_softmax.get_top(), output_probs.get_bottom(), buff=0.1
        )

        self.play(FadeIn(output_probs), Create(final_arrow))

        # Key architectural notes
        notes = bullet_list(
            [
                "Residual connections around each sub-layer",
                "Layer normalization applied after each sub-layer",
                "Decoder uses causal masking to prevent future peeking",
                "Cross-attention allows decoder to attend to encoder output",
            ],
            width=12.0,
            color=TEXT,
        )

        notes.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(notes, lag_ratio=0.2))
        self.wait(3)


# ----------------------------
# 7) Training Details and Optimization
# ----------------------------
class Scene_TrainingDetails(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(
            self, "Training Methodology", "Optimization and Regularization Techniques"
        )

        # Learning rate schedule
        lr_title = (
            Text("Learning Rate Schedule", font="Arial").scale(0.8).set_color(ACCENT)
        )
        lr_eq = MathTex(
            r"\text{lrate} = d_{\text{model}}^{-0.5} \cdot \min(\text{step}^{-0.5}, \text{step} \cdot \text{warmup\_steps}^{-1.5})"
        ).scale(Style.small_eq_scale)

        lr_group = VGroup(lr_title, lr_eq)
        lr_group.arrange(DOWN, buff=0.3)
        lr_group.to_edge(UP, buff=1.0)

        self.play(Write(lr_title))
        self.play(Write(lr_eq))

        # Learning rate curve visualization
        axes = Axes(
            x_range=[0, 10000, 2000],
            y_range=[0, 0.002, 0.0005],
            tips=False,
            axis_config={"color": SECONDARY},
        ).scale(0.7)
        axes.to_edge(LEFT, buff=1.0)

        # Learning rate function
        warmup_steps = 4000
        d_model = 512

        def lr_func(step):
            if step == 0:
                return 0
            return d_model ** (-0.5) * min(
                step ** (-0.5), step * warmup_steps ** (-1.5)
            )

        steps = np.linspace(1, 10000, 1000)
        lr_values = [lr_func(step) for step in steps]

        lr_curve = axes.plot_line_graph(
            x_values=steps, y_values=lr_values, line_color=ACCENT, stroke_width=3
        )

        self.play(Create(axes))
        self.play(Create(lr_curve))

        # Mark warmup phase
        warmup_line = axes.get_vertical_line(
            axes.c2p(warmup_steps, 0), color=RED, stroke_width=2
        )
        warmup_label = (
            Text("Warmup\n4000 steps", font="Arial").scale(0.5).set_color(RED)
        )
        warmup_label.next_to(warmup_line, UP, buff=0.2)

        self.play(Create(warmup_line), Write(warmup_label))

        # Training configuration
        config_title = (
            Text("Training Configuration", font="Arial").scale(0.8).set_color(ACCENT)
        )
        config_details = bullet_list(
            [
                r"Optimizer: Adam ($\beta_1=0.9$, $\beta_2=0.98$, $\epsilon=10^{-9}$)",
                "Warmup steps: 4,000",
                "Training steps: 100K (base), 300K (big)",
                "Hardware: 8 NVIDIA P100 GPUs",
                "Batch size: ~25K source + 25K target tokens",
            ],
            width=10.0,
            color=TEXT,
        )

        config_group = VGroup(config_title, config_details)
        config_group.arrange(DOWN, buff=0.3)
        config_group.next_to(axes, RIGHT, buff=1.0)

        self.play(Write(config_title))
        self.play(FadeIn(config_details, lag_ratio=0.2))

        # Regularization techniques
        reg_title = Text("Regularization", font="Arial").scale(0.8).set_color(ACCENT)

        # Dropout illustration
        dropout_demo = VGroup()
        neurons = VGroup(
            *[Circle(radius=0.1, color=BLUE, fill_opacity=0.7) for _ in range(12)]
        )
        neurons.arrange_in_grid(rows=3, cols=4, buff=0.3)

        # Randomly "dropout" some neurons
        dropped_indices = [1, 3, 5, 7, 10]
        for i in dropped_indices:
            neurons[i].set_color(RED).set_fill_opacity(0.3)

        dropout_label = Text("Dropout (p=0.1)", font="Arial").scale(0.6)
        dropout_group = VGroup(dropout_label, dropout_demo)
        dropout_group.arrange(DOWN, buff=0.3)

        # Label smoothing illustration
        ls_title = Text("Label Smoothing", font="Arial").scale(0.6)

        # Before/after probability distributions
        true_dist = [0, 0, 1, 0, 0]  # One-hot
        smooth_dist = [0.025, 0.025, 0.9, 0.025, 0.025]  # Smoothed

        bars_before = VGroup(
            *[
                Rectangle(width=0.3, height=p * 2, color=BLUE, fill_opacity=0.7)
                for p in true_dist
            ]
        )
        bars_after = VGroup(
            *[
                Rectangle(width=0.3, height=p * 2, color=GREEN, fill_opacity=0.7)
                for p in smooth_dist
            ]
        )

        bars_before.arrange(RIGHT, buff=0.1)
        bars_after.arrange(RIGHT, buff=0.1)

        before_label = Text("Before", font="Arial").scale(0.4)
        after_label = Text("After", font="Arial").scale(0.4)

        ls_demo = VGroup(
            VGroup(before_label, bars_before).arrange(DOWN, buff=0.2),
            VGroup(after_label, bars_after).arrange(DOWN, buff=0.2),
        ).arrange(RIGHT, buff=0.8)

        ls_group = VGroup(ls_title, ls_demo)
        ls_group.arrange(DOWN, buff=0.3)

        reg_techniques = VGroup(dropout_group, ls_group)
        reg_techniques.arrange(RIGHT, buff=1.5)

        reg_content = VGroup(reg_title, reg_techniques)
        reg_content.arrange(DOWN, buff=0.5)
        reg_content.to_edge(DOWN, buff=1.0)

        self.play(Write(reg_title))
        self.play(FadeIn(dropout_group), FadeIn(ls_group))

        self.wait(2)


# ----------------------------
# 8) Results and Impact
# ----------------------------
class Scene_ResultsImpact(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(
            self,
            "Results and Impact",
            "Translation Quality and Computational Efficiency",
        )

        # BLEU score comparison
        bleu_title = (
            Text("BLEU Score Improvements", font="Arial").scale(0.8).set_color(ACCENT)
        )
        bleu_title.to_edge(UP, buff=1.5)
        self.play(Write(bleu_title))

        # EN-DE results
        ende_title = Text("English → German", font="Arial").scale(0.7)
        ende_models = ["Previous SOTA", "Transformer Base", "Transformer Big"]
        ende_scores = [27.3, 27.3, 28.4]
        ende_colors = [SECONDARY, BLUE, SUCCESS_COLOR]

        ende_bars = VGroup()
        for model, score, color in zip(ende_models, ende_scores, ende_colors):
            bar = Rectangle(width=1.0, height=score / 10, color=color, fill_opacity=0.8)
            label = Text(model, font="Arial").scale(0.4).rotate(PI / 6)
            score_text = Text(f"{score}", font="Arial").scale(0.5)

            bar_group = VGroup(bar, label, score_text)
            label.next_to(bar, DOWN, buff=0.2)
            score_text.next_to(bar, UP, buff=0.1)
            ende_bars.add(bar_group)

        ende_bars.arrange(RIGHT, buff=0.8)
        ende_chart = VGroup(ende_title, ende_bars)
        ende_chart.arrange(DOWN, buff=0.5)

        # EN-FR results
        enfr_title = Text("English → French", font="Arial").scale(0.7)
        enfr_models = ["Previous SOTA", "Transformer Base", "Transformer Big"]
        enfr_scores = [41.0, 38.1, 41.8]
        enfr_colors = [SECONDARY, BLUE, SUCCESS_COLOR]

        enfr_bars = VGroup()
        for model, score, color in zip(enfr_models, enfr_scores, enfr_colors):
            bar = Rectangle(width=1.0, height=score / 15, color=color, fill_opacity=0.8)
            label = Text(model, font="Arial").scale(0.4).rotate(PI / 6)
            score_text = Text(f"{score}", font="Arial").scale(0.5)

            bar_group = VGroup(bar, label, score_text)
            label.next_to(bar, DOWN, buff=0.2)
            score_text.next_to(bar, UP, buff=0.1)
            enfr_bars.add(bar_group)

        enfr_bars.arrange(RIGHT, buff=0.8)
        enfr_chart = VGroup(enfr_title, enfr_bars)
        enfr_chart.arrange(DOWN, buff=0.5)

        # Arrange both charts
        charts = VGroup(ende_chart, enfr_chart)
        charts.arrange(RIGHT, buff=2.0)
        charts.next_to(bleu_title, DOWN, buff=1.0)

        self.play(
            LaggedStart(*[FadeIn(chart, shift=UP) for chart in charts], lag_ratio=0.5)
        )

        # Training cost comparison
        cost_title = (
            Text("Training Cost Reduction", font="Arial").scale(0.8).set_color(ACCENT)
        )
        cost_comparison = bullet_list(
            [
                "Transformer Big: 3.5 days on 8 P100 GPUs",
                "Previous SOTA ensemble: Weeks of training",
                "Massive parallelization reduces wall-clock time",
                "Better performance with lower computational cost",
            ],
            width=10.0,
            color=TEXT,
        )

        cost_group = VGroup(cost_title, cost_comparison)
        cost_group.arrange(DOWN, buff=0.4)
        cost_group.next_to(charts, DOWN, buff=1.0)

        self.play(Write(cost_title))
        self.play(FadeIn(cost_comparison, lag_ratio=0.2))

        # Impact on the field
        impact_title = (
            Text("Revolutionary Impact", font="Arial").scale(0.8).set_color(HIGHLIGHT)
        )
        impact_points = bullet_list(
            [
                "Foundation for GPT family (GPT-1, GPT-2, GPT-3, GPT-4)",
                "Enabled BERT and bidirectional encoder architectures",
                "Sparked the large language model revolution",
                "Applications beyond NLP: Vision Transformers, protein folding",
                "Democratized access to powerful sequence modeling",
            ],
            width=12.0,
            color=TEXT,
        )

        impact_group = VGroup(impact_title, impact_points)
        impact_group.arrange(DOWN, buff=0.4)
        impact_group.to_edge(DOWN, buff=0.5)

        self.play(Write(impact_title))
        self.play(FadeIn(impact_points, lag_ratio=0.3))

        # Timeline of transformer variants
        timeline_title = (
            Text("Transformer Family Tree", font="Arial").scale(0.7).set_color(ACCENT)
        )

        variants = [
            ("2017", "Transformer"),
            ("2018", "BERT"),
            ("2018", "GPT-1"),
            ("2019", "GPT-2"),
            ("2020", "GPT-3"),
            ("2020", "ViT"),
            ("2023", "GPT-4"),
        ]

        timeline = VGroup()
        for year, model in variants:
            milestone = VGroup(
                Text(year, font="Arial").scale(0.4).set_color(SECONDARY),
                Text(model, font="Arial").scale(0.5),
                Circle(radius=0.1, color=ACCENT, fill_opacity=0.7),
            )
            milestone.arrange(DOWN, buff=0.1)
            timeline.add(milestone)

        timeline.arrange(RIGHT, buff=0.8)
        timeline_group = VGroup(timeline_title, timeline)
        timeline_group.arrange(DOWN, buff=0.3)

        # Position timeline at the bottom
        timeline_group.scale(0.8).to_edge(DOWN, buff=0.2)

        self.play(Write(timeline_title))
        self.play(
            LaggedStart(
                *[FadeIn(milestone, shift=UP) for milestone in timeline], lag_ratio=0.2
            )
        )

        self.wait(3)


# ----------------------------
# 9) Conclusion and Future Directions
# ----------------------------
class Scene_Conclusion(Scene):
    def construct(self):
        self.camera.background_color = BG
        title_block(self, "Conclusion", "The Transformer's Lasting Legacy")

        # Key innovations summary
        innovations_title = (
            Text("Revolutionary Innovations", font="Arial").scale(0.9).set_color(ACCENT)
        )
        innovations = bullet_list(
            [
                "Eliminated recurrence: Pure attention-based architecture",
                "Self-attention: Global context in constant sequential depth",
                "Multi-head attention: Parallel processing of different relationships",
                "Positional encoding: Order without recurrence",
                "Scalable training: Massive parallelization capabilities",
            ],
            width=12.0,
            color=TEXT,
        )

        innovations_box = SurroundingRectangle(innovations, color=ACCENT, buff=0.4)
        innovations_group = VGroup(innovations_title, innovations, innovations_box)
        innovations_group.arrange(DOWN, buff=0.4)
        innovations_group.to_edge(UP, buff=1.0)

        self.play(Write(innovations_title))
        self.play(FadeIn(innovations, lag_ratio=0.2))
        self.play(Create(innovations_box))

        # Impact metrics
        metrics_title = (
            Text("By the Numbers", font="Arial").scale(0.8).set_color(SUCCESS_COLOR)
        )

        metrics = VGroup()
        metric_data = [
            ("Citations", "50,000+"),
            ("Model Parameters", "100M → 1T+"),
            ("Applications", "NLP, Vision, Audio, Biology"),
            ("Training Cost", "90% reduction"),
            ("Performance", "SOTA across tasks"),
        ]

        for label, value in metric_data:
            metric_item = VGroup(
                Text(label, font="Arial").scale(0.6).set_color(SECONDARY),
                Text(value, font="Arial").scale(0.8).set_color(SUCCESS_COLOR),
            )
            metric_item.arrange(DOWN, buff=0.2)
            metrics.add(metric_item)

        metrics.arrange(RIGHT, buff=1.0)
        metrics_group = VGroup(metrics_title, metrics)
        metrics_group.arrange(DOWN, buff=0.5)
        metrics_group.next_to(innovations_group, DOWN, buff=1.0)

        self.play(Write(metrics_title))
        self.play(
            LaggedStart(
                *[FadeIn(metric, shift=UP) for metric in metrics], lag_ratio=0.2
            )
        )

        # Future directions
        future_title = (
            Text("Future Directions", font="Arial").scale(0.8).set_color(HIGHLIGHT)
        )
        future_points = bullet_list(
            [
                "Efficiency improvements: Sparse attention, linear transformers",
                "Longer contexts: Handling sequences beyond current limits",
                "Multimodal fusion: Vision, text, audio integration",
                "Interpretability: Understanding what models learn",
                "Domain specialization: Optimized architectures for specific tasks",
            ],
            width=12.0,
            color=TEXT,
        )

        future_group = VGroup(future_title, future_points)
        future_group.arrange(DOWN, buff=0.4)
        future_group.next_to(metrics_group, DOWN, buff=1.0)

        self.play(Write(future_title))
        self.play(FadeIn(future_points, lag_ratio=0.2))

        # Final message
        final_message = (
            Text(
                '"Attention Is All You Need" - A Simple Idea That Changed Everything',
                font="Arial",
            )
            .scale(0.8)
            .set_color(ACCENT)
        )

        final_box = SurroundingRectangle(final_message, color=ACCENT, buff=0.5)
        final_group = VGroup(final_box, final_message)
        final_group.to_edge(DOWN, buff=0.5)

        self.play(Create(final_box))
        self.play(Write(final_message))

        # Closing animation - attention visualization
        attention_demo = VGroup()
        nodes = VGroup(
            *[Circle(radius=0.1, color=BLUE, fill_opacity=0.7) for _ in range(8)]
        )
        nodes.arrange_in_grid(rows=2, cols=4, buff=0.8)

        connections = VGroup()
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i != j:
                    connection = Line(
                        node1.get_center(),
                        node2.get_center(),
                        stroke_width=1,
                        stroke_opacity=0.3,
                        color=ACCENT,
                    )
                    connections.add(connection)

        attention_demo.add(connections, nodes)
        attention_demo.scale(0.6).next_to(final_group, UP, buff=0.5)

        self.play(FadeIn(attention_demo))

        # Animate connections
        for connection in connections:
            self.play(connection.animate.set_stroke_opacity(0.8), run_time=0.1)
            self.play(connection.animate.set_stroke_opacity(0.3), run_time=0.1)

        self.wait(3)


# ----------------------------
# Master Scene - Complete Tutorial
# ----------------------------
class ComprehensiveTransformerTutorial(Scene):
    def construct(self):
        """Complete tutorial combining all scenes"""
        self.camera.background_color = BG

        # Run all scenes in sequence
        scenes = [
            Scene_Intro,
            Scene_AttentionMath,
            Scene_AttentionVisualization,
            Scene_MultiHeadDetailed,
            Scene_PositionalEncodingDetailed,
            Scene_FullArchitecture,
            Scene_TrainingDetails,
            Scene_ResultsImpact,
            Scene_Conclusion,
        ]

        for scene_class in scenes:
            scene = scene_class()
            scene.construct()
            self.wait(2)
            self.clear()


if __name__ == "__main__":
    # Example usage:
    # manim -pqh comprehensive_transformer_tutorial.py Scene_Intro
    # manim -pqh comprehensive_transformer_tutorial.py ComprehensiveTransformerTutorial
    pass
