#!/usr/bin/env python3
"""
Test script for the complete audio + video pipeline
Generates audio narration and combines it with existing videos
"""

import asyncio
import base64
from pathlib import Path
from audio_narrator import TransformerAudioNarrator
import subprocess


async def test_local_audio_generation():
    """Test local audio generation"""
    print("🎙️ Testing local audio generation...")

    narrator = TransformerAudioNarrator(voice="coral")

    # Test with a short narration
    test_text = """
    Welcome to our exploration of the Transformer architecture - one of the most 
    revolutionary developments in artificial intelligence.
    
    The Transformer, introduced in "Attention Is All You Need", fundamentally changed 
    how we approach sequence modeling by eliminating recurrence entirely.
    """

    try:
        audio_file = await narrator.generate_scene_audio("test_intro", test_text)
        print(f"✅ Audio generated: {audio_file}")

        # Check if ffmpeg is available
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            print("✅ FFmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg not found - install with: brew install ffmpeg")
            return

        # Test combining with existing video
        video_path = Path("media/videos/TransformerArchitectureIntro.mp4")
        if video_path.exists():
            output_path = Path(
                "media/videos/TransformerArchitectureIntro_with_audio.mp4"
            )
            success = narrator.combine_video_with_audio(
                video_path, audio_file, output_path
            )
            if success:
                print(f"✅ Combined video created: {output_path}")
            else:
                print("❌ Failed to combine video with audio")
        else:
            print(f"⚠️ Video not found: {video_path}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def test_modal_audio_pipeline():
    """Test the Modal audio pipeline"""
    print("🚀 Testing Modal audio pipeline...")

    try:
        import modal

        # Import our Modal app
        from modal_gpu_manim import complete_gpu_video_with_audio_pipeline

        # Test with a Transformer topic
        result = await complete_gpu_video_with_audio_pipeline.remote.aio(
            "Attention Is All You Need - Transformer Architecture", voice="coral"
        )

        if result["success"]:
            print(f"✅ Modal pipeline succeeded!")
            print(f"📹 Video: {result['filename']}")
            print(f"🎙️ Has audio: {result['has_audio']}")
            print(f"⏱️ Total time: {result['total_time']:.1f}s")

            # Save the video locally
            video_data = base64.b64decode(result["video_data"])
            output_path = Path("media/videos") / result["filename"]
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(video_data)

            print(f"💾 Video saved locally: {output_path}")

        else:
            print(f"❌ Modal pipeline failed: {result.get('error')}")

    except Exception as e:
        print(f"❌ Error testing Modal pipeline: {e}")


async def save_comprehensive_tutorial_with_audio():
    """Generate audio for our comprehensive tutorial and save locally"""
    print("🎬 Creating comprehensive tutorial with audio...")

    narrator = TransformerAudioNarrator(voice="coral")

    # Use the introduction narration
    intro_text = """
    Welcome to our comprehensive exploration of "Attention Is All You Need" - 
    the groundbreaking paper that revolutionized artificial intelligence.
    
    Published in 2017 by Vaswani and colleagues at Google, this paper introduced 
    the Transformer architecture... an elegant solution that would become the 
    foundation for GPT, BERT, and virtually every modern language model.
    
    But what made this work so revolutionary? Let's journey through the problems 
    it solved, the mathematics behind it, and why attention truly is all you need.
    
    For decades, sequence modeling relied on recurrent neural networks. But RNNs 
    had a fundamental limitation... they processed information sequentially, 
    word by word, creating a computational bottleneck.
    
    The Transformer changed everything. By eliminating recurrence entirely and 
    relying purely on attention mechanisms, it achieved superior performance 
    while being dramatically more efficient to train.
    """

    try:
        # Generate audio
        audio_file = await narrator.generate_scene_audio(
            "comprehensive_intro",
            intro_text,
            instructions=(
                "Speak with excitement and wonder about this breakthrough. "
                "Use dramatic pauses after key points like 'Transformer architecture' "
                "and 'attention truly is all you need'. Sound like you're unveiling "
                "something amazing to students."
            ),
        )

        print(f"✅ Comprehensive audio generated: {audio_file}")

        # Find existing video
        existing_videos = list(Path("media/videos").glob("*.mp4"))
        if existing_videos:
            video_path = existing_videos[0]  # Use the first video found
            print(f"📹 Using video: {video_path}")

            output_path = Path(
                "media/videos/Attention_Is_All_You_Need_-_Comprehensive_Tutorial_with_audio.mp4"
            )

            success = narrator.combine_video_with_audio(
                video_path, audio_file, output_path
            )
            if success:
                print(f"🎥 Final video with audio: {output_path}")
                print(
                    f"📏 File size: {output_path.stat().st_size / (1024*1024):.2f} MB"
                )
            else:
                print("❌ Failed to combine video with audio")
        else:
            print("⚠️ No existing videos found")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Main test function"""
    print("🎬 Audio Pipeline Test Suite")
    print("=" * 50)

    # Test 1: Local audio generation
    await test_local_audio_generation()
    print()

    # Test 2: Create comprehensive tutorial with audio
    await save_comprehensive_tutorial_with_audio()
    print()

    # Test 3: Modal pipeline (commented out for now)
    # await test_modal_audio_pipeline()

    print("🏁 Test suite completed!")


if __name__ == "__main__":
    asyncio.run(main())
