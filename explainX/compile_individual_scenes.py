#!/usr/bin/env python3
"""
Compile individual scenes of the Transformer tutorial
This approach is more reliable than rendering the complete master scene
"""

import asyncio
import base64
from pathlib import Path
import time


async def render_scene_on_modal(scene_name: str, tutorial_code: str):
    """Render a single scene using Modal GPU"""
    from modal_gpu_manim import gpu_render_manim_video

    print(f"🎬 Rendering {scene_name}...")
    start_time = time.time()

    try:
        result = await gpu_render_manim_video.remote.aio(
            manim_code=tutorial_code, scene_name=scene_name
        )

        if result["success"]:
            render_time = time.time() - start_time
            print(f"✅ {scene_name} rendered in {render_time:.1f}s")
            print(f"📏 Size: {result['file_size'] / (1024*1024):.2f} MB")

            # Save the video locally
            video_bytes = base64.b64decode(result["video_data"])
            output_dir = Path("media/videos")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / f"{scene_name}.mp4"
            with open(output_path, "wb") as f:
                f.write(video_bytes)

            print(f"💾 Saved: {output_path}")
            return output_path, render_time

        else:
            print(f"❌ {scene_name} failed: {result.get('error', 'Unknown error')}")
            return None, 0

    except Exception as e:
        print(f"❌ Error rendering {scene_name}: {e}")
        return None, 0


async def compile_all_scenes():
    """Compile all individual scenes of the Transformer tutorial"""

    print("🚀 Compiling Transformer Tutorial - Individual Scenes")
    print("=" * 60)

    # Read the tutorial code
    tutorial_path = Path("comprehensive_transformer_tutorial.py")
    if not tutorial_path.exists():
        print(f"❌ Tutorial file not found: {tutorial_path}")
        return []

    with open(tutorial_path, "r") as f:
        tutorial_code = f.read()

    print(f"📖 Loaded tutorial: {len(tutorial_code)} characters")

    # List of scenes to render
    scenes_to_render = [
        "Scene_Intro",
        "Scene_AttentionMath",
        "Scene_AttentionVisualization",
        "Scene_MultiHeadDetailed",
        "Scene_PositionalEncodingDetailed",
        "Scene_FullArchitecture",
        "Scene_TrainingDetails",
        "Scene_ResultsImpact",
        "Scene_Conclusion",
    ]

    print(f"🎯 Will render {len(scenes_to_render)} scenes")
    print(f"📋 Scenes: {', '.join(scenes_to_render)}")

    total_start_time = time.time()
    rendered_videos = []
    total_render_time = 0

    # Render each scene individually
    for i, scene_name in enumerate(scenes_to_render, 1):
        print(f"\n📽️ [{i}/{len(scenes_to_render)}] {scene_name}")

        video_path, render_time = await render_scene_on_modal(scene_name, tutorial_code)

        if video_path:
            rendered_videos.append(video_path)
            total_render_time += render_time

        # Small delay between renders to avoid overwhelming the system
        if i < len(scenes_to_render):
            await asyncio.sleep(2)

    total_time = time.time() - total_start_time

    # Summary
    print(f"\n🏁 Compilation Summary")
    print("=" * 40)
    print(
        f"✅ Successfully rendered: {len(rendered_videos)}/{len(scenes_to_render)} scenes"
    )
    print(f"⏱️ Total render time: {total_render_time:.1f}s")
    print(f"🕒 Total elapsed time: {total_time:.1f}s")
    print(f"🔥 Using: Modal GPU A100 acceleration")

    if rendered_videos:
        print(f"\n📹 Generated Videos:")
        total_size = 0
        for video_path in rendered_videos:
            if video_path.exists():
                size_mb = video_path.stat().st_size / (1024 * 1024)
                total_size += size_mb
                print(f"  • {video_path.name} ({size_mb:.2f} MB)")

        print(f"\n📊 Total size: {total_size:.2f} MB")
        print(f"💾 Location: media/videos/")

        # Instructions for combining videos
        print(f"\n🔧 To combine all scenes into one video, run:")
        print(
            f"ffmpeg -f concat -safe 0 -i scene_list.txt -c copy comprehensive_tutorial.mp4"
        )

        # Create concat file
        create_concat_file(rendered_videos)

    return rendered_videos


def create_concat_file(video_paths):
    """Create a concat file for ffmpeg to combine all videos"""
    concat_file = Path("scene_list.txt")

    with open(concat_file, "w") as f:
        for video_path in video_paths:
            f.write(f"file '{video_path.absolute()}'\n")

    print(f"📝 Created concat file: {concat_file}")


async def quick_test_render():
    """Quick test with just the intro scene"""
    print("🧪 Quick Test: Rendering Scene_Intro only")
    print("=" * 40)

    tutorial_path = Path("comprehensive_transformer_tutorial.py")
    with open(tutorial_path, "r") as f:
        tutorial_code = f.read()

    video_path, render_time = await render_scene_on_modal("Scene_Intro", tutorial_code)

    if video_path:
        print(f"✅ Test successful! Scene rendered in {render_time:.1f}s")
        return True
    else:
        print(f"❌ Test failed!")
        return False


async def main():
    """Main function with options"""
    print("🎬 Transformer Tutorial Compiler")
    print("Choose compilation mode:")
    print("1. Quick test (Scene_Intro only)")
    print("2. Full compilation (all 9 scenes)")

    # For automation, let's do the quick test first
    print("\n🧪 Running quick test first...")
    test_success = await quick_test_render()

    if test_success:
        print("\n🚀 Test passed! Running full compilation...")
        await compile_all_scenes()
    else:
        print("\n❌ Test failed. Please check Modal setup.")


if __name__ == "__main__":
    asyncio.run(main())
