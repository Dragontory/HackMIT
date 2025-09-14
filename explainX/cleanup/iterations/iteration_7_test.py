from manim import *
import numpy as np

class AttentionMechanismsInNMT(Scene):
    def construct(self):
        # Title and introduction
        title = Text("Attention Mechanisms in Neural Machine Translation", font_size=40)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(2)
        self.play(FadeOut(title))
        self.wait(0.8)
        
        section_title = Text("Vanilla Encoder-Decoder NMT", font_size=36)
        section_title.to_edge(UP)
        section_title = Text("Vanilla Encoder-Decoder NMT", font_size=36)
        self.play(Write(section_title))
        self.play(section_title.animate.to_edge(UP))
        self.wait(0.8)
        self.play(section_title.animate.to_edge(UP))
        
        # Create encoder-decoder diagram
        encoder = Rectangle(height=3, width=1.5, color=BLUE).shift(LEFT*3)
        encoder_label = Text("Encoder", font_size=24).next_to(encoder, DOWN)
        
        # Source sentence
        src_text = Text("The cat sat on the mat", font_size=20).next_to(encoder, LEFT, buff=0.5)
        src_arrows = [Arrow(src_text.get_right(), encoder.get_left(), color=BLUE_C)]
        
        # Context vector (bottleneck)
        context_vector = Circle(radius=0.5, color=YELLOW).shift(LEFT*0.5)
        context_label = Text("Fixed-size\nContext Vector", font_size=18).next_to(context_vector, DOWN)
        
        # Decoder
        decoder = Rectangle(height=3, width=1.5, color=RED).shift(RIGHT*3)
        decoder_label = Text("Decoder", font_size=24).next_to(decoder, DOWN)
        
        # Target sentence
        tgt_text = Text("Le chat s'assit sur le tapis", font_size=20).next_to(decoder, RIGHT, buff=0.5)
        tgt_arrows = [Arrow(decoder.get_right(), tgt_text.get_left(), color=RED_C)]
        
        # Arrows connecting components
        enc_to_ctx = Arrow(encoder.get_right(), context_vector.get_left(), color=BLUE_C)
        ctx_to_dec = Arrow(context_vector.get_right(), decoder.get_left(), color=RED_C)
        
        # Display the basic architecture
        self.play(
            Create(encoder), Write(encoder_label),
            Create(context_vector), Write(context_label),
            Create(decoder), Write(decoder_label)
        )
        self.play(Write(src_text), Create(enc_to_ctx), Create(ctx_to_dec))
        self.play(Write(tgt_text), *[Create(arrow) for arrow in src_arrows + tgt_arrows])
        self.wait(2)
        
        # Highlight the bottleneck problem
        bottleneck_highlight = Circle(radius=0.8, color=RED, stroke_width=3)
        bottleneck_text = Text("Bottleneck Problem", color=YELLOW, font_size=24).next_to(bottleneck_highlight, UP)
        self.play(Create(bottleneck_highlight), Write(bottleneck_text))
        self.wait(0.8)
        self.play(Create(bottleneck_highlight), Write(bottleneck_text))
        
        problem_desc = Text(
            "A single vector must encode all information\nfrom the source sentence, causing information loss",
            font_size=18
        ).to_edge(DOWN)
        self.play(Write(problem_desc))
        self.play(*[FadeOut(obj) for obj in self.mobjects])
        self.wait(0.8)
        
        # Clear the scene for the next part
        self.play(*[FadeOut(obj) for obj in self.mobjects])
        section_title = Text("Attention Mechanisms", font_size=36)
        section_title.to_edge(UP)
        self.play(section_title.animate.to_edge(UP))
        self.wait(0.8)
        section_title = Text("Attention Mechanisms", font_size=36)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))
        
        attention_desc = Text(
            "Attention allows the decoder to focus on\ndifferent parts of the source sentence\nat each decoding step",
            font_size=24
        )
        self.play(Write(attention_desc))
        self.wait(2)
        self.play(FadeOut(attention_desc))
        
        # Create a more detailed encoder-decoder with attention
        # Encoder hidden states
        encoder = Rectangle(height=3, width=1.5, color=BLUE).shift(LEFT*4)
        encoder_label = Text("Encoder", font_size=20).next_to(encoder, DOWN)
        
        # Source tokens and hidden states
        src_tokens = ["The", "cat", "sat", "on", "the", "mat"]
        src_text_objs = []
        hidden_states = []
        hidden_state_labels = []
        
        for i, token in enumerate(src_tokens):
            y_pos = 1.5 - i * 0.6
            text_obj = Text(token, font_size=16).move_to(LEFT*5.5 + UP*y_pos)
            src_text_objs.append(text_obj)
            
            h_state = Circle(radius=0.2, color=BLUE).move_to(LEFT*2.5 + UP*y_pos)
            h_label = MathTex(f"h_{i+1}", font_size=16).next_to(h_state, RIGHT, buff=0.1)
            hidden_states.append(h_state)
            hidden_state_labels.append(h_label)
        
        # Decoder and current state
        decoder = Rectangle(height=3, width=1.5, color=RED).shift(RIGHT*4)
        decoder_label = Text("Decoder", font_size=20).next_to(decoder, DOWN)
        
        # Current decoder state
        current_state = Circle(radius=0.3, color=RED).move_to(RIGHT*2.5)
        current_state_label = MathTex("s_t", font_size=20).next_to(current_state, LEFT, buff=0.1)
        
        # Target token being generated
        current_target = Text("chat", font_size=20).move_to(RIGHT*5.5)
        target_arrow = Arrow(decoder.get_right(), current_target.get_left(), color=RED_C)
        
        # Display encoder, decoder, and states
        self.play(
            Create(encoder), Write(encoder_label),
            Create(decoder), Write(decoder_label)
        )
        
        self.play(
            *[Write(text) for text in src_text_objs],
            *[Create(h) for h in hidden_states],
            *[Write(label) for label in hidden_state_labels]
        )
        
        self.play(
            Create(current_state), Write(current_state_label),
            Write(current_target), Create(target_arrow)
        )
        attention_title = Text("Attention Computation", font_size=28).next_to(section_title, DOWN)
        self.play(Write(attention_title))
        self.wait(0.8)
        self.wait(2)
        
        step1 = Text("Step 1: Calculate alignment scores", font_size=20).to_edge(DOWN, buff=1.5)
        self.play(Write(step1))
        self.wait(0.8)
        self.play(Write(attention_title))
        
        # Step 1: Calculate alignment scores
        self.play(Write(step1))
        
        # Alignment scores
        score_arrows = []
        score_labels = []
        
        for i, h_state in enumerate(hidden_states):
            arrow = Arrow(current_state.get_left(), h_state.get_right(), color=YELLOW, buff=0.1)
            score = MathTex(f"e_{{{i+1}}}", font_size=16).next_to(arrow, UP, buff=0.1)
            score_arrows.append(arrow)
            score_labels.append(score)
        
        self.play(
            *[Create(arrow) for arrow in score_arrows],
            *[Write(label) for label in score_labels]
        )
        self.wait(2)
        step2 = Text("Step 2: Apply softmax to get attention weights", font_size=20).to_edge(DOWN, buff=1.5)
        softmax_eq = MathTex(r"\alpha_{i} = \frac{\exp(e_i)}{\sum_j \exp(e_j)}", font_size=24).next_to(step2, UP)
        self.play(Write(softmax_eq))
        self.wait(0.8)
        # Step 2: Apply softmax to get attention weights
        self.play(FadeOut(step1))
        self.play(Write(step2))
        
        self.play(Write(softmax_eq))
        
        # Update arrows with attention weights
        weight_values = [0.1, 0.6, 0.2, 0.05, 0.03, 0.02]  # Example weights
        
        for i, (arrow, weight) in enumerate(zip(score_arrows, weight_values)):
            new_arrow = Arrow(
                current_state.get_left(), hidden_states[i].get_right(), 
                color=YELLOW, buff=0.1,
                stroke_width=weight*15  # Scale width by weight
            )
            new_label = MathTex(f"\\alpha_{{{i+1}}} = {weight}", font_size=16).next_to(new_arrow, UP, buff=0.1)
            self.play(
                ReplacementTransform(arrow, new_arrow),
                ReplacementTransform(score_labels[i], new_label)
            )
            score_arrows[i] = new_arrow
            score_labels[i] = new_label
        
        step3 = Text("Step 3: Compute context vector as weighted sum", font_size=20).to_edge(DOWN, buff=1.5)
        context_eq = MathTex(r"c_t = \sum_{i} \alpha_i h_i", font_size=24).next_to(step3, UP)
        self.play(Write(context_eq))
        self.wait(0.8)
        
        # Step 3: Compute context vector
        self.play(FadeOut(step2), FadeOut(softmax_eq))
        self.play(Write(step3))
        self.play(Create(context_vector), Write(context_label))
        self.wait(0.8)
        self.play(Write(context_eq))
        
        # Create context vector
        context_vector = Circle(radius=0.3, color=GREEN).move_to(RIGHT*1)
        context_label = MathTex("c_t", font_size=20).next_to(context_vector, DOWN, buff=0.1)
        
        # Animate hidden states flowing to context vector
        self.play(Create(context_vector), Write(context_label))
        
        flow_animations = []
        for i, h_state in enumerate(hidden_states):
            dot = Dot(color=BLUE).move_to(h_state.get_center())
            flow_animations.append(
                dot.animate.move_to(context_vector.get_center()).scale(weight_values[i]*5)
            )
        
        self.play(Create(ctx_to_dec))
        self.wait(0.8)
        self.wait(1)
        step4 = Text("Step 4: Combine with decoder state to predict output", font_size=20).to_edge(DOWN, buff=1.5)
        output_eq = MathTex(r"\tilde{s}_t = tanh(W_c[c_t;s_t])", font_size=24).next_to(step4, UP)
        self.play(Write(output_eq))
        self.wait(0.8)
        # Step 4: Combine with decoder state
        self.play(FadeOut(step3), FadeOut(context_eq))
        self.play(Write(step4))
        
        # Arrow from context to decoder
        ctx_to_dec = Arrow(context_vector.get_right(), current_state.get_left(), color=GREEN)
        self.play(Create(ctx_to_dec))
        
        self.play(section_title.animate.to_edge(UP))
        self.wait(0.8)
        
        self.wait(2)
        bahdanau_title = Text("Bahdanau (Additive) Attention", font_size=28).next_to(section_title, DOWN, buff=0.5)
        self.play(Write(bahdanau_title))
        self.wait(0.8)
        # Clear for next section
        section_title = Text("Types of Attention Mechanisms", font_size=36)
        section_title.to_edge(UP)
        
        # Part 3: Types of Attention
        section_title = Text("Types of Attention Mechanisms", font_size=36)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))
        
        # Bahdanau (Additive) Attention
        self.play(Write(bahdanau_title))
        
        bahdanau_eq = MathTex(
            r"e_{ij} = v_a^T \tanh(W_a s_{i-1} + U_a h_j)",
            font_size=28
        ).next_to(bahdanau_title, DOWN, buff=0.5)
        
        bahdanau_desc = Text(
            "Uses a small neural network to compute alignment scores",
            font_size=20
        ).next_to(bahdanau_eq, DOWN, buff=0.5)
        
        self.play(Write(bahdanau_eq), Write(bahdanau_desc))
        self.wait(2)
        
        # Luong (Dot-Product) Attention
        self.play(FadeOut(bahdanau_eq), FadeOut(bahdanau_desc), FadeOut(bahdanau_title))
        
        luong_title = Text("Luong (Dot-Product) Attention", font_size=28).next_to(section_title, DOWN, buff=0.5)
        self.play(Write(luong_title))
        
        # Create a VGroup for the equations
        luong_eqs = VGroup(
            MathTex(r"\text{Dot:} \quad e_{ij} = s_i^T h_j", font_size=28),
            MathTex(r"\text{General:} \quad e_{ij} = s_i^T W_a h_j", font_size=28),
            MathTex(r"\text{Concat:} \quad e_{ij} = v_a^T \tanh(W_a [s_i; h_j])", font_size=28)
        ).arrange(DOWN, buff=0.5).next_to(luong_title, DOWN, buff=0.5)
        
        luong_desc = Text(
            "Simpler scoring functions that are more computationally efficient",
            font_size=20
        ).next_to(luong_eqs, DOWN, buff=0.5)
        
        self.play(Write(luong_eqs), Write(luong_desc))
        self.wait(3)
        
        # Comparison
        self.play(
            FadeOut(luong_eqs), FadeOut(luong_desc), FadeOut(luong_title),
            FadeOut(section_title)
        )
        
        comparison_title = Text("Attention Mechanisms Comparison", font_size=36).to_edge(UP)
        self.play(Write(comparison_title))
        
        comparison_table = Table(
            [
                ["Bahdanau (Additive)", "Neural network", "More expressive", "Computationally expensive"],
                ["Luong (Dot-Product)", "Vector similarity", "Faster computation", "Simpler alignment"]
            ],
            row_labels=[Text("Type", font_size=20), Text("Type", font_size=20)],
            col_labels=[Text("Mechanism", font_size=20), Text("Scoring Function", font_size=20), 
                        Text("Advantage", font_size=20), Text("Characteristic", font_size=20)],
            include_outer_lines=True
        ).scale(0.6).next_to(comparison_title, DOWN, buff=0.5)
        
        self.play(Create(comparison_table))
        self.wait(3)
        
        # Conclusion
        self.play(FadeOut(comparison_table), FadeOut(comparison_title))
        
        conclusion_title = Text("Key Takeaways", font_size=36).to_edge(UP)
        self.play(Write(conclusion_title))
        
        takeaways = BulletedList(
            "Attention solves the bottleneck problem in encoder-decoder models",
            "Allows dynamic focus on relevant parts of the source sequence",
            "Different scoring functions offer trade-offs between expressivity and efficiency",
            "Foundation for modern transformer architectures",
            font_size=24,
            buff=0.3
        ).next_to(conclusion_title, DOWN, buff=0.5)
        
        self.play(Write(takeaways))
        self.wait(3)
        final_title = Text("Attention Mechanisms in NMT", font_size=40)
        final_title.to_edge(UP)
        # Final title
        self.play(FadeOut(takeaways), FadeOut(conclusion_title))
        
        final_title = Text("Attention Mechanisms in NMT", font_size=40)
        final_subtitle = Text("Foundation for Modern NLP", font_size=30).next_to(final_title, DOWN)
        
        self.play(Write(final_title), Write(final_subtitle))
        self.wait(3)
        
        self.play(FadeOut(final_title), FadeOut(final_subtitle))