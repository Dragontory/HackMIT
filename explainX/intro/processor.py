"""
PDF Text Processor for ExplainX
Processes extracted PDF text and generates detailed educational notes using Anthropic Claude
"""

import os
import json
from typing import Dict, Any, Optional
import subprocess
import sys

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Anthropic for generating detailed educational notes
try:
    import anthropic
except ImportError:
    anthropic = None


def generate_detailed_notes(pdf_processing_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract text from PDF processing result and generate detailed educational notes using Anthropic Claude.

    Args:
        pdf_processing_result: Dictionary containing PDF processing results with 'extracted_text' field

    Returns:
        Dictionary containing the generated notes and metadata

    Example input:
        {
            "message": "PDF processed successfully",
            "filename": "Sample.pdf",
            "extracted_text": "...",
            "extracted_images": [...]
        }
    """

    # Validate input
    if not isinstance(pdf_processing_result, dict):
        return {"success": False, "error": "Input must be a dictionary", "notes": None}

    if "extracted_text" not in pdf_processing_result:
        return {
            "success": False,
            "error": "No 'extracted_text' field found in input",
            "notes": None,
        }

    extracted_text = pdf_processing_result.get("extracted_text", "").strip()

    if not extracted_text:
        return {"success": False, "error": "Extracted text is empty", "notes": None}

    # Check for Anthropic API key
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        return {
            "success": False,
            "error": "ANTHROPIC_API_KEY environment variable not found",
            "notes": None,
        }

    if not anthropic:
        return {
            "success": False,
            "error": "Anthropic library not installed. Run: pip install anthropic",
            "notes": None,
        }

    try:
        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=anthropic_api_key)

        # Create comprehensive educational prompt
        educational_prompt = f"""You are an expert educator and academic note-taker. Your task is to create comprehensive, detailed educational notes based on the extracted text from an academic document.

**Your Role**: Act as the most thorough and helpful teacher who wants to ensure students deeply understand every concept.

**Instructions for Creating Detailed Notes**:

1. **COMPREHENSIVE COVERAGE**: Create extensive notes that cover every important concept, formula, definition, and example in the text
2. **EDUCATIONAL DEPTH**: Explain not just WHAT concepts are, but WHY they matter and HOW they connect to broader topics
3. **STRUCTURED LEARNING**: Organize information in a logical, hierarchical way that builds understanding step by step
4. **PRACTICAL INSIGHTS**: Include practical applications, real-world examples, and study tips
5. **MATHEMATICAL CLARITY**: For any mathematical content, provide:
   - Clear explanations of formulas and their components
   - Step-by-step worked examples
   - Intuitive explanations of mathematical concepts
6. **VISUAL DESCRIPTIONS**: When referencing charts, graphs, or diagrams mentioned in the text, provide detailed descriptions
7. **STUDY AIDS**: Include:
   - Key takeaways for each section
   - Important formulas highlighted
   - Common pitfalls to avoid
   - Practice questions or self-check items where appropriate

**Format Requirements**:
- Use clear headings and subheadings
- Include bullet points for key concepts
- Use numbered lists for procedures or steps
- Highlight important terms and definitions
- Include examples and counterexamples where helpful

**Tone**: Write as an enthusiastic, knowledgeable teacher who wants to make complex concepts accessible and engaging.

**Document Content to Process**:
{extracted_text}

**Generate detailed educational notes that would help a student master this material completely. Make the notes as comprehensive and educational as possible - this is not a summary, but rather detailed teaching notes that expand on and clarify the content.**"""

        # Make API call to Anthropic
        print("🤖 Generating detailed educational notes with Anthropic Claude...")

        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",  # Latest available Claude model
            max_tokens=4000,  # Allow for comprehensive notes
            temperature=0.1,  # Low temperature for consistent, accurate educational content
            messages=[{"role": "user", "content": educational_prompt}],
        )

        generated_notes = response.content[0].text

        # Extract metadata from original input
        filename = pdf_processing_result.get("filename", "Unknown")
        has_images = bool(pdf_processing_result.get("extracted_images", []))

        return {
            "success": True,
            "error": None,
            "notes": generated_notes,
            "metadata": {
                "source_filename": filename,
                "original_text_length": len(extracted_text),
                "notes_length": len(generated_notes),
                "has_extracted_images": has_images,
                "image_count": len(pdf_processing_result.get("extracted_images", [])),
                "model_used": "claude-3-7-sonnet-20250219",
                "processing_timestamp": pdf_processing_result.get("timestamp"),
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating notes with Anthropic: {str(e)}",
            "notes": None,
        }


def extract_educational_context_for_video(notes: str, max_length: int = 400) -> str:
    """
    Extract the first meaningful chunk of educational notes for video generation.

    Args:
        notes: Generated educational notes
        max_length: Maximum length of educational context

    Returns:
        Cleaned educational context suitable for video generation
    """
    if not notes:
        return ""

    # Split into lines and find content after the header
    lines = notes.split("\n")
    content_lines = []
    started = False

    for line in lines:
        # Skip header information
        if (
            line.startswith("DETAILED EDUCATIONAL NOTES")
            or line.startswith("Source:")
            or line.startswith("Generated by:")
            or line.startswith("=")
        ):
            continue

        # Start collecting after we hit actual content
        if line.strip() and (line.startswith("#") or started):
            started = True
            # Remove markdown formatting for video context
            clean_line = line.replace("#", "").replace("*", "").replace("-", "").strip()
            if clean_line:
                content_lines.append(clean_line)

        # Stop if we have enough content or hit a major section break
        current_text = " ".join(content_lines)
        if len(current_text) >= max_length:
            break

    # Join and clean up
    educational_context = " ".join(content_lines)

    # Truncate to max length if needed
    if len(educational_context) > max_length:
        educational_context = educational_context[:max_length].rsplit(" ", 1)[0] + "..."

    return educational_context


def generate_video_from_notes(
    notes: str,
    presenter_image_path: str = "Generated Image September 14, 2025 - 6_32AM.png",
) -> Dict[str, Any]:
    """
    Generate a video using the first chunk of educational notes as context.

    Args:
        notes: Generated educational notes
        presenter_image_path: Path to presenter image

    Returns:
        Dictionary with video generation results
    """
    try:
        # Extract educational context from notes
        educational_context = extract_educational_context_for_video(notes)

        if not educational_context:
            return {
                "success": False,
                "error": "Could not extract educational context from notes",
                "video_result": None,
            }

        print(f"🎬 Extracted educational context for video:")
        print(f"📝 Context: {educational_context[:100]}...")

        # Import video generation function
        try:
            from presenter_video_service import upload_and_generate_presenter_video
        except ImportError:
            return {
                "success": False,
                "error": "presenter_video_service not available",
                "video_result": None,
            }

        # Get API keys
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if not gemini_api_key:
            return {
                "success": False,
                "error": "GEMINI_API_KEY environment variable required",
                "video_result": None,
            }

        # Check if presenter image exists
        if not os.path.exists(presenter_image_path):
            return {
                "success": False,
                "error": f"Presenter image not found: {presenter_image_path}",
                "video_result": None,
            }

        print(f"🚀 Starting video generation with educational context...")

        # Generate video with extracted educational context
        video_result = upload_and_generate_presenter_video(
            api_key=gemini_api_key,
            local_image_path=presenter_image_path,
            educational_context=educational_context,
            video_length="extensive",
            background_style="professional",
            lighting_style="soft",
            clothing_style="business_casual",
            wait_for_completion=False,
            background_wait_minutes=15,
            anthropic_api_key=anthropic_api_key,
        )

        return {
            "success": True,
            "error": None,
            "video_result": video_result,
            "educational_context_used": educational_context,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating video: {str(e)}",
            "video_result": None,
        }


def process_pdf_text_to_notes(
    pdf_processing_result: Dict[str, Any],
    save_to_file: bool = False,
    output_dir: str = "generated_notes",
    generate_video: bool = False,
    presenter_image_path: str = "Generated Image September 14, 2025 - 6_32AM.png",
) -> Dict[str, Any]:
    """
    Complete pipeline to process PDF text and generate detailed notes.

    Args:
        pdf_processing_result: Dictionary from PDF processing
        save_to_file: Whether to save notes to a text file
        output_dir: Directory to save notes file
        generate_video: Whether to generate a video from the notes
        presenter_image_path: Path to presenter image for video generation

    Returns:
        Dictionary with processing results and generated notes
    """

    print("📚 Processing PDF text for detailed educational notes...")

    # Generate detailed notes
    result = generate_detailed_notes(pdf_processing_result)

    if not result["success"]:
        print(f"❌ Error: {result['error']}")
        return result

    print("✅ Successfully generated detailed educational notes!")

    # Optionally save to file
    if save_to_file and result["notes"]:
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Generate filename
            source_filename = result["metadata"]["source_filename"]
            base_name = os.path.splitext(source_filename)[0]
            notes_filename = f"{base_name}_detailed_notes.txt"
            notes_path = os.path.join(output_dir, notes_filename)

            # Save notes
            with open(notes_path, "w", encoding="utf-8") as f:
                f.write(f"DETAILED EDUCATIONAL NOTES\n")
                f.write(f"Source: {source_filename}\n")
                f.write(f"Generated by: Claude (Anthropic)\n")
                f.write(f"{'='*60}\n\n")
                f.write(result["notes"])

            result["notes_file_path"] = notes_path
            print(f"💾 Notes saved to: {notes_path}")

        except Exception as e:
            print(f"⚠️ Warning: Could not save notes to file: {e}")

    # Optionally generate video from notes
    if generate_video and result["notes"]:
        print("\n🎬 Generating video from educational notes...")
        video_result = generate_video_from_notes(result["notes"], presenter_image_path)

        if video_result["success"]:
            print("✅ Video generation started successfully!")
            result["video_generation"] = video_result
            result["educational_context_for_video"] = video_result[
                "educational_context_used"
            ]
        else:
            print(f"❌ Video generation failed: {video_result['error']}")
            result["video_generation"] = video_result

    return result


def process_pdf_and_generate_video(
    pdf_processing_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convenience function: Complete workflow from PDF processing to video generation.

    Args:
        pdf_processing_result: Dictionary from PDF processing

    Returns:
        Dictionary with complete processing results
    """
    print("🚀 Starting complete PDF-to-Video pipeline...")

    return process_pdf_text_to_notes(
        pdf_processing_result=pdf_processing_result,
        save_to_file=True,  # Save notes file
        generate_video=True,  # Generate video
        output_dir="generated_notes",
    )


# Example usage and testing
if __name__ == "__main__":
    # Test with sample data
    sample_input = {
        "message": "PDF processed successfully",
        "filename": "Sample.pdf",
        "extracted_text": "Summarizing Data II \nMath 11: Lecture 2\nDenise Rava (drava@ucsd.edu)\nUCSD\n\n\nDataset: an example\nAcademic salaries data:\nVariables\nObservations\nSource: https://support.minitab.com/en-us/datasets/anova-data-sets/academic-salaries/\n\n\nCategorical/Qualitative: Bar Chart.               \n12 professors teach  humanities' courses\n9 professors teach  management' courses\nVisualizing Data\n13\n12\n\n\nVisualizing Data\nNumeric/Quantitative: Histogram.               \nOnly one professor got a salary  \nbetween 1.6 and 1.8.\n9 professors got a salary  \nbetween 2.6 and 2.8.\n1 .8",
        "extracted_images": ["877e7a40482e3737", "936e626e627e486a"],
    }

    print("🧪 Testing PDF text processor...")

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable to test")
        print("💡 Add to .env file: ANTHROPIC_API_KEY=your_api_key_here")
    else:
        # Test basic processing
        result = process_pdf_text_to_notes(sample_input, save_to_file=True)

        if result["success"]:
            print("\n📋 Generated Notes Preview:")
            print("-" * 50)
            print(
                result["notes"][:500] + "..."
                if len(result["notes"]) > 500
                else result["notes"]
            )
            print("-" * 50)
            print(f"📊 Metadata: {result['metadata']}")

            # Test educational context extraction
            print("\n🧪 Testing educational context extraction for video...")
            educational_context = extract_educational_context_for_video(result["notes"])
            print(f"📝 Extracted context: {educational_context}")

            # Test full pipeline with video generation (if GEMINI_API_KEY available)
            if os.getenv("GEMINI_API_KEY"):
                print("\n🎬 Testing full pipeline with video generation...")
                full_result = process_pdf_text_to_notes(
                    sample_input, save_to_file=True, generate_video=True
                )

                if full_result.get("video_generation", {}).get("success"):
                    print("✅ Full pipeline test successful!")
                    print(
                        f"🎬 Video context: {full_result.get('educational_context_for_video', '')[:100]}..."
                    )
                else:
                    print(
                        "⚠️ Video generation test failed (expected without presenter image)"
                    )
            else:
                print("💡 Add GEMINI_API_KEY to test video generation")

        else:
            print(f"❌ Failed: {result['error']}")
