from manim import *
import numpy as np


class TransformerArchitectureIntro(Scene):
    def construct(self):
        # Title and Introduction
        title = Text("Introduction to Transformers Architecture", font_size=48)
        subtitle = Text("From Encoder-Decoder to Attention-based Models", font_size=32)
        subtitle.next_to(title, DOWN)

        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))

        # Part 1: Vanilla Encoder-Decoder NMT
        section_title = Text("1. Vanilla Encoder-Decoder NMT", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))

        # Create encoder-decoder diagram
        encoder_rect = Rectangle(height=3, width=2, color=BLUE).shift(LEFT * 3)
        encoder_label = Text("Encoder", font_size=24).next_to(encoder_rect, UP)

        decoder_rect = Rectangle(height=3, width=2, color=GREEN).shift(RIGHT * 3)
        decoder_label = Text("Decoder", font_size=24).next_to(decoder_rect, UP)

        bottleneck = Rectangle(height=0.5, width=1, color=RED).move_to([0, 0, 0])
        bottleneck_label = Text("Fixed-size\nVector", font_size=20).next_to(
            bottleneck, DOWN
        )

        # Input and output text
        input_text = Text("Input Sequence", font_size=20).next_to(
            encoder_rect, DOWN, buff=0.5
        )
        output_text = Text("Output Sequence", font_size=20).next_to(
            decoder_rect, DOWN, buff=0.5
        )

        # Arrows
        arrow1 = Arrow(encoder_rect.get_right(), bottleneck.get_left(), color=WHITE)
        arrow2 = Arrow(bottleneck.get_right(), decoder_rect.get_left(), color=WHITE)

        # Display the basic encoder-decoder model
        self.play(
            Create(encoder_rect),
            Write(encoder_label),
            Create(decoder_rect),
            Write(decoder_label),
        )
        self.play(Write(input_text), Write(output_text))
        self.play(Create(arrow1), Create(bottleneck), Write(bottleneck_label))
        self.play(Create(arrow2))
        self.wait(2)

        # Highlight the bottleneck problem
        problem_text = Text(
            "Problem: Fixed-size bottleneck limits model capacity",
            font_size=24,
            color=RED,
        ).to_edge(DOWN)
        self.play(Write(problem_text))
        self.play(Indicate(bottleneck))
        self.wait(2)

        # Clear the scene
        self.play(*[FadeOut(obj) for obj in self.mobjects])

        # Part 2: Attention Mechanisms
        section_title = Text("2. Attention Mechanisms", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))

        # Create a more detailed encoder-decoder with attention
        encoder_rect = Rectangle(height=3, width=2, color=BLUE).shift(LEFT * 3.5)
        encoder_label = Text("Encoder", font_size=24).next_to(encoder_rect, UP)

        decoder_rect = Rectangle(height=3, width=2, color=GREEN).shift(RIGHT * 3.5)
        decoder_label = Text("Decoder", font_size=24).next_to(decoder_rect, UP)

        # Encoder hidden states
        encoder_states = VGroup()
        for i in range(5):
            state = Circle(radius=0.2, color=BLUE_E, fill_opacity=0.8)
            state.move_to(encoder_rect.get_center() + UP * (1 - i * 0.5))
            encoder_states.add(state)

        # Decoder state
        decoder_state = Circle(radius=0.2, color=GREEN_E, fill_opacity=0.8)
        decoder_state.move_to(decoder_rect.get_center() + UP * 1)

        # Attention mechanism
        attention_rect = Rectangle(height=2, width=3, color=YELLOW).move_to([0, 0, 0])
        attention_label = Text("Attention", font_size=24).next_to(attention_rect, UP)

        # Arrows
        encoder_to_attention_arrows = VGroup()
        for state in encoder_states:
            arrow = Arrow(
                state.get_right(),
                attention_rect.get_left()
                + UP * (state.get_center()[1] - attention_rect.get_center()[1]),
                color=WHITE,
                buff=0.1,
            )
            encoder_to_attention_arrows.add(arrow)

        decoder_to_attention_arrow = Arrow(
            decoder_state.get_left(),
            attention_rect.get_right()
            + UP * (decoder_state.get_center()[1] - attention_rect.get_center()[1]),
            color=WHITE,
            buff=0.1,
        )

        attention_to_decoder_arrow = Arrow(
            attention_rect.get_right(), decoder_rect.get_left(), color=WHITE, buff=0.1
        )

        # Display the attention-based model
        self.play(
            Create(encoder_rect),
            Write(encoder_label),
            Create(decoder_rect),
            Write(decoder_label),
        )
        self.play(Create(VGroup(*encoder_states)), Create(decoder_state))
        self.play(Create(attention_rect), Write(attention_label))
        self.play(
            Create(VGroup(*encoder_to_attention_arrows)),
            Create(decoder_to_attention_arrow),
        )
        self.play(Create(attention_to_decoder_arrow))

        # Explanation text
        explanation = Text(
            "Attention allows the decoder to focus on\nrelevant parts of the input sequence",
            font_size=24,
        ).to_edge(DOWN)
        self.play(Write(explanation))
        self.wait(2)

        # Clear for next section
        self.play(*[FadeOut(obj) for obj in self.mobjects])

        # Part 3: Bahdanau (Additive) Attention
        section_title = Text("3. Bahdanau (Additive) Attention", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))

        # Mathematical formulation
        bahdanau_eq = MathTex(
            r"\text{score}(h_t, \bar{h}_i) = v_a^T \tanh(W_a [h_t; \bar{h}_i])",
            font_size=36,
        )
        self.play(Write(bahdanau_eq))
        self.wait(2)

        # Explanation of variables
        explanation = (
            VGroup(
                Text("Where:", font_size=24),
                MathTex(r"h_t = \text{decoder hidden state at time } t", font_size=28),
                MathTex(
                    r"\bar{h}_i = \text{encoder hidden state at position } i",
                    font_size=28,
                ),
                MathTex(r"W_a, v_a = \text{learnable parameters}", font_size=28),
            )
            .arrange(DOWN, aligned_edge=LEFT)
            .next_to(bahdanau_eq, DOWN, buff=0.5)
        )

        self.play(Write(explanation))
        self.wait(2)

        # Attention weights calculation
        attention_weights_eq = MathTex(
            r"\alpha_{t,i} = \frac{\exp(\text{score}(h_t, \bar{h}_i))}{\sum_{j=1}^{T_x} \exp(\text{score}(h_t, \bar{h}_j))}",
            font_size=36,
        ).next_to(explanation, DOWN, buff=0.5)

        self.play(Write(attention_weights_eq))
        self.wait(2)

        # Context vector calculation
        context_vector_eq = MathTex(
            r"c_t = \sum_{i=1}^{T_x} \alpha_{t,i} \bar{h}_i", font_size=36
        ).next_to(attention_weights_eq, DOWN, buff=0.5)

        self.play(Write(context_vector_eq))
        self.wait(2)

        # Clear for next section
        self.play(*[FadeOut(obj) for obj in self.mobjects])

        # Part 4: Luong (Dot-Product) Attention
        section_title = Text("4. Luong (Dot-Product) Attention", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))

        # Mathematical formulation
        dot_product_eq = MathTex(
            r"\text{score}(h_t, \bar{h}_i) = h_t^T \bar{h}_i", font_size=36
        )
        self.play(Write(dot_product_eq))
        self.wait(2)

        # General attention
        general_eq = MathTex(
            r"\text{score}(h_t, \bar{h}_i) = h_t^T W_a \bar{h}_i", font_size=36
        ).next_to(dot_product_eq, DOWN, buff=0.5)

        general_label = Text("General Attention", font_size=24, color=YELLOW).next_to(
            general_eq, RIGHT
        )

        self.play(Write(general_eq), Write(general_label))
        self.wait(2)

        # Comparison with Bahdanau
        comparison = Text(
            "Luong attention is computationally simpler\nthan Bahdanau attention",
            font_size=24,
        ).next_to(general_eq, DOWN, buff=0.5)

        self.play(Write(comparison))
        self.wait(2)

        # Clear for next section
        self.play(*[FadeOut(obj) for obj in self.mobjects])

        # Part 5: Self-Attention
        section_title = Text("5. Self-Attention", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))

        # Self-attention explanation
        explanation = Text(
            "Self-attention allows a sequence to attend to itself,\ncapturing dependencies between different positions",
            font_size=24,
        )
        self.play(Write(explanation))
        self.wait(2)

        # Self-attention diagram
        self.play(explanation.animate.to_edge(UP).scale(0.8))

        # Create sequence of tokens
        tokens = VGroup()
        token_labels = ["The", "cat", "sat", "on", "the", "mat"]
        for i, label in enumerate(token_labels):
            token = Square(side_length=0.8, color=BLUE).shift(LEFT * 5 + RIGHT * 2 * i)
            token_text = Text(label, font_size=20).move_to(token.get_center())
            tokens.add(VGroup(token, token_text))

        self.play(Create(tokens))
        self.wait(1)

        # Show self-attention connections for "cat"
        connections = VGroup()
        focus_token = tokens[1]  # "cat"

        # Highlight the focus token
        self.play(focus_token[0].animate.set_color(YELLOW))

        # Create connections with varying opacity based on attention strength
        attention_strengths = [0.1, 1.0, 0.7, 0.2, 0.1, 0.3]  # Example values
        for i, token in enumerate(tokens):
            if i != 1:  # Skip self-connection for clarity
                line = Line(
                    focus_token.get_center(),
                    token.get_center(),
                    color=YELLOW,
                    stroke_opacity=attention_strengths[i],
                )
                connections.add(line)

        self.play(Create(connections))
        self.wait(2)

        # Self-attention formula
        self.play(
            *[FadeOut(obj) for obj in [tokens, connections]],
            explanation.animate.to_edge(UP),
        )

        self_attention_eq = MathTex(
            r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V",
            font_size=36,
        )
        self.play(Write(self_attention_eq))
        self.wait(2)

        # Explanation of Q, K, V
        qkv_explanation = (
            VGroup(
                Text("Where:", font_size=24),
                MathTex(r"Q = \text{Query matrix}", font_size=28),
                MathTex(r"K = \text{Key matrix}", font_size=28),
                MathTex(r"V = \text{Value matrix}", font_size=28),
                MathTex(r"d_k = \text{Dimension of keys}", font_size=28),
            )
            .arrange(DOWN, aligned_edge=LEFT)
            .next_to(self_attention_eq, DOWN, buff=0.5)
        )

        self.play(Write(qkv_explanation))
        self.wait(2)

        # Clear for next section
        self.play(*[FadeOut(obj) for obj in self.mobjects])

        # Part 6: Multi-Head Attention
        section_title = Text("6. Multi-Head Attention", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))

        # Multi-head attention explanation
        explanation = Text(
            "Multi-head attention runs multiple attention operations in parallel,\nallowing the model to focus on different aspects of the input",
            font_size=24,
        ).next_to(section_title, DOWN)
        self.play(Write(explanation))
        self.wait(2)

        # Multi-head attention diagram
        self.play(explanation.animate.scale(0.8).to_edge(UP))

        # Create attention heads
        heads = VGroup()
        for i in range(4):
            head = Rectangle(height=1.5, width=2, color=BLUE).shift(
                UP * 1 + LEFT * 4 + RIGHT * 2.5 * i
            )
            head_label = Text(f"Head {i+1}", font_size=20).move_to(head.get_center())
            heads.add(VGroup(head, head_label))

        self.play(Create(heads))

        # Concatenation box
        concat = Rectangle(height=1, width=3, color=GREEN).shift(DOWN * 1)
        concat_label = Text("Concatenate", font_size=20).move_to(concat.get_center())

        # Linear projection
        projection = Rectangle(height=1, width=3, color=RED).shift(DOWN * 3)
        projection_label = Text("Linear Projection", font_size=20).move_to(
            projection.get_center()
        )

        # Arrows from heads to concat
        head_arrows = VGroup()
        for i, head in enumerate(heads):
            arrow = Arrow(
                head.get_bottom(),
                concat.get_top() + LEFT * 1.5 + RIGHT * i,
                color=WHITE,
                buff=0.1,
            )
            head_arrows.add(arrow)

        # Arrow from concat to projection
        concat_arrow = Arrow(
            concat.get_bottom(), projection.get_top(), color=WHITE, buff=0.1
        )

        # Animate the flow
        self.play(Create(concat), Write(concat_label))
        self.play(Create(head_arrows))
        self.play(Create(projection), Write(projection_label))
        self.play(Create(concat_arrow))
        self.wait(2)

        # Multi-head attention formula
        self.play(
            *[
                FadeOut(obj)
                for obj in [
                    heads,
                    head_arrows,
                    concat,
                    concat_label,
                    concat_arrow,
                    projection,
                    projection_label,
                ]
            ]
        )

        multihead_eq = MathTex(
            r"\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O",
            font_size=36,
        )
        self.play(Write(multihead_eq))
        self.wait(1)

        head_eq = MathTex(
            r"\text{where head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)",
            font_size=36,
        ).next_to(multihead_eq, DOWN, buff=0.5)

        self.play(Write(head_eq))
        self.wait(2)

        # Clear for next section
        self.play(*[FadeOut(obj) for obj in self.mobjects])

        # Part 7: Full Transformer Architecture
        section_title = Text("7. Full Transformer Architecture", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))

        # Create a simplified transformer diagram
        # Encoder stack
        encoder_stack = Rectangle(height=4, width=2.5, color=BLUE).shift(LEFT * 3)
        encoder_label = Text("Encoder Stack", font_size=24).next_to(encoder_stack, UP)

        # Decoder stack
        decoder_stack = Rectangle(height=4, width=2.5, color=GREEN).shift(RIGHT * 3)
        decoder_label = Text("Decoder Stack", font_size=24).next_to(decoder_stack, UP)

        # Components inside encoder
        enc_components = (
            VGroup(
                Text("Self-Attention", font_size=18),
                Text("Feed Forward", font_size=18),
                Text("+ Residual Connections", font_size=18),
                Text("+ Layer Normalization", font_size=18),
            )
            .arrange(DOWN, buff=0.2)
            .scale(0.8)
            .move_to(encoder_stack.get_center())
        )

        # Components inside decoder
        dec_components = (
            VGroup(
                Text("Masked Self-Attention", font_size=18),
                Text("Encoder-Decoder Attention", font_size=18),
                Text("Feed Forward", font_size=18),
                Text("+ Residual Connections", font_size=18),
                Text("+ Layer Normalization", font_size=18),
            )
            .arrange(DOWN, buff=0.2)
            .scale(0.8)
            .move_to(decoder_stack.get_center())
        )

        # Input and output
        input_text = Text("Input + Positional Encoding", font_size=20).next_to(
            encoder_stack, DOWN, buff=0.5
        )
        output_text = Text("Output Probabilities", font_size=20).next_to(
            decoder_stack, DOWN, buff=0.5
        )

        # Arrow from encoder to decoder
        encoder_to_decoder = Arrow(
            encoder_stack.get_right(), decoder_stack.get_left(), color=WHITE
        )

        # Display the transformer architecture
        self.play(
            Create(encoder_stack),
            Write(encoder_label),
            Create(decoder_stack),
            Write(decoder_label),
        )
        self.play(Write(enc_components), Write(dec_components))
        self.play(Write(input_text), Write(output_text))
        self.play(Create(encoder_to_decoder))
        self.wait(2)

        # Key advantages
        advantages = (
            VGroup(
                Text("Key Advantages:", font_size=28, color=YELLOW),
                Text("• Parallelizable (no recurrence)", font_size=24),
                Text("• Captures long-range dependencies", font_size=24),
                Text("• Scales to longer sequences", font_size=24),
                Text("• State-of-the-art performance", font_size=24),
            )
            .arrange(DOWN, aligned_edge=LEFT)
            .to_edge(DOWN)
        )

        self.play(Write(advantages))
        self.wait(3)

        # Conclusion
        self.play(*[FadeOut(obj) for obj in self.mobjects])

        conclusion = Text(
            "Transformers have revolutionized NLP and beyond,\nserving as the foundation for models like BERT, GPT, and T5",
            font_size=32,
        )
        self.play(Write(conclusion))
        self.wait(2)

        final_title = Text("Thank you!", font_size=48, color=YELLOW)
        self.play(ReplacementTransform(conclusion, final_title))
        self.wait(3)
