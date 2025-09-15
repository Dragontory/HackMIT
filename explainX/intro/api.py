"""
ExplainX PDF Processor API
FastAPI server that receives PDF processing results and generates educational content
"""

import os
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import our processor functions
from processor import (
    generate_detailed_notes,
    process_pdf_text_to_notes,
    process_pdf_and_generate_video,
    extract_educational_context_for_video,
)

# Import video generation functions
from presenter_video_service import upload_and_generate_presenter_video

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# Pydantic models matching your PDF parser client
class PDFProcessingRequest(BaseModel):
    """Model matching the exact response from your PDF parser"""

    message: str = Field(..., description="Status message from PDF processing")
    filename: str = Field(..., description="Original filename of the PDF")
    extracted_text: str = Field(..., description="Text extracted from the PDF")
    extracted_images: List[str] = Field(
        default=[], description="List of image hashes/filenames"
    )


class ProcessingOptions(BaseModel):
    """Options for processing the PDF data"""

    save_to_file: bool = Field(False, description="Whether to save notes to file")
    generate_video: bool = Field(
        False, description="Whether to generate video from notes"
    )
    output_dir: str = Field("generated_notes", description="Directory to save notes")
    presenter_image_path: str = Field(
        "Generated Image September 14, 2025 - 6_32AM.png",
        description="Path to presenter image",
    )
    max_context_length: int = Field(
        400, description="Maximum length of educational context for video"
    )


class NotesResponse(BaseModel):
    """Response model for generated notes"""

    success: bool
    error: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    notes_file_path: Optional[str] = None
    educational_context_for_video: Optional[str] = None
    video_generation: Optional[Dict[str, Any]] = None


class FullProcessingRequest(BaseModel):
    """Complete request for full processing pipeline"""

    pdf_data: PDFProcessingRequest
    options: ProcessingOptions = ProcessingOptions()


class EducationalContextResponse(BaseModel):
    """Response for educational context extraction"""

    success: bool
    notes: Optional[str] = None
    educational_context: Optional[str] = None
    context_length: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class EducationalContentRequest(BaseModel):
    """Request model for direct educational content to video generation"""

    educational_content: str = Field(
        ..., description="Educational content to convert to video"
    )
    presenter_image_path: str = Field(
        "Generated Image September 14, 2025 - 6_31AM.png",
        description="Path to presenter image (defaults to Generated Image September 14, 2025 - 6_31AM.png)",
    )
    video_length: str = Field(
        "extensive", description="Video length: extensive, medium, or short"
    )
    background_style: str = Field(
        "auto", description="Background style: auto, home_office, classroom, etc."
    )
    lighting_style: str = Field(
        "auto", description="Lighting style: auto, warm, bright, natural, etc."
    )
    clothing_style: str = Field(
        "auto", description="Clothing style: auto, professional, casual, etc."
    )


class VideoGenerationResponse(BaseModel):
    """Response for direct video generation"""

    success: bool
    error: Optional[str] = None
    operation_name: Optional[str] = None
    educational_content: Optional[str] = None
    presenter_image_path: Optional[str] = None
    video_settings: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# FastAPI application setup
app = FastAPI(
    title="ExplainX PDF Processor API",
    description="API for processing PDF text and generating educational notes with optional video generation",
    version="1.0.0",
)

# Add CORS middleware - matching your client's configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # Your PDF parser
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ExplainX PDF Processor API",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "generate_notes": "/api/generate-notes",
            "process_full": "/api/process-full",
            "extract_context": "/api/extract-context",
            "generate_video": "/api/generate-video",
            "direct_video": "/api/direct-video",
        },
    }


@app.post("/api/generate-notes", response_model=NotesResponse)
async def api_generate_notes(request: PDFProcessingRequest):
    """
    Generate detailed educational notes from PDF processing results.

    Accepts the exact response format from your PDF parser and returns
    comprehensive educational notes generated by Anthropic Claude.
    """
    try:
        # Convert Pydantic model to dict for processing
        pdf_data = request.model_dump()

        print(f"📚 Received PDF processing request for: {pdf_data['filename']}")
        print(f"📄 Text length: {len(pdf_data['extracted_text'])} characters")
        print(f"🖼️ Images count: {len(pdf_data['extracted_images'])}")

        # Generate notes using existing function
        result = generate_detailed_notes(pdf_data)

        return NotesResponse(**result)

    except Exception as e:
        print(f"❌ Error generating notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating notes: {str(e)}")


