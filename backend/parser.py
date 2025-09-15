import os
import shutil
import fitz  # PyMuPDF
import hashlib
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware  # Import CORS Middleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import imagehash
from PIL import Image
import io
from fastapi.staticfiles import StaticFiles
import sys

# Add the intro directory to Python path to import processor
sys.path.append(os.path.join(os.path.dirname(__file__), "../../intro"))
try:
    from processor import process_pdf_text_to_notes
except ImportError as e:
    print(f"Warning: Could not import processor: {e}")
    process_pdf_text_to_notes = None

# Initialize the FastAPI app
app = FastAPI(
    title="PDF Parsing API",
    description="Upload a PDF to extract text and images with perceptual hashing.",
    version="1.1.0",
)

# --- CRITICAL: ADD CORS MIDDLEWARE ---
# This allows your React frontend (running on a different port)
# to make requests to this backend.
origins = [
    "http://localhost:5173",  # The default Vite dev server port
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # A common alternative
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Static Files for Images ---
UPLOAD_FOLDER = "temp_uploads"

# Mount the temp_uploads folder to serve static files
app.mount("/temp_uploads", StaticFiles(directory=UPLOAD_FOLDER), name="temp_uploads")


# --- Pydantic Models ---
class PDFParseResponse(BaseModel):
    message: str = Field(..., description="A status message confirming the outcome.")
    filename: str = Field(..., description="The original name of the uploaded file.")
    extracted_text: str = Field(..., description="All the text extracted from the PDF.")
    extracted_images: List[str] = Field(
        ..., description="A list of image hashes for the extracted images."
    )
    processed_notes: Optional[str] = Field(
        default=None, description="Generated educational notes from the extracted text."
    )
    processing_metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata about the processing results."
    )
    processing_error: Optional[str] = Field(
        default=None, description="Error message if processing failed."
    )


# --- Helper Functions & Setup ---
UPLOAD_FOLDER = "temp_uploads"


@app.on_event("startup")
async def startup_event():
    """Create the upload directory when the app starts."""
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER)


def get_perceptual_hash(image_bytes: bytes) -> str:
    """Calculates the pHash of an image from its bytes."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return str(imagehash.phash(image))
    except Exception as e:
        print(f"Warning: Could not hash an image. Error: {e}")
        # Return a hash of the bytes as a fallback
        return hashlib.sha256(image_bytes).hexdigest()


# --- API Endpoint ---
@app.post("/upload", response_model=PDFParseResponse)
async def upload_and_parse_pdf(
    file: UploadFile = File(...), voice: str = Form(...), goDeeper: str = Form(...)
):

    print(f"Received voice selection: {voice}")
    print(f"Go Deeper option: {goDeeper}")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a PDF."
        )

    temp_pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)

    try:
        # Save the uploaded PDF temporarily
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse the PDF
        doc = fitz.open(temp_pdf_path)
        full_text = ""
        image_filenames = set()  # Use a set to store full filenames

        for page in doc:
            full_text += page.get_text("text") + "\n\n"

            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                p_hash = get_perceptual_hash(image_bytes)

                image_ext = base_image["ext"]
                image_filename = f"{p_hash}.{image_ext}"

                # Check if we've already processed an image with this content
                if image_filename not in image_filenames:
                    image_filenames.add(image_filename)
                    image_save_path = os.path.join(UPLOAD_FOLDER, image_filename)

                    # Save the image only if it doesn't already exist
                    if not os.path.exists(image_save_path):
                        with open(image_save_path, "wb") as img_file:
                            img_file.write(image_bytes)

        doc.close()

        # Prepare data for processor
        pdf_processing_result = {
            "message": "PDF processed successfully",
            "filename": file.filename,
            "extracted_text": full_text,
            "extracted_images": list(image_filenames),
        }

        # Initialize response fields
        processed_notes = None
        processing_metadata = None
        processing_error = None

        # Process with educational notes generator if available
        if process_pdf_text_to_notes and full_text.strip():
            try:
                print("🧠 Generating educational notes...")
                processing_result = process_pdf_text_to_notes(
                    pdf_processing_result=pdf_processing_result,
                    save_to_file=True,
                    output_dir="../../intro/generated_notes",  # Save to intro directory
                    generate_video=False,  # Don't generate video by default
                )

                if processing_result.get("success"):
                    processed_notes = processing_result.get("notes")
                    processing_metadata = processing_result.get("metadata")
                    print("✅ Educational notes generated successfully!")
                else:
                    processing_error = processing_result.get("error")
                    print(f"❌ Note generation failed: {processing_error}")

            except Exception as e:
                processing_error = f"Error in note processing: {str(e)}"
                print(f"❌ Processing error: {processing_error}")

        return PDFParseResponse(
            message="PDF processed successfully",
            filename=file.filename,
            extracted_text=full_text,
            extracted_images=list(image_filenames),
            processed_notes=processed_notes,
            processing_metadata=processing_metadata,
            processing_error=processing_error,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        await file.close()
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


if __name__ == "__main__":
    uvicorn.run("parser:app", host="127.0.0.1", port=8000, reload=True)
