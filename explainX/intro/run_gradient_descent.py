"""
Generate Gradient Descent Video with Dynamic Intro
Using the exact inputs provided by the user
"""

import os
from presenter_video_service import upload_and_generate_presenter_video

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def main():
    """Generate video with user's exact inputs"""

    print("🎬 ExplainX: Gradient Descent Video with Dynamic Intro")
    print("=" * 60)

    # Check API keys
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not gemini_api_key:
        print("❌ Please set GEMINI_API_KEY environment variable")
        return

    if not anthropic_api_key:
        print("⚠️ No ANTHROPIC_API_KEY found - will use fallback intro")

    # User's exact inputs
    presenter_image_path = "Generated Image September 14, 2025 - 6_32AM.png"

    educational_context = """Gradient Descent — a practical, detailed guide

Gradient descent is the workhorse of modern optimization. If you train a neural network, fit a logistic regression, or tune a large language model, you are moving parameters by following gradients of a loss function. This guide gives you a careful, practitioner-friendly walk through the core ideas, variants you will actually use, when each makes sense, and the math that explains why they work."""

    # Check if image exists
    if not os.path.exists(presenter_image_path):
        print(f"❌ Image not found: {presenter_image_path}")
        return

    print(f"📸 Using image: {presenter_image_path}")
    print(f"🎓 Educational content: {educational_context[:100]}...")
    print(f"\n🤖 Generating dynamic intro and starting video creation...")

    # Generate video with dynamic intro
    result = upload_and_generate_presenter_video(
        api_key=gemini_api_key,
        local_image_path=presenter_image_path,
        educational_context=educational_context,
        # intro_prompt=None,  # Will be generated dynamically from the content!
        video_length="extensive",
        background_style="professional",
        lighting_style="soft",
        clothing_style="business_casual",
        resolution="720p",
        aspect_ratio="9:16",
        wait_for_completion=False,  # Use background monitor
        background_wait_minutes=15,  # Check after 15 minutes
        anthropic_api_key=anthropic_api_key,
    )

    if result.success:
        print(f"\n✅ Video generation started successfully!")
        print(f"🆔 Operation: {result.operation_name}")
        print(f"📁 Video will be saved to: generated_videos/")
        print(f"⏰ Background monitor will check in 15 minutes")
        print(f"\n💡 Next steps:")
        print(f"   1. Start monitor: python video_monitor.py")
        print(f"   2. Or use: ./start_monitor.sh")
        print(f"   3. Video will download automatically when ready")
    else:
        print(f"\n❌ Video generation failed!")
        print(f"🚨 Error: {result.error_message}")


if __name__ == "__main__":
    main()