@app.post("/api/process-full", response_model=NotesResponse)
async def api_process_full(request: FullProcessingRequest):
    """
    Complete processing pipeline with options.

    Accepts PDF processing results with processing options for saving files
    and generating videos.
    """
    try:
        # Convert Pydantic models to dict
        pdf_data = request.pdf_data.model_dump()
        options = request.options.model_dump()

        print(f"🚀 Starting full processing pipeline for: {pdf_data['filename']}")
        print(
            f"⚙️ Options: save_file={options['save_to_file']}, generate_video={options['generate_video']}"
        )

        # Process with all options
        result = process_pdf_text_to_notes(
            pdf_processing_result=pdf_data,
            save_to_file=options["save_to_file"],
            generate_video=options["generate_video"],
            output_dir=options["output_dir"],
            presenter_image_path=options["presenter_image_path"],
        )

        return NotesResponse(**result)

    except Exception as e:
        print(f"❌ Error in full processing: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error in full processing: {str(e)}"
        )


@app.post("/api/extract-context", response_model=EducationalContextResponse)
async def api_extract_context(request: PDFProcessingRequest, max_length: int = 400):
    """
    Generate notes and extract educational context for video generation.

    Returns both the full notes and the extracted context suitable for video generation.
    Perfect for getting the educational context that would be sent to generate_video.py
    """
    try:
        # Convert Pydantic model to dict
        pdf_data = request.model_dump()

        print(f"🎬 Extracting educational context for: {pdf_data['filename']}")

        # Generate notes first
        notes_result = generate_detailed_notes(pdf_data)

        if not notes_result["success"]:
            return EducationalContextResponse(
                success=False, error=notes_result["error"]
            )

        # Extract educational context for video
        educational_context = extract_educational_context_for_video(
            notes_result["notes"], max_length=max_length
        )

        return EducationalContextResponse(
            success=True,
            notes=notes_result["notes"],
            educational_context=educational_context,
            context_length=len(educational_context),
            metadata=notes_result["metadata"],
            message=f"Educational context extracted successfully for {pdf_data['filename']}",
        )

    except Exception as e:
        print(f"❌ Error extracting context: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error extracting context: {str(e)}"
        )


@app.post("/api/generate-video", response_model=NotesResponse)
async def api_generate_video(request: PDFProcessingRequest):
    """
    Complete PDF-to-Video pipeline.

    This is the main endpoint for the complete workflow:
    1. Generate detailed educational notes from PDF text
    2. Extract educational context for video
    3. Generate video using the extracted context

    This endpoint does what the user requested - sends the first chunk of content
    as educational_context to the video generation system.
    """
    try:
        # Convert Pydantic model to dict
        pdf_data = request.model_dump()

        print(f"🎥 Starting complete PDF-to-Video pipeline for: {pdf_data['filename']}")

        # Run the complete pipeline
        result = process_pdf_and_generate_video(pdf_data)

        return NotesResponse(**result)

    except Exception as e:
        print(f"❌ Error in PDF-to-Video pipeline: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error in PDF-to-Video pipeline: {str(e)}"
        )


@app.post("/api/notes-and-video", response_model=NotesResponse)
async def api_notes_and_video(request: PDFProcessingRequest):
    """
    Convenience endpoint: Generate notes, save to file, and create video.

    This combines the most common workflow:
    - Generate detailed educational notes
    - Save notes to file
    - Extract educational context and generate video
    """
    try:
        pdf_data = request.dict()

        print(
            f"🎬📚 Processing {pdf_data['filename']} with notes + video generation..."
        )

        # Process with both file saving and video generation enabled
        result = process_pdf_text_to_notes(
            pdf_processing_result=pdf_data,
            save_to_file=True,
            generate_video=True,
            output_dir="generated_notes",
        )

        return NotesResponse(**result)

    except Exception as e:
        print(f"❌ Error in notes-and-video pipeline: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error in notes-and-video pipeline: {str(e)}"
        )


