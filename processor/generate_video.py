"""
Simple Video Generation Script
Clean architecture with automatic background downloading
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
    """Generate presenter video with automatic background downloading"""

    print("🎬 ExplainX: Clean Video Generation")
    print("=" * 50)

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Please set GEMINI_API_KEY environment variable")
        return

    # Use the second presenter image for Gradient Descent
    presenter_image_path = "Generated Image September 14, 2025 - 6_32AM.png"

    if not os.path.exists(presenter_image_path):
        print(f"❌ Image not found: {presenter_image_path}")
        return

    print(f"📸 Using: {presenter_image_path}")

    # Educational content - User's exact input
    educational_context = """Gradient Descent — a practical, detailed guide

Gradient descent is the workhorse of modern optimization. If you train a neural network, fit a logistic regression, or tune a large language model, you are moving parameters by following gradients of a loss function. This guide gives you a careful, practitioner-friendly walk through the core ideas, variants you will actually use, when each makes sense, and the math that explains why they work."""

    print(f"🎓 Topic: {educational_context}")
    print(f"\n🚀 Starting generation with dynamic intro...")

    # Generate video with dynamic intro - no hardcoded intro_prompt!
    result = upload_and_generate_presenter_video(
        api_key=api_key,
        local_image_path=presenter_image_path,
        educational_context=educational_context,
        # intro_prompt=None,  # Will be generated dynamically!
        video_length="extensive",
        background_style="professional",
        lighting_style="soft",
        clothing_style="business_casual",
        wait_for_completion=False,  # Don't wait - use background job
        background_wait_minutes=15,  # Check after 15 minutes
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),  # For dynamic intro
    )

    if result.success:
        print(f"\n✅ Video generation started!")
        print(f"🆔 Operation: {result.operation_name}")
        print(f"📁 Video will be saved to: generated_videos/")
        print(f"⏰ Automatic download will start in 15 minutes")
        print(f"\n💡 Script completed. Background job is running.")
    else:
        print(f"\n❌ Generation failed: {result.error_message}")


if __name__ == "__main__":
    main()
