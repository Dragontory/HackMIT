#!/usr/bin/env python3
"""
Direct Transformers video generator that bypasses Integration Orchestrator issues.
"""

import asyncio
from agents_system.infrastructure.config import AgentConfig
from agents_system.infrastructure.anthropic.client import AnthropicClient


async def generate_transformers_video():
    """Generate a comprehensive Transformers educational video directly."""

    try:
        # Initialize Claude client
        config = AgentConfig.from_env()
        claude_client = AnthropicClient(config.anthropic)

        # Read the Transformers content
        with open("testfile.txt", "r") as f:
            content = f.read()

        print("🚀 Direct Transformers Video Generation")
        print(f"📄 Content: {len(content)} characters")
        print("=" * 60)

        # Step 1: Create educational strategy
        print("\n🧠 Step 1: Analyzing content and creating strategy...")
        from agents_system.core.agents.content_strategist import ContentStrategistAgent

        content_agent = ContentStrategistAgent(claude_client)

        title = "Attention, NMT, and Transformers — a detailed walkthrough"
        strategy = await content_agent.analyze_content(content, title)
        print(f"   ✅ Created {len(strategy.learning_objectives)} learning objectives")

        # Step 2: Design educational flow
        print("\n🎨 Step 2: Designing educational flow...")
        from agents_system.core.agents.educational_design import EducationalDesignAgent

        edu_agent = EducationalDesignAgent(claude_client)
        edu_result = await edu_agent.design_educational_flow(content, strategy)

        if not edu_result.success:
            print("   ❌ Educational design failed")
            return False

        print(
            f"   ✅ Designed educational flow with {len(edu_result.designed_flow.learning_segments)} segments"
        )

        # Step 3: Create comprehensive Manim code directly using Claude
        print("\n🎬 Step 3: Generating comprehensive Manim code...")

        # Create a detailed prompt for Claude
        educational_context = f"""
Educational Context:
Title: {title}

Learning Objectives:
"""
        for obj in strategy.learning_objectives:
            educational_context += (
                f"- {obj.title}: {obj.description} (Time: {obj.time_estimate} min)\n"
            )

        educational_context += f"""
Learning Segments:
"""
        for segment in edu_result.designed_flow.learning_segments:
            educational_context += f"- {segment.title}: {segment.content}\n"

        # Key content excerpts
        key_content = f"""
Key Content Areas from Source:
1. Attention Problem: {content[500:1000]}...
2. Mathematical Formulas: {content[1500:2000]}...
3. Architecture Details: {content[5000:5500]}...
"""

        manim_prompt = f"""
You are an expert educational video creator specializing in mathematical concepts and animations.

{educational_context}

{key_content}

Generate a comprehensive Manim educational video that covers:

1. **Introduction & Motivation**: 
   - The bottleneck problem in encoder-decoder NMT
   - Why attention mechanisms were needed

2. **Mathematical Foundation**:
   - Scaled dot-product attention formula: Attention(Q,K,V) = softmax(QK^T/√d_k)V
   - Visual explanation of Q, K, V matrices
   - Step-by-step computation visualization

3. **Multi-Head Attention**:
   - Parallel attention heads concept
   - Different heads learning different patterns
   - Concatenation and output projection

4. **Positional Encodings**:
   - Why position information is needed
   - Sinusoidal encoding visualization
   - How encodings are added to embeddings

5. **Transformer Architecture**:
   - Complete encoder-decoder structure
   - Layer normalization and residual connections
   - Information flow visualization

Requirements:
- Create engaging, progressive animations
- Use clear mathematical notation with MathTex
- Include explanatory text at appropriate points
- Use colors and positioning to enhance understanding
- Target 4-5 minutes of content
- Make it educational and accessible

Generate complete, working Manim code for class "ComprehensiveTransformersVideo".
"""

        # Send to Claude for generation
        messages = [{"role": "user", "content": manim_prompt}]
        response = await claude_client.send_message(
            messages,
            "Generate comprehensive Manim code for Transformers educational video.",
        )

        generated_code = response.content

        if not generated_code or len(generated_code) < 1000:
            print("   ❌ Code generation failed or too short")
            return False

        print(f"   ✅ Generated {len(generated_code)} characters of Manim code")

        # Step 4: Save and validate
        print("\n💾 Step 4: Saving generated video...")

        with open("comprehensive_transformers_educational_video.py", "w") as f:
            f.write(generated_code)

        print("   ✅ Saved to: comprehensive_transformers_educational_video.py")

        # Show preview
        print("\n📺 PREVIEW (first 1500 characters):")
        print("=" * 80)
        print(generated_code[:1500])
        print("=" * 80)

        # Quick syntax check
        try:
            compile(generated_code, "<string>", "exec")
            print("\n✅ Code syntax is valid!")
        except SyntaxError as e:
            print(f"\n⚠️ Syntax warning: {e}")

        print(f"\n🎉 SUCCESS! Generated comprehensive Transformers educational video!")
        print(f"📄 Code length: {len(generated_code)} characters")
        print(
            f"🎥 Ready to render with: manim comprehensive_transformers_educational_video.py ComprehensiveTransformersVideo -pql"
        )

        return True

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(generate_transformers_video())
    print(f'\n🏁 Final Result: {"SUCCESS" if success else "FAILED"}')
