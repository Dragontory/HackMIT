"""
Simple presenter video generation service for ExplainX
Generates presenter introduction videos using Google Veo 3 API via Gemini
"""

import time
import random
import base64
import os
from typing import Optional, List
from dataclasses import dataclass
from google import genai
from google.genai import types
import requests  # Still needed for image upload

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Anthropic for dynamic intro generation
try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class VideoResult:
    """Result of video generation"""

    success: bool
    operation_name: str
    status: str
    video_file_path: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ImageUploadResult:
    """Result of image upload to public URL"""

    success: bool
    public_url: str
    error_message: Optional[str] = None


def upload_image_to_public_url(image_path: str) -> ImageUploadResult:
    """
    Upload a local image file to a publicly accessible URL

    Args:
        image_path: Path to the local image file

    Returns:
        ImageUploadResult with success status and public URL

    Example:
        upload_result = upload_image_to_public_url("./my_presenter.jpg")
        if upload_result.success:
            print(f"Public URL: {upload_result.public_url}")
    """

    if not os.path.exists(image_path):
        return ImageUploadResult(
            success=False,
            public_url="",
            error_message=f"Image file not found: {image_path}",
        )

    try:
        print(f"📤 Uploading image to public URL: {os.path.basename(image_path)}")

        # Read and encode the image file
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        # Upload to Imgur (anonymous upload - no API key required)
        imgur_url = "https://api.imgur.com/3/image"
        headers = {
            "Authorization": "Client-ID 546c25a59c58ad7",  # Public anonymous client ID
            "Content-Type": "application/json",
        }

        payload = {
            "image": image_data,
            "type": "base64",
            "title": f"Presenter Image - {os.path.basename(image_path)}",
            "description": "Uploaded for ExplainX presenter video generation",
        }

        response = requests.post(imgur_url, headers=headers, json=payload)
        result = response.json()

        if response.ok and result.get("success"):
            public_url = result["data"]["link"]
            print(f"✅ Image uploaded successfully!")
            print(f"🔗 Public URL: {public_url}")

            return ImageUploadResult(
                success=True, public_url=public_url, error_message=None
            )
        else:
            error_msg = result.get("data", {}).get("error", "Unknown upload error")
            print(f"❌ Upload failed: {error_msg}")

            return ImageUploadResult(
                success=False,
                public_url="",
                error_message=f"Upload failed: {error_msg}",
            )

    except Exception as e:
        error_msg = f"Error uploading image: {str(e)}"
        print(f"💥 {error_msg}")

        return ImageUploadResult(success=False, public_url="", error_message=error_msg)


def generate_dynamic_intro_prompt(educational_context: str, api_key: str = None) -> str:
    """Generate dynamic intro prompt based on educational content using Anthropic API"""

    if not anthropic:
        print("⚠️ Anthropic not installed, using fallback intro")
        return f"Hello! Welcome to today's lesson on {educational_context}. I'm excited to guide you through this important topic. Let's dive in and explore these concepts together!"

    try:
        # Use provided API key or get from environment
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            print("⚠️ No Anthropic API key found, using fallback intro")
            return f"Hello! Welcome to today's lesson on {educational_context}. I'm excited to guide you through this important topic. Let's dive in and explore these concepts together!"

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Create an engaging, personalized introduction for an AI presenter who will teach about: "{educational_context}"

Requirements:
- 2-3 sentences maximum
- Enthusiastic but professional tone
- Mention the specific topic by name
- Use "I" as the presenter
- End with transition to the main content
- Make it feel personal and engaging
- No quotes around the response

Example topics and style:
- For "Machine Learning Basics": "Hello! I'm thrilled to introduce you to the fascinating world of Machine Learning. Today we'll explore how algorithms learn from data to make predictions and decisions. Let's dive into these powerful concepts that are reshaping our world!"

Topic: {educational_context}

