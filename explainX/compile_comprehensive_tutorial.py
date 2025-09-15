#!/usr/bin/env python3
"""
Compile the comprehensive Transformer tutorial using GPU Modal
Renders all scenes with audio narration and combines them into a final video
"""

import asyncio
import base64
from pathlib import Path
import modal
import time


async def compile_comprehensive_tutorial():
    """Compile the comprehensive Transformer tutorial with GPU acceleration"""

    print("🎬 Compiling Comprehensive Transformer Tutorial with GPU Modal")
    print("=" * 70)

    # Import Modal functions
    from modal_gpu_manim import (
        gpu_render_manim_video,
        generate_educational_audio,
        combine_video_with_audio,
    )

    # Read the comprehensive tutorial code
    tutorial_path = Path("comprehensive_transformer_tutorial.py")
    if not tutorial_path.exists():
        print(f"❌ Tutorial file not found: {tutorial_path}")
        return

    with open(tutorial_path, "r") as f:
        tutorial_code = f.read()

    print(f"📖 Loaded tutorial code: {len(tutorial_code)} characters")
    print(f"🎯 Target scene: ComprehensiveTransformerTutorial")

    # Phase 1: Generate educational audio narration
    print("\n🎙️ Phase 1: Generating Educational Audio...")

    comprehensive_narration = """
    Welcome to our comprehensive exploration of "Attention Is All You Need" - 
    the groundbreaking paper that revolutionized artificial intelligence.
    
    Published in 2017 by Vaswani and colleagues at Google, this paper introduced 
    the Transformer architecture... an elegant solution that would become the 
    foundation for GPT, BERT, and virtually every modern language model.
    
    Today, we'll journey through the mathematical foundations, explore how 
    attention mechanisms work, understand multi-head attention, and see why 
    this architecture sparked the AI revolution we see today.
    
    From the problems with sequential models to the elegant solutions of 
    self-attention, from positional encoding to the complete encoder-decoder 
    architecture - we'll cover it all with detailed visualizations and 
    step-by-step explanations.
    
    This comprehensive tutorial will give you a deep understanding of the 
    Transformer's inner workings and why attention truly is all you need.
    
    Let's begin our journey into the architecture that changed everything.
    """

    start_time = time.time()

    try:
        audio_result = await generate_educational_audio.remote.aio(
            scene_name="comprehensive_transformer_tutorial",
            narration_text=comprehensive_narration,
            voice="coral",
        )

        if audio_result["success"]:
            print(f"✅ Audio generated in {time.time() - start_time:.1f}s")
            print(f"📏 Audio size: {audio_result['file_size'] / 1024:.1f} KB")
            audio_data = audio_result["audio_data"]
        else:
            print(f"⚠️ Audio generation failed: {audio_result.get('error')}")
            audio_data = None

    except Exception as e:
        print(f"⚠️ Audio generation error: {e}")
        audio_data = None

    # Phase 2: GPU render the comprehensive tutorial
    print(f"\n🎬 Phase 2: GPU Rendering Comprehensive Tutorial...")

    video_start = time.time()

    try:
        # Render the main comprehensive scene
        video_result = await gpu_render_manim_video.remote.aio(
            manim_code=tutorial_code, scene_name="ComprehensiveTransformerTutorial"
        )

        if video_result["success"]:
            print(f"✅ Video rendered in {time.time() - video_start:.1f}s")
            print(f"📹 Video file: {video_result['filename']}")
            print(f"📏 Video size: {video_result['file_size'] / (1024*1024):.2f} MB")
            video_data = video_result["video_data"]
        else:
            print(f"❌ Video rendering failed: {video_result.get('error')}")
            return

    except Exception as e:
        print(f"❌ Video rendering error: {e}")
        return

    # Phase 3: Combine video with audio (if audio was generated)
    if audio_data:
        print(f"\n🎵 Phase 3: Combining Video with Audio...")

        combine_start = time.time()

        try:
            combine_result = await combine_video_with_audio.remote.aio(
                video_data=video_data,
                audio_data=audio_data,
                output_name="comprehensive_transformer_tutorial",
            )

            if combine_result["success"]:
                print(f"✅ Audio+Video combined in {time.time() - combine_start:.1f}s")
                final_video_data = combine_result["video_data"]
                final_filename = combine_result["filename"]
                final_size = combine_result["file_size"]
            else:
                print(f"⚠️ Combining failed: {combine_result.get('error')}")
                # Fall back to video-only
                final_video_data = video_data
                final_filename = "comprehensive_transformer_tutorial.mp4"
                final_size = video_result["file_size"]

        except Exception as e:
            print(f"⚠️ Combining error: {e}")
            # Fall back to video-only
            final_video_data = video_data
            final_filename = "comprehensive_transformer_tutorial.mp4"
            final_size = video_result["file_size"]
    else:
        final_video_data = video_data
        final_filename = "comprehensive_transformer_tutorial.mp4"
        final_size = video_result["file_size"]

    # Phase 4: Save the final video locally
    print(f"\n💾 Phase 4: Saving Final Video...")

    try:
        # Decode and save the video
        video_bytes = base64.b64decode(final_video_data)

        output_dir = Path("media/videos")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / final_filename

        with open(output_path, "wb") as f:
            f.write(video_bytes)

        print(f"✅ Final video saved: {output_path}")
        print(f"📏 File size: {final_size / (1024*1024):.2f} MB")
        print(f"🎵 Has audio: {audio_data is not None}")

        # Calculate total time
        total_time = time.time() - start_time
        print(f"\n🏁 Total compilation time: {total_time:.1f}s")

        # Show final summary
        print(f"\n🎉 SUCCESS! Comprehensive Transformer Tutorial Compiled!")
        print(f"📹 Video: {output_path}")
        print(f"⏱️ Duration: Check the video for exact duration")
        print(f"🎯 Scenes: All comprehensive scenes included")
        print(f"🔥 GPU: A100 acceleration used")

        return output_path

    except Exception as e:
        print(f"❌ Error saving video: {e}")
        return None