@app.post("/api/direct-video", response_model=VideoGenerationResponse)
async def api_direct_video_generation(request: EducationalContentRequest):
    """
    Direct educational content to video generation.

    This endpoint bypasses PDF processing and note generation, taking educational content
    directly and sending it to the video generation pipeline. This is the most direct
    path from educational content to video.

    Flow: Educational Content -> generate_video.py + presenter_video_service.py -> Background Job -> video_monitor.py
    """
    try:
        # Convert Pydantic model to dict
        content_data = request.model_dump()

        print(f"🎥 Direct video generation for educational content...")
        print(
            f"📝 Content length: {len(content_data['educational_content'])} characters"
        )
        print(f"📸 Using presenter image: {content_data['presenter_image_path']}")
        print(
            f"⚙️ Settings: {content_data['video_length']} length, {content_data['background_style']} background"
        )

        # Get API keys
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if not gemini_api_key:
            return VideoGenerationResponse(
                success=False,
                error="GEMINI_API_KEY environment variable required for video generation",
            )

        # Check if presenter image exists
        presenter_image_path = content_data["presenter_image_path"]
        if not os.path.exists(presenter_image_path):
            return VideoGenerationResponse(
                success=False,
                error=f"Presenter image not found: {presenter_image_path}. Please ensure the image file exists.",
            )

        print(f"🚀 Starting video generation with presenter_video_service...")

        # Call video generation directly
        video_result = upload_and_generate_presenter_video(
            api_key=gemini_api_key,
            local_image_path=presenter_image_path,
            educational_context=content_data["educational_content"],
            intro_prompt=None,  # Will be generated dynamically
            video_length=content_data["video_length"],
            background_style=content_data["background_style"],
            lighting_style=content_data["lighting_style"],
            clothing_style=content_data["clothing_style"],
            wait_for_completion=False,  # Don't wait - use background job
            background_wait_minutes=15,  # Check after 15 minutes
            anthropic_api_key=anthropic_api_key,
        )

        if video_result.success:
            print(f"✅ Video generation started successfully!")
            print(f"🆔 Operation: {video_result.operation_name}")
            print(f"📁 Video will be saved to: generated_videos/")
            print(f"⏰ Automatic download will start in 15 minutes")

            return VideoGenerationResponse(
                success=True,
                operation_name=video_result.operation_name,
                educational_content=content_data["educational_content"],
                presenter_image_path=presenter_image_path,
                video_settings={
                    "video_length": content_data["video_length"],
                    "background_style": content_data["background_style"],
                    "lighting_style": content_data["lighting_style"],
                    "clothing_style": content_data["clothing_style"],
                },
                message=f"Video generation started. Operation: {video_result.operation_name}",
            )
        else:
            print(f"❌ Video generation failed: {video_result.error_message}")
            return VideoGenerationResponse(
                success=False,
                error=f"Video generation failed: {video_result.error_message}",
            )

    except Exception as e:
        print(f"❌ Error in direct video generation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error in direct video generation: {str(e)}"
        )


def start_api_server(host: str = "127.0.0.1", port: int = 8001, reload: bool = True):
    """
    Start the FastAPI server for the processor.

    Note: Using port 8001 to avoid conflict with your PDF parser on port 8000
    """
    print(f"🚀 Starting ExplainX PDF Processor API server on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Interactive API: http://{host}:{port}/redoc")
    print(f"💡 Your PDF parser should send requests to: http://{host}:{port}/api/")
    print(
        f"🎯 Main endpoint for video generation: http://{host}:{port}/api/generate-video"
    )

    uvicorn.run("api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    import sys

    # Check if user wants to specify port
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

    print("🧪 ExplainX PDF Processor API")
    print("=" * 50)
    print("📋 Available endpoints:")
    print("  • /api/generate-notes    - Generate detailed notes only")
    print("  • /api/extract-context   - Generate notes + extract video context")
    print("  • /api/generate-video    - Complete PDF-to-Video pipeline")
    print("  • /api/notes-and-video   - Notes + Video (convenience endpoint)")
    print("  • /api/process-full      - Full pipeline with custom options")
    print("  • /api/direct-video      - Direct educational content to video (NEW!)")
    print()

    start_api_server(port=port)
