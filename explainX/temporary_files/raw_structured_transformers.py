from manim import *
import numpy as np

class TransformerAttentionMechanisms(Scene):
    def construct(self):
        # Title and Introduction
        title = Text("Transformers and Attention Mechanisms", font_size=48)
        subtitle = Text("From Encoder-Decoder to Modern Transformers", font_size=32)
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
        
        # Create encoder-decoder architecture
        encoder_rect = Rectangle(height=3, width=1.5, color=BLUE)
        encoder_label = Text("Encoder", font_size=24).next_to(encoder_rect, UP)
        encoder_group = VGroup(encoder_rect, encoder_label).move_to(LEFT * 3)
        
        decoder_rect = Rectangle(height=3, width=1.5, color=GREEN)
        decoder_label = Text("Decoder", font_size=24).next_to(decoder_rect, UP)
        decoder_group = VGroup(decoder_rect, decoder_label).move_to(RIGHT * 3)
        
        # Input and output text
        input_text = Text("Input: 'Bonjour le monde'", font_size=20).next_to(encoder_group, DOWN, buff=0.5)
        output_text = Text("Output: 'Hello world'", font_size=20).next_to(decoder_group, DOWN, buff=0.5)
        
        # Context vector
        context_circle = Circle(radius=0.5, color=YELLOW).move_to(ORIGIN)
        context_label = Text("Context\nVector", font_size=16).next_to(context_circle, DOWN, buff=0.2)
        context_group = VGroup(context_circle, context_label)
        
        # Arrows
        arrow1 = Arrow(encoder_rect.get_right(), context_circle.get_left(), color=WHITE)
        arrow2 = Arrow(context_circle.get_right(), decoder_rect.get_left(), color=WHITE)
        
        # Display the basic architecture
        self.play(Create(encoder_group), Create(decoder_group))
        self.play(Write(input_text), Write(output_text))
        self.play(Create(context_group), Create(arrow1), Create(arrow2))
        self.wait(2)
        
        # Explain the bottleneck problem
        bottleneck_text = Text("Bottleneck Problem:", color=RED, font_size=24).to_edge(DOWN, buff=1.5)
        bottleneck_detail = Text("A single fixed-size vector must encode all information", font_size=20)
        bottleneck_detail.next_to(bottleneck_text, DOWN)
        
        self.play(Write(bottleneck_text))
        self.play(Write(bottleneck_detail))
        self.wait(2)
        
        # Clear the scene for the next part
        self.play(
            FadeOut(encoder_group), FadeOut(decoder_group),
            FadeOut(input_text), FadeOut(output_text),
            FadeOut(context_group), FadeOut(arrow1), FadeOut(arrow2),
            FadeOut(bottleneck_text), FadeOut(bottleneck_detail),
            FadeOut(section_title)
        )
        
        # Part 2: Attention Mechanisms
        section_title = Text("2. Attention Mechanisms", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))
        
        # Create a more detailed encoder-decoder with attention
        # Encoder hidden states
        encoder_states = VGroup()
        for i in range(5):
            state = Square(side_length=0.5, color=BLUE)
            state.move_to(LEFT * 4 + UP * (1 - i))
            encoder_states.add(state)
        
        encoder_label = Text("Encoder\nHidden States", font_size=20).next_to(encoder_states, UP)
        
        # Decoder state
        decoder_state = Square(side_length=0.5, color=GREEN).move_to(RIGHT * 4)
        decoder_label = Text("Decoder\nState at t", font_size=20).next_to(decoder_state, UP)
        
        # Display encoder and decoder states
        self.play(Create(encoder_states), Write(encoder_label))
        self.play(Create(decoder_state), Write(decoder_label))
        self.wait(1)
        
        # Attention mechanism explanation
        attention_title = Text("Attention Mechanism", font_size=28).move_to(UP * 2)
        attention_desc = Text("Allows decoder to focus on relevant parts of the input", font_size=20)
        attention_desc.next_to(attention_title, DOWN)
        
        self.play(Write(attention_title), Write(attention_desc))
        self.wait(2)
        
        # Visualize attention scores and weights
        score_arrows = VGroup()
        for i, state in enumerate(encoder_states):
            arrow = Arrow(decoder_state.get_left(), state.get_right(), color=YELLOW, buff=0.1)
            score_arrows.add(arrow)
        
        score_label = Text("Compute\nScores", font_size=16).move_to(ORIGIN)
        
        self.play(Create(score_arrows), Write(score_label))
        self.wait(1)
        
        # Show attention weights with varying opacity
        weights = [0.1, 0.15, 0.5, 0.15, 0.1]  # Example weights
        weight_labels = VGroup()
        
        for i, (state, weight) in enumerate(zip(encoder_states, weights)):
            weight_text = MathTex(f"\\alpha_{{{i+1}}} = {weight}", font_size=24)
            weight_text.next_to(state, RIGHT)
            weight_labels.add(weight_text)
            
            # Adjust arrow opacity based on weight
            self.play(score_arrows[i].animate.set_opacity(weight * 2), run_time=0.3)
        
        self.play(Write(weight_labels))
        self.wait(2)
        
        # Context vector as weighted sum
        context_eq = MathTex(r"c_t = \sum_{i} \alpha_i h_i", font_size=32).move_to(DOWN * 2)
        context_desc = Text("Context vector is a weighted sum of encoder states", font_size=20)
        context_desc.next_to(context_eq, DOWN)
        
        self.play(Write(context_eq), Write(context_desc))
        self.wait(2)
        
        # Clear for next section
        self.play(
            FadeOut(encoder_states), FadeOut(encoder_label),
            FadeOut(decoder_state), FadeOut(decoder_label),
            FadeOut(attention_title), FadeOut(attention_desc),
            FadeOut(score_arrows), FadeOut(score_label),
            FadeOut(weight_labels), FadeOut(context_eq),
            FadeOut(context_desc), FadeOut(section_title)
        )
        
        # Part 3: Types of Attention
        section_title = Text("3. Types of Attention", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))
        
        # Bahdanau (Additive) Attention
        bahdanau_title = Text("Bahdanau (Additive) Attention", font_size=32).move_to(UP * 2)
        self.play(Write(bahdanau_title))
        
        bahdanau_eq = MathTex(
            r"score(h_t, \bar{h}_i) = v_a^T \tanh(W_a [h_t; \bar{h}_i])",
            font_size=28
        ).move_to(UP * 0.5)
        
        bahdanau_desc = Text(
            "Uses a small neural network to compute alignment scores",
            font_size=20
        ).next_to(bahdanau_eq, DOWN)
        
        self.play(Write(bahdanau_eq), Write(bahdanau_desc))
        self.wait(2)
        
        # Luong (Dot-Product) Attention
        luong_title = Text("Luong (Dot-Product) Attention", font_size=32).move_to(DOWN * 1)
        self.play(Write(luong_title))
        
        luong_eq = MathTex(
            r"score(h_t, \bar{h}_i) = h_t^T \bar{h}_i",
            font_size=28
        ).next_to(luong_title, DOWN, buff=0.5)
        
        luong_desc = Text(
            "Simpler scoring using dot product between states",
            font_size=20
        ).next_to(luong_eq, DOWN)
        
        self.play(Write(luong_eq), Write(luong_desc))
        self.wait(2)
        
        # General Attention
        general_title = Text("General Attention", font_size=32).move_to(DOWN * 3)
        general_eq = MathTex(
            r"score(h_t, \bar{h}_i) = h_t^T W_a \bar{h}_i",
            font_size=28
        ).next_to(general_title, DOWN, buff=0.5)
        
        self.play(Write(general_title), Write(general_eq))
        self.wait(2)
        
        # Clear for next section
        self.play(
            FadeOut(bahdanau_title), FadeOut(bahdanau_eq), FadeOut(bahdanau_desc),
            FadeOut(luong_title), FadeOut(luong_eq), FadeOut(luong_desc),
            FadeOut(general_title), FadeOut(general_eq), FadeOut(section_title)
        )
        
        # Part 4: Self-Attention and Transformers
        section_title = Text("4. Self-Attention & Transformers", font_size=40)
        self.play(Write(section_title))
        self.wait(1)
        self.play(section_title.animate.to_edge(UP))
        
        # Self-Attention explanation
        self_attn_title = Text("Self-Attention", font_size=32).move_to(UP * 2)
        self.play(Write(self_attn_title))
        
        self_attn_desc = Text(
            "Each position attends to all positions in the same sequence",
            font_size=20
        ).next_to(self_attn_title, DOWN)
        
        self.play(Write(self_attn_desc))
        self.wait(1)
        
        # QKV explanation
        qkv_title = Text("Query, Key, Value Projections", font_size=28).move_to(UP * 0.5)
        self.play(Write(qkv_title))
        
        # Create QKV equations
        qkv_eqs = VGroup(
            MathTex(r"Q = X W^Q", font_size=24),
            MathTex(r"K = X W^K", font_size=24),
            MathTex(r"V = X W^V", font_size=24)
        ).arrange(DOWN, buff=0.3).next_to(qkv_title, DOWN)
        
        self.play(Write(qkv_eqs))
        self.wait(1)
        
        # Self-attention formula
        attn_formula = MathTex(
            r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V",
            font_size=28
        ).move_to(DOWN * 1)
        
        self.play(Write(attn_formula))
        self.wait(2)
        
        # Multi-head attention
        multihead_title = Text("Multi-Head Attention", font_size=28).move_to(DOWN * 2)
        self.play(Write(multihead_title))
        
        multihead_desc = Text(
            "Run multiple attention operations in parallel, then concatenate",
            font_size=20
        ).next_to(multihead_title, DOWN)
        
        self.play(Write(multihead_desc))
        self.wait(2)
        
        # Clear for final transformer architecture
        self.play(
            FadeOut(self_attn_title), FadeOut(self_attn_desc),
            FadeOut(qkv_title), FadeOut(qkv_eqs),
            FadeOut(attn_formula), FadeOut(multihead_title),
            FadeOut(multihead_desc), FadeOut(section_title)
        )
        
        # Part 5: Full Transformer Architecture
        final_title = Text("The Transformer Architecture", font_size=40)
        self.play(Write(final_title))
        self.wait(1)
        self.play(final_title.animate.to_edge(UP))
        
        # Create a simplified transformer architecture diagram
        # Encoder stack
        encoder_block = Rectangle(height=4, width=2, color=BLUE)
        encoder_label = Text("Encoder", font_size=24).next_to(encoder_block, UP)
        
        # Add internal components to encoder
        self_attn_box = Rectangle(height=1, width=1.8, color=YELLOW).move_to(encoder_block.get_top() + DOWN * 0.7)
        self_attn_text = Text("Self-Attention", font_size=14).move_to(self_attn_box)
        
        norm1 = Rectangle(height=0.4, width=1.8, color=GREEN).next_to(self_attn_box, DOWN, buff=0.2)
        norm1_text = Text("Add & Norm", font_size=14).move_to(norm1)
        
        ffn = Rectangle(height=1, width=1.8, color=YELLOW).next_to(norm1, DOWN, buff=0.2)
        ffn_text = Text("Feed Forward", font_size=14).move_to(ffn)
        
        norm2 = Rectangle(height=0.4, width=1.8, color=GREEN).next_to(ffn, DOWN, buff=0.2)
        norm2_text = Text("Add & Norm", font_size=14).move_to(norm2)
        
        encoder_components = VGroup(self_attn_box, self_attn_text, norm1, norm1_text, ffn, ffn_text, norm2, norm2_text)
        encoder_group = VGroup(encoder_block, encoder_label, encoder_components).move_to(LEFT * 3)
        
        # Decoder stack
        decoder_block = Rectangle(height=4, width=2, color=RED)
        decoder_label = Text("Decoder", font_size=24).next_to(decoder_block, UP)
        
        # Add internal components to decoder
        masked_attn_box = Rectangle(height=0.8, width=1.8, color=YELLOW).move_to(decoder_block.get_top() + DOWN * 0.6)
        masked_attn_text = Text("Masked\nSelf-Attention", font_size=12).move_to(masked_attn_box)
        
        d_norm1 = Rectangle(height=0.3, width=1.8, color=GREEN).next_to(masked_attn_box, DOWN, buff=0.1)
        d_norm1_text = Text("Add & Norm", font_size=12).move_to(d_norm1)
        
        cross_attn_box = Rectangle(height=0.8, width=1.8, color=YELLOW).next_to(d_norm1, DOWN, buff=0.1)
        cross_attn_text = Text("Cross-Attention", font_size=12).move_to(cross_attn_box)
        
        d_norm2 = Rectangle(height=0.3, width=1.8, color=GREEN).next_to(cross_attn_box, DOWN, buff=0.1)
        d_norm2_text = Text("Add & Norm", font_size=12).move_to(d_norm2)
        
        d_ffn = Rectangle(height=0.8, width=1.8, color=YELLOW).next_to(d_norm2, DOWN, buff=0.1)
        d_ffn_text = Text("Feed Forward", font_size=12).move_to(d_ffn)
        
        d_norm3 = Rectangle(height=0.3, width=1.8, color=GREEN).next_to(d_ffn, DOWN, buff=0.1)
        d_norm3_text = Text("Add & Norm", font_size=12).move_to(d_norm3)
        
        decoder_components = VGroup(masked_attn_box, masked_attn_text, d_norm1, d_norm1_text, 
                                    cross_attn_box, cross_attn_text, d_norm2, d_norm2_text,
                                    d_ffn, d_ffn_text, d_norm3, d_norm3_text)
        decoder_group = VGroup(decoder_block, decoder_label, decoder_components).move_to(RIGHT * 3)
        
        # Arrows connecting encoder and decoder
        connection_arrow = Arrow(encoder_block.get_right(), cross_attn_box.get_left(), color=WHITE)
        
        # Input and output embeddings
        input_embed = Rectangle(height=0.5, width=2, color=BLUE_E).next_to(encoder_block, DOWN, buff=0.3)
        input_text = Text("Input Embeddings + Positional Encoding", font_size=14).next_to(input_embed, DOWN)
        
        output_embed = Rectangle(height=0.5, width=2, color=RED_E).next_to(decoder_block, DOWN, buff=0.3)
        output_text = Text("Output Embeddings + Positional Encoding", font_size=14).next_to(output_embed, DOWN)
        
        # Display the transformer architecture
        self.play(Create(encoder_block), Write(encoder_label))
        self.play(Create(decoder_block), Write(decoder_label))
        self.play(Create(encoder_components), Create(decoder_components))
        self.play(Create(connection_arrow))
        self.play(Create(input_embed), Write(input_text))
        self.play(Create(output_embed), Write(output_text))
        
        self.wait(3)
        
        # Final summary
        self.play(
            FadeOut(encoder_group), FadeOut(decoder_group),
            FadeOut(connection_arrow), FadeOut(input_embed),
            FadeOut(input_text), FadeOut(output_embed),
            FadeOut(output_text), FadeOut(final_title)
        )
        
        summary_title = Text("Key Takeaways", font_size=40)
        self.play(Write(summary_title))
        self.wait(1)
        self.play(summary_title.animate.to_edge(UP))
        
        # Create bullet points for key takeaways
        bullet_points = VGroup(
            Text("• Attention solves the bottleneck problem in sequence models", font_size=24),
            Text("• Different attention mechanisms: Bahdanau, Luong, Self-Attention", font_size=24),
            Text("• Transformers use self-attention and multi-head attention", font_size=24),
            Text("• Parallel computation enables efficient training", font_size=24),
            Text("• Foundation for modern NLP models like BERT, GPT, etc.", font_size=24)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to(ORIGIN)
        
        for bullet in bullet_points:
            self.play(Write(bullet))
            self.wait(0.5)
        
        self.wait(3)
        
        # Final fade out
        self.play(FadeOut(summary_title), FadeOut(bullet_points))
        
        # End credits
        thank_you = Text("Thank you for watching!", font_size=48)
        self.play(Write(thank_you))
        self.wait(2)
        self.play(FadeOut(thank_you))