async def render_individual_scenes():
    """Render individual scenes for testing"""

    print("🎬 Rendering Individual Tutorial Scenes")
    print("=" * 50)

    # Import Modal functions
    from modal_gpu_manim import gpu_render_manim_video

    # Read the comprehensive tutorial code
    tutorial_path = Path("comprehensive_transformer_tutorial.py")
    with open(tutorial_path, "r") as f:
        tutorial_code = f.read()

    # Scene list to render individually
    individual_scenes = [
        "Scene_Intro",
        "Scene_AttentionMath",
        "Scene_AttentionVisualization",
        "Scene_MultiHeadDetailed",
        "Scene_PositionalEncodingDetailed",
    ]

    rendered_videos = []

    for scene_name in individual_scenes:
        print(f"\n🎯 Rendering: {scene_name}")

        try:
            start_time = time.time()

            result = await gpu_render_manim_video.remote.aio(
                manim_code=tutorial_code, scene_name=scene_name
            )

            if result["success"]:
                print(f"✅ {scene_name} rendered in {time.time() - start_time:.1f}s")

                # Save the individual video
                video_bytes = base64.b64decode(result["video_data"])
                output_path = Path("media/videos") / f"{scene_name}.mp4"

                with open(output_path, "wb") as f:
                    f.write(video_bytes)

                print(f"💾 Saved: {output_path}")
                rendered_videos.append(output_path)

            else:
                print(f"❌ {scene_name} failed: {result.get('error')}")

        except Exception as e:
            print(f"❌ Error rendering {scene_name}: {e}")

    print(f"\n🏁 Rendered {len(rendered_videos)} individual scenes")
    return rendered_videos


async def main():
    """Main compilation function"""

    print("🚀 Comprehensive Transformer Tutorial Compilation")
    print("Using GPU acceleration on Modal Labs")
    print("=" * 70)

    # Option 1: Compile the full comprehensive tutorial
    print("📋 Option 1: Full Comprehensive Tutorial")
    final_video = await compile_comprehensive_tutorial()

    if final_video:
        print(f"\n✅ SUCCESS: {final_video}")
    else:
        print(f"\n❌ Compilation failed")

    # Option 2: Render individual scenes (commented out by default)
    # print("\n📋 Option 2: Individual Scenes")
    # individual_videos = await render_individual_scenes()

    print(f"\n🎬 Compilation complete!")


if __name__ == "__main__":
    asyncio.run(main())