Generate the intro:"""

        print(f"🤖 Generating dynamic intro for: {educational_context}")

        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=150,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )

        intro = message.content[0].text.strip()
        print(f"✅ Dynamic intro generated: {len(intro)} characters")

        return intro

    except Exception as e:
        print(f"⚠️ Error generating dynamic intro: {e}")
        print(f"🔄 Using fallback intro")
        return f"Hello! Welcome to today's lesson on {educational_context}. I'm excited to guide you through this important topic. Let's dive in and explore these concepts together!"


def upload_and_generate_presenter_video(
    api_key: str,
    local_image_path: str,
    educational_context: str,
    intro_prompt: str = None,  # Now optional - will be generated if not provided
    wait_for_completion: bool = True,
    video_length: str = "extensive",
    background_style: str = "auto",
    lighting_style: str = "auto",
    clothing_style: str = "auto",
    resolution: str = "720p",
    aspect_ratio: str = "9:16",
    start_background_checker: bool = False,
    background_wait_minutes: int = 20,
    anthropic_api_key: str = None,  # Optional Anthropic API key for dynamic intro
) -> VideoResult:
    """
    Upload local image to public URL and generate presenter introduction video

    This is a convenience function that combines image upload and video generation.

    Args:
        api_key: Veo3 API key
        local_image_path: Path to local presenter image file
        educational_context: What will be taught (e.g., "calculus derivatives")
        intro_prompt: What presenter should say (e.g., "Welcome to today's lesson...")
        wait_for_completion: Whether to wait for generation to complete
        video_length: "extensive", "medium", "short" - determines video length and detail
        background_style: "auto", "home_office", "classroom", "outdoor", "studio", "library"
        lighting_style: "auto", "warm", "bright", "natural", "professional", "soft"
        clothing_style: "auto", "professional", "casual", "formal", "colorful", "neutral"

    Returns:
        VideoResult with success status, task_id, video URLs

    Example:
        result = upload_and_generate_presenter_video(
            api_key="your_gemini_api_key",
            local_image_path="./Generated Image September 14, 2025 - 6_31AM.png",
            educational_context="calculus derivatives and limits",
            intro_prompt="Hello! Welcome to today's calculus lesson.",
            video_length="extensive",
            background_style="home_office",
            resolution="720p",
            aspect_ratio="9:16",
            start_background_checker=True,  # Auto-download in 20 minutes
            background_wait_minutes=20
        )

        if result.success:
            print(f"Video generated: {result.video_urls}")
    """

    print(f"🎬 Starting presenter video generation with local image...")

    # Step 0: Generate dynamic intro if not provided
    if intro_prompt is None:
        print(f"🤖 Generating dynamic intro prompt...")
        intro_prompt = generate_dynamic_intro_prompt(
            educational_context=educational_context, api_key=anthropic_api_key
        )
    else:
        print(f"📝 Using provided intro prompt")

    # Step 1: Upload image to get public URL
    upload_result = upload_image_to_public_url(local_image_path)

    if not upload_result.success:
        return VideoResult(
            success=False,
            task_id="",
            video_urls=[],
            status="upload_failed",
            error_message=f"Image upload failed: {upload_result.error_message}",
        )

    # Step 2: Generate video using the public URL
    print(f"🎥 Proceeding with video generation using public URL...")

    result = generate_presenter_intro_video(
        api_key=api_key,
        local_image_path=local_image_path,
        educational_context=educational_context,
        intro_prompt=intro_prompt,
        wait_for_completion=wait_for_completion,
        video_length=video_length,
        background_style=background_style,
        lighting_style=lighting_style,
        clothing_style=clothing_style,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
    )

    # Step 3: Start automatic background downloader
    if result.success and result.operation_name:
        print(f"🚀 Starting automatic background downloader...")
        _start_automatic_downloader(
            operation_name=result.operation_name,
            educational_context=educational_context,
            wait_minutes=background_wait_minutes,
        )

    return result


def generate_presenter_intro_video(
    api_key: str,
    local_image_path: str,
    educational_context: str,
    intro_prompt: str,
    wait_for_completion: bool = True,
    video_length: str = "extensive",
    background_style: str = "auto",
    lighting_style: str = "auto",
    clothing_style: str = "auto",
    resolution: str = "720p",
    aspect_ratio: str = "9:16",
) -> VideoResult:
    """
    Generate a presenter introduction video for educational content

    Args:
        api_key: Google Gemini API key (GEMINI_API_KEY)
        local_image_path: Path to local presenter image file
        educational_context: What will be taught (e.g., "calculus derivatives")
        intro_prompt: What presenter should say (e.g., "Welcome to today's lesson...")
        wait_for_completion: Whether to wait for generation to complete
        video_length: "extensive", "medium", "short" - determines video length and detail
        background_style: "auto", "home_office", "classroom", "outdoor", "studio", "library"
        lighting_style: "auto", "warm", "bright", "natural", "professional", "soft"
        clothing_style: "auto", "professional", "casual", "formal", "colorful", "neutral"
        resolution: "720p" (default) or "1080p" (16:9 only)
        aspect_ratio: "9:16" (default for mobile) or "16:9"

    Returns:
        VideoResult with success status, task_id, video URLs

    Example:
        result = generate_presenter_intro_video(
            api_key="your_gemini_api_key",
            local_image_path="./presenter.jpg",
            educational_context="calculus derivatives and limits",
            intro_prompt="Hello! Welcome to today's calculus lesson. I'm excited to guide you through understanding derivatives.",
            video_length="extensive",
            background_style="home_office",
            lighting_style="warm",
            clothing_style="professional",
            resolution="720p",
            aspect_ratio="9:16"
        )

        if result.success:
            print(f"Video generated: {result.video_file_path}")
    """

    # Generate background, lighting, and clothing suggestions
    background_options = _get_background_options(background_style, educational_context)
    lighting_options = _get_lighting_options(lighting_style)
    clothing_options = _get_clothing_options(clothing_style, educational_context)
    video_details = _get_video_length_details(video_length)

    # Create comprehensive enhanced prompt for natural presenter behavior
    enhanced_prompt = f"""
    {intro_prompt}
    
    Educational context: This is an {video_details['duration']} introduction to a lesson about {educational_context}.
    
    PRESENTER BEHAVIOR AND ACTIONS:
    The presenter should demonstrate the following throughout the video:
    - Start with a warm, welcoming smile and maintain engaging facial expressions
    - Make direct eye contact with the camera to connect with viewers
    - Use natural, expressive hand gestures that complement the speech
    - Maintain confident, professional posture while appearing approachable
    - Show genuine enthusiasm and passion for the educational topic
    - Speak clearly, at an appropriate pace with good articulation
    - Convey both expertise and accessibility
    - {video_details['behavior_detail']}
    
    BACKGROUND AND SETTING:
    {background_options}
    
    LIGHTING AND VISUAL STYLE:
    {lighting_options}
    
    CLOTHING AND APPEARANCE:
    {clothing_options}
    
    AUDIO AND DIALOGUE:
    - The presenter should speak clearly with natural audio
    - Consider ambient sound appropriate for the setting
    - Professional quality audio that matches the educational context
    - Include appropriate sound effects if relevant (e.g., "Good morning class")
    
    VIDEO QUALITY AND STYLE:
    - {video_details['quality']}
    - Smooth, professional camera work with stable framing
    - Natural transitions between different poses and gestures
    - Clear, crisp visual quality suitable for educational content
    - The presenter should feel alive and dynamic, not static
    
    OVERALL TONE:
    Professional yet approachable educational presenter, creating an inviting learning environment
    that makes complex topics accessible and engaging for students.
    """

    try:
        print(f"🎬 Generating presenter intro for: {educational_context}")

        # Initialize Gemini client
        client = genai.Client(api_key=api_key)

        # Load the image
        if not os.path.exists(local_image_path):
            raise Exception(f"Image file not found: {local_image_path}")

        print(f"📸 Loading image: {os.path.basename(local_image_path)}")

        # Prepare image for Veo 3 video generation
        print(f"📤 Preparing image for Veo 3...")

        # Read and encode image
        with open(local_image_path, "rb") as f:
            image_data = f.read()

        mime_type = (
            "image/png" if local_image_path.lower().endswith(".png") else "image/jpeg"
        )

        # Create image object using the correct field names (raw bytes, not base64)
        image = types.Image(image_bytes=image_data, mime_type=mime_type)

        print(f"✅ Image prepared for Veo 3 generation")

        # Generate video config (resolution not supported in current API)
        config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
        )

        # Step 1: Submit video generation request
        print(f"🚀 Starting Veo 3 video generation...")
        operation = client.models.generate_videos(
            model="veo-3.0-generate-001",
            prompt=enhanced_prompt,
            image=image,
            config=config,
        )

        print(f"🚀 Video generation started. Operation: {operation.name}")

        if not wait_for_completion:
            return VideoResult(
                success=True, operation_name=operation.name, status="generating"
            )

        # Step 2: Wait for completion
        print("⏳ Waiting for video generation to complete...")
        while not operation.done:
            print("⏳ Still generating...")
            time.sleep(10)
            operation = client.operations.get(operation)

        # Step 3: Download the video
        if operation.response and operation.response.generated_videos:
            video = operation.response.generated_videos[0]

            # Generate filename
            timestamp = int(time.time())
            filename = f"presenter_video_{timestamp}.mp4"

            print(f"📥 Downloading video to: {filename}")
            client.files.download(file=video.video)
            video.video.save(filename)

            print(f"✅ Video generated successfully!")
            print(f"🎥 Video saved to: {filename}")

            return VideoResult(
                success=True,
                operation_name=operation.name,
                video_file_path=filename,
                status="completed",
            )
        else:
            raise Exception("No video generated in operation response")

    except Exception as e:
        error_msg = f"Error generating presenter video: {str(e)}"
        print(f"💥 {error_msg}")
        return VideoResult(
            success=False,
            operation_name="",
            status="error",
            error_message=error_msg,
        )


def _start_automatic_downloader(
    operation_name: str, educational_context: str, wait_minutes: int = 20
):
    """Register task for automatic downloading by separate monitor process"""

    # Create pending tasks file for separate monitor to process
    import json
    from datetime import datetime

    pending_tasks_file = "pending_downloads.json"

    # Load existing pending tasks
    pending_tasks = []
    if os.path.exists(pending_tasks_file):
        try:
            with open(pending_tasks_file, "r") as f:
                pending_tasks = json.load(f)
        except:
            pending_tasks = []

    # Add new task
    task = {
        "operation_name": operation_name,
        "educational_context": educational_context,
        "created_at": datetime.now().isoformat(),
        "check_after": (datetime.now().timestamp() + (wait_minutes * 60)),
        "wait_minutes": wait_minutes,
        "status": "pending",
    }

    pending_tasks.append(task)

    # Save tasks
    with open(pending_tasks_file, "w") as f:
        json.dump(pending_tasks, f, indent=2)

    print(f"📝 Task registered for automatic download")
    print(f"⏰ Will be checked after {wait_minutes} minutes")
    print(f"🚀 Run: python video_monitor.py (to start background monitor)")

    return True


def _wait_for_completion_gemini(
    client: genai.Client, operation_name: str, max_wait_minutes: int = 10
) -> VideoResult:
    """Wait for Gemini video generation to complete"""

    try:
        operation = types.GenerateVideosOperation(name=operation_name)

        max_wait_time = max_wait_minutes * 60
        start_time = time.time()
        poll_interval = 10  # seconds

        while time.time() - start_time < max_wait_time:
            if operation.done:
                if operation.response and operation.response.generated_videos:
                    video = operation.response.generated_videos[0]

                    # Generate filename
                    timestamp = int(time.time())
                    filename = f"presenter_video_{timestamp}.mp4"

                    print(f"📥 Downloading video to: {filename}")
                    client.files.download(file=video.video)
                    video.video.save(filename)

                    return VideoResult(
                        success=True,
                        operation_name=operation_name,
                        video_file_path=filename,
                        status="completed",
                    )
                else:
                    return VideoResult(
                        success=False,
                        operation_name=operation_name,
                        status="failed",
                        error_message="No video generated in response",
                    )

            print(f"⏳ Still generating... ({int(time.time() - start_time)}s elapsed)")
            time.sleep(poll_interval)

            # Refresh operation status
            operation = client.operations.get(operation)

        # Timeout
        return VideoResult(
            success=False,
            operation_name=operation_name,
            status="timeout",
            error_message=f"Video generation timed out after {max_wait_minutes} minutes",
        )

    except Exception as e:
        return VideoResult(
            success=False,
            operation_name=operation_name,
            status="error",
            error_message=f"Status check error: {str(e)}",
        )


def _get_background_options(background_style: str, educational_context: str) -> str:
    """Generate background setting options for the presenter"""

    context_lower = educational_context.lower()

    if background_style == "auto":
        # Auto-select based on educational context
        if any(
            word in context_lower
            for word in ["science", "physics", "chemistry", "biology", "lab"]
        ):
            backgrounds = [
                "modern laboratory with scientific equipment softly blurred in background",
                "bright, clean science classroom with periodic table or models visible",
                "home office with science books and educational posters on walls",
            ]
        elif any(
            word in context_lower
            for word in ["math", "calculus", "algebra", "statistics"]
        ):
            backgrounds = [
                "minimalist home office with mathematical equations or formulas on whiteboard behind",
                "cozy study room with mathematics textbooks on shelves",
                "bright classroom with mathematical diagrams on walls",
            ]
        elif any(
            word in context_lower for word in ["history", "literature", "language"]
        ):
            backgrounds = [
                "warm library setting with books visible in soft focus",
                "elegant home study with classic books and wooden furniture",
                "comfortable reading room with historical artifacts or maps",
            ]
        elif any(
            word in context_lower for word in ["business", "finance", "economics"]
        ):
            backgrounds = [
                "professional home office with business books and charts",
                "modern office space with city view through window",
                "executive study room with professional lighting",
            ]
        else:
            backgrounds = [
                "bright, professional home office with educational materials",
                "clean, modern study space with good lighting",
                "comfortable learning environment with books and plants",
            ]
    else:
        background_options = {
            "home_office": [
                "comfortable home office with bookshelves, plants, and warm lighting",
                "modern home workspace with educational posters and organized desk",
                "cozy study room with personal touches and good natural light",
            ],
            "classroom": [
                "bright, modern classroom with whiteboards and educational materials",
                "traditional academic classroom with desks and learning resources",
                "interactive learning space with modern teaching tools",
            ],
            "outdoor": [
                "peaceful outdoor setting like a campus courtyard with natural lighting",
                "garden or park environment with soft, natural background",
                "outdoor educational space with trees and natural elements",
            ],
            "studio": [
                "professional video studio with controlled lighting and clean background",
                "modern broadcast-style setting with professional equipment",
                "minimalist studio space with professional backdrop",
            ],
            "library": [
                "traditional library with books and academic atmosphere",
                "modern library with comfortable seating and good lighting",
                "quiet study area in library with scholarly environment",
            ],
        }
        backgrounds = background_options.get(
            background_style, background_options["home_office"]
        )

    selected_background = random.choice(backgrounds)

    return f"""
    Setting: {selected_background}
    - The background should complement but not distract from the presenter
    - Ensure the setting feels authentic and appropriate for educational content
    - Background elements should be visible but softly focused
    """


def _get_lighting_options(lighting_style: str) -> str:
    """Generate lighting style options"""

    lighting_options = {
        "auto": [
            "natural, bright lighting that flatters the presenter and creates a welcoming atmosphere",
            "professional lighting setup with warm tones and good contrast",
            "soft, even lighting that eliminates harsh shadows and creates a friendly appearance",
        ],
        "warm": [
            "warm, golden lighting that creates a cozy and inviting atmosphere",
            "soft, warm-toned lighting similar to sunset or early morning light",
            "comfortable indoor lighting with warm color temperature",
        ],
        "bright": [
            "bright, energetic lighting that keeps the presenter alert and vibrant",
            "well-lit environment with high-key lighting for clear visibility",
            "crisp, bright lighting similar to daylight",
        ],
        "natural": [
            "natural window light with soft shadows and organic feel",
            "outdoor natural lighting or large window illumination",
            "daylight-balanced lighting that feels authentic and unforced",
        ],
        "professional": [
            "studio-quality lighting with key light, fill light, and background lighting",
            "professional three-point lighting setup for optimal presentation",
            "broadcast-quality lighting that enhances the presenter's features",
        ],
        "soft": [
            "gentle, diffused lighting that creates a calm and approachable mood",
            "soft box lighting that eliminates harsh shadows",
            "tender, flattering light that makes the presenter appear friendly",
        ],
    }

    selected_lighting = random.choice(
        lighting_options.get(lighting_style, lighting_options["auto"])
    )

    return f"""
    Lighting: {selected_lighting}
    - Lighting should enhance the presenter's facial features and expressions
    - Avoid harsh shadows or overexposed areas
    - Create depth and dimension while maintaining clarity
    """


def _get_clothing_options(clothing_style: str, educational_context: str) -> str:
    """Generate clothing and appearance options"""

    clothing_options = {
        "auto": [
            "smart casual attire appropriate for educational content - perhaps a nice shirt or blouse",
            "professional but approachable clothing that reflects expertise and accessibility",
            "clean, well-fitted clothing in colors that complement the background and lighting",
        ],
        "professional": [
            "business professional attire - blazer, dress shirt, or professional blouse",
            "formal business wear that conveys authority and expertise",
            "executive-style clothing with clean lines and professional appearance",
        ],
        "casual": [
            "smart casual wear - comfortable but neat shirt, sweater, or casual blazer",
            "relaxed but presentable clothing that makes the presenter seem approachable",
            "casual professional attire that's comfortable for teaching",
        ],
        "formal": [
            "formal academic attire - perhaps with subtle academic touches",
            "elegant, formal clothing suitable for important presentations",
            "sophisticated formal wear that commands respect and attention",
        ],
        "colorful": [
            "vibrant, engaging colors that energize the presentation - blues, greens, or warm tones",
            "bright, positive colors that create visual interest and engagement",
            "colorful but professional attire that reflects personality and enthusiasm",
        ],
        "neutral": [
            "neutral tones like navy, gray, beige, or white that focus attention on the message",
            "classic, timeless colors that won't distract from the educational content",
            "subtle, understated colors that create a professional baseline",
        ],
    }

    selected_clothing = random.choice(
        clothing_options.get(clothing_style, clothing_options["auto"])
    )

    return f"""
    Clothing and Appearance: {selected_clothing}
    - Clothing should be well-fitted and appropriate for the educational setting
    - Colors should work well with the background and lighting
    - Overall appearance should be neat, professional, and engaging
    - Consider the target audience and subject matter when choosing style
    """


def _get_video_length_details(video_length: str) -> dict:
    """Generate video length and detail specifications"""

    length_options = {
        "extensive": {
            "duration": "comprehensive and detailed",
            "behavior_detail": "Include multiple gestures, varied expressions, and dynamic movement throughout",
            "quality": "High production value with multiple angles or movements, detailed expressions and gestures",
        },
        "medium": {
            "duration": "moderately detailed",
            "behavior_detail": "Include several natural gestures and expression changes",
            "quality": "Good production quality with natural presenter movement and engagement",
        },
        "short": {
            "duration": "concise but engaging",
            "behavior_detail": "Focus on key gestures and clear, direct communication",
            "quality": "Clean, focused production with essential presenter elements",
        },
    }

    return length_options.get(video_length, length_options["extensive"])


# Enhanced test function
def test_with_enhanced_options():
    """Test function demonstrating the enhanced presenter video options"""

    import os

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Set GEMINI_API_KEY environment variable")
        return

    # Test cases with different style combinations
    test_cases = [
        {
            "name": "Science Lesson - Auto Settings",
            "image_path": "Generated Image September 14, 2025 - 6_31AM.png",
            "context": "quantum physics and particle behavior",
            "prompt": "Hello! Welcome to today's fascinating journey into quantum physics. I'm thrilled to guide you through the mysterious world of particle behavior and quantum mechanics.",
            "video_length": "extensive",
            "background": "auto",
            "lighting": "auto",
            "clothing": "auto",
            "resolution": "720p",
            "aspect_ratio": "9:16",
        },
        {
            "name": "Math Lesson - Home Office Setup",
            "image_path": "Generated Image September 14, 2025 - 6_31AM.png",
            "context": "calculus derivatives and optimization",
            "prompt": "Good morning! Ready to master calculus? Today we're diving deep into derivatives and optimization problems that will transform how you approach mathematics.",
            "video_length": "extensive",
            "background": "home_office",
            "lighting": "warm",
            "clothing": "professional",
            "resolution": "720p",
            "aspect_ratio": "9:16",
        },
        {
            "name": "History Lesson - Library Setting",
            "image_path": "Generated Image September 14, 2025 - 6_31AM.png",
            "context": "Renaissance art and cultural impact",
            "prompt": "Welcome to our exploration of Renaissance art! I'm excited to take you on a journey through this transformative period that reshaped human creativity and culture.",
            "video_length": "extensive",
            "background": "library",
            "lighting": "natural",
            "clothing": "colorful",
            "resolution": "720p",
            "aspect_ratio": "9:16",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎬 Test Case {i}: {test_case['name']}")
        print("=" * 50)

        result = generate_presenter_intro_video(
            api_key=api_key,
            local_image_path=test_case["image_path"],
            educational_context=test_case["context"],
            intro_prompt=test_case["prompt"],
            video_length=test_case["video_length"],
            background_style=test_case["background"],
            lighting_style=test_case["lighting"],
            clothing_style=test_case["clothing"],
            resolution=test_case["resolution"],
            aspect_ratio=test_case["aspect_ratio"],
            wait_for_completion=False,  # Just start generation for testing
        )

        if result.success:
            print(f"✅ Video generation started!")
            print(f"📋 Operation: {result.operation_name}")
            print(
                f"📝 Settings: {test_case['background']} background, {test_case['lighting']} lighting, {test_case['clothing']} clothing"
            )
            print(
                f"📱 Resolution: {test_case['resolution']}, Aspect: {test_case['aspect_ratio']}"
            )
        else:
            print(f"❌ Failed: {result.status}")
            if result.error_message:
                print(f"💥 Error: {result.error_message}")

        print()


def simple_test():
    """Simple test with default settings"""

    import os

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Set GEMINI_API_KEY environment variable")
        return

    # Simple test with auto settings
    image_path = "Generated Image September 14, 2025 - 6_31AM.png"

    result = generate_presenter_intro_video(
        api_key=api_key,
        local_image_path=image_path,
        educational_context="machine learning fundamentals",
        intro_prompt="Hello! Welcome to today's lesson on machine learning. I'm excited to guide you through these fascinating concepts!",
        # All other parameters will use defaults (extensive, auto, auto, auto, 720p, 9:16)
        wait_for_completion=False,
    )

    print(f"Simple Test Result: {result}")


if __name__ == "__main__":
    print("🎓 Enhanced Presenter Video Generation Tests")
    print("=" * 60)

    # Run comprehensive tests
    test_with_enhanced_options()

    print("\n" + "=" * 60)
    print("🔧 Simple Test with Default Settings")
    print("=" * 60)

    # Run simple test
    simple_test()
