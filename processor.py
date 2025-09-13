import os
import httpx  # A modern, async-friendly HTTP client library
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import uvicorn

# --- 1. DEFINE APP AND DATA MODELS ---

app = FastAPI(
    title="AI Content Processing API",
    description="Receives parsed text and images, and uses an LLM to filter and categorize the content.",
    version="1.0.0",
)

# This model defines the expected INPUT for our /process endpoint
# It matches the OUTPUT of your parser.py
class ProcessingRequest(BaseModel):
    filename: str
    extracted_text: str
    extracted_images: List[str] # List of image hashes

# This model defines the OUTPUT of our /process endpoint
class ProcessingResponse(BaseModel):
    summary: str = Field(..., description="A concise summary of the essential text content.")
    relevant_images: List[str] = Field(..., description="A list of image hashes deemed relevant to the summary.")

# --- 2. CONFIGURE GEMINI API CALL ---

# IMPORTANT: In a real project, use environment variables for API keys!
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# --- 3. THE CORE LOGIC: PROMPTING THE LLM ---

async def get_ai_filtered_content(text: str, image_hashes: List[str]) -> (str, List[str]):
    """
    Calls the Gemini API to analyze and filter the parsed content.
    """
    if not image_hashes:
        image_list_str = "No images were provided."
    else:
        image_list_str = ", ".join(image_hashes)

    # This is the "magic". A well-crafted prompt is crucial for good results.
    prompt = f"""
    You are an expert educational content analyst. Your task is to distill raw text and a list of associated image identifiers from a student's notes into a concise summary and a list of essential visuals for creating an educational video.

    Here is the raw text extracted from the document:
    ---
    {text}
    ---

    Here is the list of available image identifiers (perceptual hashes):
    ---
    {image_list_str}
    ---

    Perform the following two tasks:
    1.  **Summarize the Text:** Read through the entire text and create a clean, concise summary of the core educational concepts. You MUST identify and remove any content that is not central to the topic, such as page numbers, headers, footers, citations, bibliographies, irrelevant conversational fluff, or repeated phrases. The summary should be well-structured and easy to understand.
    2.  **Select Relevant Images:** Based on your summary, determine which of the provided image identifiers correspond to visuals that are essential for understanding the material. An essential image is a diagram, graph, chart, or a key illustration. Do NOT include images that are likely decorative, logos, or irrelevant to the main topics.

    Your final output MUST be a valid JSON object with ONLY the following two keys:
    - "summary": A string containing your cleaned-up summary.
    - "relevant_images": A JSON array of strings, where each string is an identifier of an essential image from the provided list.
    """

    # For a true multimodal call, you would send image bytes. For now, the LLM will use the text context
    # to infer which images might be important, which is a very effective strategy.
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload)
            response.raise_for_status()  # Raises an exception for 4xx or 5xx status codes
            
            # Extract the text, which should be our JSON string
            result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            # The response from the LLM is a string that we need to parse into a JSON object
            import json
            processed_data = json.loads(result_text)
            
            summary = processed_data.get("summary", "")
            relevant_images = processed_data.get("relevant_images", [])
            
            return summary, relevant_images

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Error from AI Service: {e.response.text}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")


# --- 4. API ENDPOINT ---

@app.post("/process", response_model=ProcessingResponse)
async def process_content(request: ProcessingRequest):
    """
    Receives parsed PDF data, sends it to an LLM for filtering and categorization,
    and returns the cleaned-up content.
    """
    if not request.extracted_text.strip():
        raise HTTPException(status_code=400, detail="Extracted text cannot be empty.")
        
    summary, relevant_images = await get_ai_filtered_content(request.extracted_text, request.extracted_images)
    
    return ProcessingResponse(
        summary=summary,
        relevant_images=relevant_images
    )

# --- 5. RUN THE APP ---
if __name__ == "__main__":
    uvicorn.run("processor:app", host="127.0.0.1", port=8001, reload=True) # Running on a different port
