"""
Client Demo: How your PDF parser would send requests to the ExplainX Processor API
This demonstrates the integration between your PDF parser and the processor API
"""

import requests
import json

# Configuration
PROCESSOR_API_URL = "http://127.0.0.1:8001"


def send_pdf_to_processor(pdf_processing_result):
    """
    Send PDF processing results to the ExplainX Processor API.

    This is exactly what your PDF parser would do after processing a PDF.
    """

    print("🚀 Sending PDF processing result to ExplainX Processor API...")
    print(f"📄 Filename: {pdf_processing_result['filename']}")
    print(f"📝 Text length: {len(pdf_processing_result['extracted_text'])} characters")
    print(f"🖼️ Images: {len(pdf_processing_result['extracted_images'])} images")

    # Option 1: Generate detailed notes only
    print("\n📚 Option 1: Generate detailed educational notes...")
    try:
        response = requests.post(
            f"{PROCESSOR_API_URL}/api/generate-notes",
            json=pdf_processing_result,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Notes generated successfully!")
            print(f"📝 Notes length: {len(result['notes'])} characters")
            print(f"🎯 Preview: {result['notes'][:200]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Option 2: Extract educational context for video
    print("\n🎬 Option 2: Extract educational context for video...")
    try:
        response = requests.post(
            f"{PROCESSOR_API_URL}/api/extract-context",
            json=pdf_processing_result,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Educational context extracted!")
            print(f"📝 Context length: {result['context_length']} characters")
            print(f"🎯 Context for video: {result['educational_context']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Option 3: Complete PDF-to-Video pipeline
    print("\n🎥 Option 3: Complete PDF-to-Video pipeline...")
    try:
        response = requests.post(
            f"{PROCESSOR_API_URL}/api/generate-video",
            json=pdf_processing_result,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print("✅ Complete pipeline executed!")
                if "video_generation" in result:
                    video_result = result["video_generation"]
                    if video_result["success"]:
                        print(
                            f"🎬 Video generation started: {video_result['video_result'].get('operation_name', 'N/A')}"
                        )
                        print(
                            f"📝 Educational context used: {result.get('educational_context_for_video', '')[:100]}..."
                        )
                    else:
                        print(f"⚠️ Video generation failed: {video_result['error']}")
                print(f"💾 Notes file: {result.get('notes_file_path', 'Not saved')}")
            else:
                print(f"❌ Pipeline failed: {result['error']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")


def test_direct_video_generation():
    """
    Test the new direct video generation endpoint.

    This demonstrates the shortest path from educational content to video.
    """

    print("\n🎬 Option 4: Direct Educational Content to Video...")

    # Direct educational content request
    direct_video_request = {
        "educational_content": """
        Introduction to Machine Learning Fundamentals
        
        Machine learning is a powerful subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. In this comprehensive guide, we'll explore the core concepts that make machine learning possible.
        
        Key topics we'll cover:
        - Supervised Learning: Learning from labeled examples
        - Unsupervised Learning: Finding patterns in unlabeled data  
        - Neural Networks: The building blocks of deep learning
        - Feature Engineering: Preparing data for optimal learning
        - Model Evaluation: Measuring and improving performance
        
        Understanding these fundamentals will give you a solid foundation for diving deeper into advanced machine learning techniques and applications.
        """,
        "presenter_image_path": "Generated Image September 14, 2025 - 6_31AM.png",
        "video_length": "extensive",
        "background_style": "auto",
        "lighting_style": "professional",
        "clothing_style": "professional",
    }

    try:
        response = requests.post(
            f"{PROCESSOR_API_URL}/api/direct-video",
            json=direct_video_request,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print("✅ Direct video generation started!")
                print(f"🆔 Operation: {result['operation_name']}")
                print(f"📸 Using image: {result['presenter_image_path']}")
                print(f"⚙️ Video settings: {result['video_settings']}")
                print(f"📁 Video will be saved to: generated_videos/")
                print(f"⏰ Background job will download in ~15 minutes")
                print(f"🔧 Monitor with: python video_monitor.py")
            else:
                print(f"❌ Direct video generation failed: {result['error']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")


def main():
    """Demonstrate how your PDF parser would integrate with the processor API"""

    print("🧪 ExplainX Client Demo")
    print("=" * 50)
    print("This demonstrates how your PDF parser sends data to the processor API")
    print()

    # This is the exact format your PDF parser sends
    sample_pdf_result = {
        "message": "PDF processed successfully",
        "filename": "Advanced_Statistics_Lecture.pdf",
        "extracted_text": """
Statistical Analysis and Data Interpretation

Chapter 3: Hypothesis Testing and Confidence Intervals

Introduction:
Statistical inference allows us to make conclusions about populations based on sample data. 
This chapter covers the fundamental concepts of hypothesis testing, including null and alternative 
hypotheses, Type I and Type II errors, p-values, and confidence intervals.

Hypothesis Testing Framework:
1. State the null hypothesis (H0) and alternative hypothesis (H1)
2. Choose significance level (α)
3. Calculate test statistic
4. Determine p-value
5. Make decision: reject or fail to reject H0

Confidence Intervals:
A confidence interval provides a range of plausible values for a population parameter.
The confidence level represents the probability that the interval contains the true parameter.

Example: 95% confidence interval for population mean
When σ is known: x̄ ± z(α/2) × (σ/√n)
When σ is unknown: x̄ ± t(α/2) × (s/√n)

Applications:
- Quality control in manufacturing
- Medical research and clinical trials
- Market research and polling
- Scientific experimentation
        """,
        "extracted_images": ["a1b2c3d4e5f6", "f6e5d4c3b2a1", "1a2b3c4d5e6f"],
    }

    # Check if API is running
    try:
        health_check = requests.get(f"{PROCESSOR_API_URL}/")
        if health_check.status_code == 200:
            print("✅ ExplainX Processor API is running")
            print(f"🔗 API URL: {PROCESSOR_API_URL}")
            print()

            # Demonstrate the integration
            send_pdf_to_processor(sample_pdf_result)

            # Test the new direct video generation endpoint
            test_direct_video_generation()

        else:
            print("❌ API not responding correctly")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to ExplainX Processor API")
        print(f"💡 Make sure the API is running: python api.py")
        print(f"🔗 Expected URL: {PROCESSOR_API_URL}")


if __name__ == "__main__":
    main()
