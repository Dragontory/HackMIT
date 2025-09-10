import requests
import os

API_URL = "http://127.0.0.1:8000/upload"

# Dummy PDF
PDF_FILE_PATH = "Sample.pdf"

def create_dummy_pdf():
    """Creates a simple PDF for testing purposes if one doesn't exist."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        if not os.path.exists(PDF_FILE_PATH):
            print(f"'{PDF_FILE_PATH}' not found. Creating a dummy PDF for testing.")
            c = canvas.Canvas(PDF_FILE_PATH, pagesize=letter)
            c.drawString(100, 750, "This is a test PDF document.")
            c.drawString(100, 730, "It contains some sample text for the parser.")
            c.save()
            print("Dummy PDF created.")
    except ImportError:
        print("\n---")
        print("WARNING: `reportlab` is not installed. Cannot create a dummy PDF.")
        print(f"Please manually create a file named '{PDF_FILE_PATH}' to run this test.")
        print("You can install it with: pip install reportlab")
        print("---\n")
        return False
    return True

def test_pdf_upload():
    """
    Sends a POST request with a PDF file to the API endpoint and prints the response.
    """
    if not os.path.exists(PDF_FILE_PATH):
        if not create_dummy_pdf():
            return # Stop if dummy PDF can't be created and no file exists

    print(f"Testing PDF upload with file: '{PDF_FILE_PATH}'")
    
    try:
        # Open the PDF file in read mode
        with open(PDF_FILE_PATH, 'rb') as f:
            files = {'file': (os.path.basename(PDF_FILE_PATH), f, 'application/pdf')}
            
            # Send the request
            response = requests.post(API_URL, files=files)

        print("\n--- Test Results ---")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Response JSON:")
            import json
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error Response:")
            print(response.text)
            
    except requests.exceptions.ConnectionError as e:
        print("\n--- CONNECTION ERROR ---")
        print(f"Could not connect to the API at {API_URL}.")
        print("Please make sure the FastAPI server is running.")
        print("You can start it by running 'uvicorn main:app --reload' in your terminal.")
    except FileNotFoundError:
        print(f"\n--- FILE NOT FOUND ---")
        print(f"The file '{PDF_FILE_PATH}' does not exist.")
        print("Please place a sample PDF in the same directory as this script.")

if __name__ == "__main__":
    test_pdf_upload()