#!/usr/bin/env python3
"""
Enhanced Chunked Pipeline - Process content in focused chunks for comprehensive coverage.
Each chunk generates detailed video content, then all videos are combined.
"""

import os
import sys
import json
import time
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Add the generator package to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from generator.agents.client_openai import OpenAIClient, GenerationConfig
    from generator.compiler import compile_scene_enhanced, CompileOptions
    from generator.compiler.assets import StaticAssetResolver
    from generator.style.provider import StylePackProvider
    from generator.style.models import StylePack, ColorPalette, Typography
    from dotenv import load_dotenv
    from openai import OpenAI
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()


# Pydantic models for structured output
class StyleOverride(BaseModel):
    """Style override settings."""

    font_size: Optional[float] = Field(default=None, description="Font size override")
    text_color: Optional[str] = Field(default=None, description="Text color override")
    position: Optional[str] = Field(default=None, description="Position override")


class DSLOperation(BaseModel):
    """Single operation in a scene timeline."""

    type: str = Field(
        description="Operation type: 'text', 'math', 'list', 'visualization'"
    )
    content: str = Field(description="Main content for the operation")
    duration_s: Optional[float] = Field(default=5.0, description="Duration in seconds")
    style: Optional[StyleOverride] = Field(default=None, description="Style overrides")


class SceneDSL(BaseModel):
    """Complete Scene DSL structure."""

    scene_id: str = Field(description="Unique scene identifier")
    title: str = Field(description="Scene title")
    duration_s: float = Field(description="Total scene duration in seconds")
    operations: List[DSLOperation] = Field(description="List of operations to perform")


class ChunkCourseDSL(BaseModel):
    """Video course for a single content chunk."""

    chunk_id: str = Field(description="Unique chunk identifier")
    title: str = Field(description="Chunk title")
    total_duration_s: float = Field(description="Total chunk duration")
    scenes: List[SceneDSL] = Field(description="List of scenes in this chunk")


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print("=" * 80)


def chunk_content(content: str, chunk_size: int = 3000) -> List[Dict[str, str]]:
    """
    Split content into focused chunks for better model processing.

    Args:
        content: Full content text
        chunk_size: Target characters per chunk

    Returns:
        List of chunk dictionaries with metadata
    """
    print_header("Content Chunking Strategy")

    # Split by major sections/paragraphs first
    paragraphs = content.split("\n\n")

    chunks = []
    current_chunk = ""
    chunk_num = 1

    for para in paragraphs:
        # If adding this paragraph would exceed chunk size and we have content
        if len(current_chunk + para) > chunk_size and current_chunk:
            # Save current chunk
            chunk_title = extract_chunk_title(current_chunk, chunk_num)
            chunks.append(
                {
                    "chunk_id": f"chunk_{chunk_num:02d}",
                    "title": chunk_title,
                    "content": current_chunk.strip(),
                    "char_count": len(current_chunk),
                }
            )

            print(f"📦 Chunk {chunk_num}: {chunk_title} ({len(current_chunk)} chars)")

            # Start new chunk
            current_chunk = para + "\n\n"
            chunk_num += 1
        else:
            current_chunk += para + "\n\n"

    # Add final chunk if there's content
    if current_chunk.strip():
        chunk_title = extract_chunk_title(current_chunk, chunk_num)
        chunks.append(
            {
                "chunk_id": f"chunk_{chunk_num:02d}",
                "title": chunk_title,
                "content": current_chunk.strip(),
                "char_count": len(current_chunk),
            }
        )
        print(f"📦 Chunk {chunk_num}: {chunk_title} ({len(current_chunk)} chars)")

    print(f"\n✅ Split content into {len(chunks)} focused chunks")
    total_chars = sum(chunk["char_count"] for chunk in chunks)
    avg_chars = total_chars / len(chunks) if chunks else 0
    print(f"📊 Total: {total_chars} chars, Average: {avg_chars:.0f} chars per chunk")

    return chunks


def extract_chunk_title(content: str, chunk_num: int) -> str:
    """Extract a meaningful title from chunk content."""
    lines = content.strip().split("\n")

    # Look for numbered sections or headers
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("#") or len(line) < 50):
            # Clean up title
            title = line.replace("#", "").strip()
            if len(title) > 60:
                title = title[:60] + "..."
            return title

    # Fallback: use first meaningful sentence
    for line in lines:
        line = line.strip()
        if len(line) > 20 and len(line) < 80:
            return line[:60] + "..." if len(line) > 60 else line

    # Final fallback
    return f"Transformers & Attention - Part {chunk_num}"


