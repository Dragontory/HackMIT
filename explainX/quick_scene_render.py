#!/usr/bin/env python3
"""
Quick scene rendering script that compiles individual scenes
"""

import subprocess
import time
from pathlib import Path


def render_scene(scene_name: str):
    """Render a single scene using Modal CLI"""
    print(f"🎬 Rendering {scene_name}...")
    start_time = time.time()

    cmd = [
        "conda",
        "activate",
        "crawler_Env",
        "&&",
        "modal",
        "run",
        "modal_gpu_manim.py::gpu_render_manim_video",
        "--manim-code",
        "$(cat comprehensive_transformer_tutorial.py)",
        "--scene-name",
        scene_name,
    ]

    try:
        result = subprocess.run(
            " ".join(cmd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout per scene
        )

        render_time = time.time() - start_time

        if "Generated video:" in result.stdout and "File size:" in result.stdout:
            print(f"✅ {scene_name} rendered in {render_time:.1f}s")
            return True
        else:
            print(f"❌ {scene_name} failed or incomplete")
            print(f"Exit code: {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr[-500:]}")  # Last 500 chars
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️ {scene_name} timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Error rendering {scene_name}: {e}")
        return False


def compile_key_scenes():
    """Compile the most important scenes"""

    print("🎬 Compiling Key Transformer Tutorial Scenes")
    print("=" * 50)

    # Key scenes to render (focusing on most important content)
    key_scenes = [
        "Scene_Intro",
        "Scene_AttentionMath",
        "Scene_AttentionVisualization",
        "Scene_MultiHeadDetailed",
        "Scene_FullArchitecture",
    ]

    print(f"🎯 Will render {len(key_scenes)} key scenes")

    successful_renders = 0
    total_start_time = time.time()

    for i, scene_name in enumerate(key_scenes, 1):
        print(f"\n📽️ [{i}/{len(key_scenes)}] {scene_name}")

        if render_scene(scene_name):
            successful_renders += 1

        # Small delay between renders
        if i < len(key_scenes):
            print("⏳ Waiting 30s before next render...")
            time.sleep(30)

    total_time = time.time() - total_start_time

    print(f"\n🏁 Compilation Summary")
    print("=" * 30)
    print(f"✅ Successfully rendered: {successful_renders}/{len(key_scenes)} scenes")
    print(f"🕒 Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"🔥 Using: Modal GPU A100 acceleration")

    # Check what videos we have
    video_dir = Path("media/videos")
    if video_dir.exists():
        videos = list(video_dir.glob("*.mp4"))
        print(f"\n📹 Generated Videos ({len(videos)}):")
        for video in videos:
            size_mb = video.stat().st_size / (1024 * 1024)
            print(f"  • {video.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    compile_key_scenes()
