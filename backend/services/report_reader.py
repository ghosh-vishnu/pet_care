import io
from PIL import Image
from pdfminer.high_level import extract_text_to_fp
from .llm_service import generate_dynamic_answer # Re-use your LLM service
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def analyze_health_report(file_data: bytes, file_mime_type: str) -> dict:
    """
    Extracts text from a report file and uses the LLM to analyze it.
    """
    report_text = ""
    
    # --- 1. Extract Text from File ---
    if 'pdf' in file_mime_type:
        # Use pdfminer to extract text from the PDF byte stream
        try:
            output = io.StringIO()
            with io.BytesIO(file_data) as pdf_file:
                extract_text_to_fp(pdf_file, output)
            report_text = output.getvalue()
        except Exception as e:
            return {"error": "Failed to read PDF content.", "detail": str(e)}

    elif 'image' in file_mime_type:
        # Placeholder for OCR on images (Requires a library like pytesseract or cloud API)
        # For simplicity now, we'll ask the user to input text if image OCR fails.
        try:
            # 1. Open the image bytes using PIL
            img = Image.open(io.BytesIO(file_data))
            
            # 2. Use pytesseract to extract text (OCR)
            report_text = pytesseract.image_to_string(img)
            
            if not report_text.strip():
                 return {"error": "OCR failed to find text in the image.", "detail": "Image may be too blurry or low resolution."}

        except pytesseract.TesseractNotFoundError:
            return {"error": "Tesseract not installed.", "detail": "Tesseract OCR is required for image analysis but was not found. Please install the Tesseract executable."}
        except Exception as e:
            return {"error": "Image report analysis failed.", "detail": str(e)}
    
    else:
        return {"error": "Unsupported file type for report analysis.", "detail": file_mime_type}

    if not report_text.strip():
        return {"error": "Report is empty or text extraction failed.", "detail": "No text found."}

    # --- 2. LLM Analysis ---
    # Construct a specific prompt to force the LLM to analyze the medical text
    analysis_prompt = (
        f"You are a **Certified Veterinary Assistant AI**."
        f"Your task is to analyze the following vet or lab report text. "
        f"Follow these steps precisely:\n"
        f"1. **SUMMARY:** Provide a clear, concise summary of the major findings (diagnosis, key results, overall health). Be reassuring and professional.\n"
        f"2. **TIPS:** Based *only* on the report, provide 3-5 practical, easy-to-follow care tips, lifestyle changes, or next-step recommendations for the pet owner. Do not suggest diagnosis, only care/follow-up.\n"
        f"3. **Format:** Present your analysis using bold headings for the SUMMARY and TIPS sections.\n\n"
        f"--- REPORT TEXT TO ANALYZE ---\n{report_text[:4000]}" # Limit text length for API
    )
    
    try:
        # Use your existing LLM function but with a specialized analysis prompt
        analysis_response = generate_dynamic_answer(
            user_msg=analysis_prompt, 
            history=[], 
            location=None, 
            pet_profile=None # No pet profile needed for raw analysis
        )
        
        return {
            "type": "report_analysis",
            "summary": "Report successfully analyzed.",
            "report_text": report_text[:500],
            "analysis_result": analysis_response
        }
    except Exception as e:
        return {"error": "LLM analysis failed.", "detail": str(e)}