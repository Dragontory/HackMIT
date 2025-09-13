import os
import shutil
import fitz  # PyMuPDF
import hashlib  # hash
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
from typing import List
import uvicorn

# Initialize the FastAPI app
app = FastAPI(
    title="PDF Parsing API",
    description="Upload a PDF to extract text and images with hashed filenames.",
    version="2.1.0",
)

# Pydantic model


class PDFParseResponse(BaseModel):
    message: str = Field(...,
                         description="A status message confirming the outcome.")
    filename: str = Field(...,
                          description="The original name of the uploaded file.")
    extracted_text: str = Field(...,
                                description="All the text extracted from the PDF.")
    extracted_images: List[str] = Field(
        ..., description="A list of hashed filenames for any extracted images.")


# Define the folder for temporary uploads and extracted images
UPLOAD_FOLDER = "temp_uploads"

# Helper Functions


@app.on_event("startup")
async def startup_event():
    """Create the upload directory when the app starts."""
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER)


def hash_image_bytes(image_bytes: bytes) -> str:
    """Generates a SHA256 hash for a given byte string."""
    return hashlib.sha256(image_bytes).hexdigest()


# API Endpoints

@app.post("/upload", response_model=PDFParseResponse)
async def upload_and_parse_pdf(file: UploadFile = File(...)):
    """
    Receives a PDF file, saves it temporarily, extracts all text and images,
    and returns the data in a structured JSON response.
    """
    # File validation
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a PDF.")

    temp_pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)

    try:
        # Save the uploaded PDF temporarily
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse the PDF using PyMuPDF
        doc = fitz.open(temp_pdf_path)
        full_text = ""
        image_files = []

        # Iterate through each page of the PDF
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Extract Text
            full_text += page.get_text("text") + "\n\n"

            # Extract Images
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Hash
                image_hash = hash_image_bytes(image_bytes)
                hashed_filename = f"{image_hash}.{image_ext}"
                image_save_path = os.path.join(UPLOAD_FOLDER, hashed_filename)

                # Save the image only if it doesn't already exist
                if not os.path.exists(image_save_path):
                    with open(image_save_path, "wb") as img_file:
                        img_file.write(image_bytes)

                # Add the hashed name to the list
                if hashed_filename not in image_files:
                    image_files.append(hashed_filename)

        doc.close()

        return PDFParseResponse(
            message="PDF processed successfully",
            filename=file.filename,
            extracted_text=full_text,
            extracted_images=image_files,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process PDF: {str(e)}")

    finally:
        await file.close()
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


# Run using "uvicorn parser:app --reload"
# or "python parser.py" for local testing
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
