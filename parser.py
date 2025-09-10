import os
import shutil
import fitz  # PyMuPDF
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
from typing import List
import uvicorn

# Initialize the FastAPI app
app = FastAPI(
    title="PDF Parsing API",
    description="Upload a PDF to extract text and images.",
    version="1.0.0",
)

# Pydantic model 
class PDFParseResponse(BaseModel):
    message: str = Field(..., description="A status message confirming the outcome.")
    filename: str = Field(..., description="The original name of the uploaded file.")
    extracted_text: str = Field(..., description="All the text extracted from the PDF.")
    extracted_images: List[str] = Field(..., description="A list of filenames for the extracted images.")

# Define the folder for temporary uploads and extracted images
UPLOAD_FOLDER = "temp_uploads"



# Helper Functions

@app.on_event("startup")
async def startup_event():
    """Create the upload directory when the app starts."""
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER)


# API Endpoints

@app.post("/upload", response_model=PDFParseResponse)
async def upload_and_parse_pdf(file: UploadFile = File(...)):
    """
    Receives a PDF file, saves it temporarily, extracts all text and images,
    and returns the data in a structured JSON response.
    """
    # File validation
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

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
                
                # Create a unique filename for each image
                image_filename = f"image_p{page_num + 1}_{img_index + 1}.{image_ext}"
                image_save_path = os.path.join(UPLOAD_FOLDER, image_filename)
                
                with open(image_save_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                image_files.append(image_filename)

        doc.close()

        return PDFParseResponse(
            message="PDF processed successfully",
            filename=file.filename,
            extracted_text=full_text,
            extracted_images=image_files,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    finally:
        await file.close()
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


# Run using "uvicorn parser:app --host 0.0.0.0 --port 8000 --reload"
# or "python parser.py" for local testing
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)