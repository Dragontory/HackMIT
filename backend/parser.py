import os
import shutil
import fitz  # PyMuPDF
import hashlib
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Import CORS Middleware
from pydantic import BaseModel, Field
from typing import List
import uvicorn
import imagehash
from PIL import Image
import io
from fastapi.staticfiles import StaticFiles

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
    "http://localhost:5173", # The default Vite dev server port
    "http://127.0.0.1:5173",
    "http://localhost:3000", # A common alternative
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
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
    extracted_images: List[str] = Field(..., description="A list of image hashes for the extracted images.")

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
async def upload_and_parse_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    temp_pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    try:
        # Save the uploaded PDF temporarily
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse the PDF
        doc = fitz.open(temp_pdf_path)
        full_text = ""
        image_hashes = set() # Use a set to automatically handle duplicates

        for page in doc:
            full_text += page.get_text("text") + "\n\n"
            
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Get the perceptual hash
                p_hash = get_perceptual_hash(image_bytes)
                
                if p_hash not in image_hashes:
                    image_hashes.add(p_hash)
                    image_ext = base_image["ext"]
                    image_save_path = os.path.join(UPLOAD_FOLDER, f"{p_hash}.{image_ext}")
                    
                    # Save the image only if it doesn't already exist
                    if not os.path.exists(image_save_path):
                        with open(image_save_path, "wb") as img_file:
                            img_file.write(image_bytes)

        doc.close()

        return PDFParseResponse(
            message="PDF processed successfully",
            filename=file.filename,
            extracted_text=full_text,
            extracted_images=list(image_hashes),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        await file.close()
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

if __name__ == "__main__":
    uvicorn.run("parser:app", host="127.0.0.1", port=8000, reload=True)