def generate_chunk_course_dsl(chunk: Dict[str, str]) -> Dict[str, Any]:
    """Generate comprehensive course DSL for a single content chunk."""
    print_header(f"GPT-5 Generation: {chunk['title']}")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        return {}

    print(f"🎯 Processing chunk: {chunk['chunk_id']}")
    print(f"📚 Title: {chunk['title']}")
    print(f"📊 Content: {chunk['char_count']} characters")

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.parse(
            model="gpt-5",
            input=[
                {
                    "role": "system",
                    "content": """You are an expert educational video creator. Generate a comprehensive video course DSL for this specific content chunk.

Create 2-3 detailed scenes that thoroughly cover the content:
- Scene 1: Introduction and core concepts (120-180 seconds)  
- Scene 2: Mathematical details and formulations (120-180 seconds)
- Scene 3: Applications and examples (90-120 seconds)

For each scene, create 6-8 operations with these types:
- "text": Clear explanations (5-7 seconds each, use for main concepts)
- "math": Mathematical formulas with LaTeX (7-10 seconds each)  
- "list": Key points and bullet lists (6-8 seconds each)
- "visualization": Integrated visual explanations (8-12 seconds each)

Make each operation substantial with detailed content. Total target: 8-12 minutes per chunk.
Use proper LaTeX notation and ensure educational progression.""",
                },
                {
                    "role": "user",
                    "content": f"""Create a comprehensive educational video course for this content chunk:

Title: {chunk['title']}

Content:
{chunk['content']}

Generate detailed scenes with substantial operations that thoroughly explain the concepts. Focus on educational clarity and mathematical rigor.""",
                },
            ],
            text_format=ChunkCourseDSL,
        )

        chunk_dsl = response.output_parsed

        print(f"\n🎉 Generated Course DSL for {chunk['chunk_id']}!")
        print(f"📊 Structure:")
        print(f"   Title: {chunk_dsl.title}")
        print(
            f"   Duration: {chunk_dsl.total_duration_s}s ({chunk_dsl.total_duration_s/60:.1f} minutes)"
        )
        print(f"   Scenes: {len(chunk_dsl.scenes)}")

        total_ops = sum(len(scene.operations) for scene in chunk_dsl.scenes)
        print(f"   Total Operations: {total_ops}")

        for i, scene in enumerate(chunk_dsl.scenes, 1):
            print(
                f"     Scene {i}: {scene.title} ({scene.duration_s}s, {len(scene.operations)} ops)"
            )

        return chunk_dsl.model_dump()

    except Exception as e:
        print(f"❌ GPT-5 generation failed for chunk {chunk['chunk_id']}: {e}")
        import traceback

        traceback.print_exc()
        return {}


def main():
    """Run the enhanced chunked pipeline."""
    start_time = time.time()

    print_header("Enhanced Chunked ExplainX Pipeline")
    print(
        "🎯 Strategy: Content Chunking → Focused DSL → Comprehensive Videos → Final Assembly"
    )
    print("📚 Content: Transformers and Attention Mechanisms")
    print("⏱️ Target: 8-12 minutes per chunk for comprehensive coverage")

    # Step 1: Read and chunk content
    content_file = ROOT / "testfile.txt"
    if not content_file.exists():
        print("❌ testfile.txt not found!")
        return

    content = content_file.read_text()
    print(f"\n📖 Original content: {len(content)} characters")

    # Chunk the content
    chunks = chunk_content(
        content, chunk_size=2500
    )  # Smaller chunks for focused processing

    if not chunks:
        print("❌ No chunks created!")
        return

    # Step 2: Process each chunk
    all_chunk_dsls = []
    chunk_videos = []

    for i, chunk in enumerate(chunks, 1):
        print(f"\n{'='*60}")
        print(f"Processing Chunk {i}/{len(chunks)}: {chunk['title']}")
        print(f"{'='*60}")

        # Generate DSL for this chunk
        chunk_dsl = generate_chunk_course_dsl(chunk)

        if chunk_dsl:
            all_chunk_dsls.append(chunk_dsl)

            # Save chunk DSL
            output_dir = ROOT / "generated_dsl" / "chunks"
            output_dir.mkdir(parents=True, exist_ok=True)

            chunk_file = output_dir / f"{chunk['chunk_id']}_course.json"
            with chunk_file.open("w") as f:
                json.dump(chunk_dsl, f, indent=2)

            print(f"💾 Chunk DSL saved: {chunk_file}")
        else:
            print(f"⚠️ Skipping chunk {chunk['chunk_id']} due to generation failure")

    # Summary
    total_time = time.time() - start_time
    total_scenes = sum(len(dsl.get("scenes", [])) for dsl in all_chunk_dsls)
    total_duration = sum(dsl.get("total_duration_s", 0) for dsl in all_chunk_dsls)

    print_header("📊 Chunked Pipeline Summary")
    print(f"✅ Processed {len(chunks)} content chunks")
    print(f"✅ Generated {len(all_chunk_dsls)} course DSLs")
    print(f"✅ Total scenes: {total_scenes}")
    print(
        f"✅ Total estimated duration: {total_duration:.0f}s ({total_duration/60:.1f} minutes)"
    )
    print(f"⏱️ Processing time: {total_time:.1f} seconds")

    if all_chunk_dsls:
        print(f"\n🎬 Next steps:")
        print(f"   1. Compile each chunk DSL to Manim code")
        print(f"   2. Render individual chunk videos")
        print(f"   3. Concatenate all chunks into final comprehensive course")
        print(
            f"   4. Target final video: {total_duration/60:.1f} minutes of educational content"
        )

    return all_chunk_dsls


if __name__ == "__main__":
    main()
