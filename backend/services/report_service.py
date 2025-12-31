import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import SimpleDocTemplate, Spacer
from reportlab.lib.utils import ImageReader
from typing import List, Dict
from .storage import REPORT_DIR, register_report
from fastapi import HTTPException
from services.dog_detector import is_dog_image
from services.breed_classifier import predict_breed
from services.health_advice import get_health_report



def _wrap_line(text: str, width: int) -> List[str]:
    """Word-wrap helper for long lines in PDF"""
    words = text.split()
    out, line = [], []
    for w in words:
        if len(" ".join(line + [w])) > width:
            out.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        out.append(" ".join(line))
    return out


def analyze_dog_image(image_path: str) -> dict:
    # Step 1: Detect dog
    if not is_dog_image(image_path):
        raise HTTPException(status_code=400, detail="No dog detected in image")

    # Step 2: Predict breed (now includes confidence)
    breed, confidence = predict_breed(image_path)

    # Step 3: Generate health report
    report = get_health_report(breed)

    return {
        "breed": breed,
        "breed_confidence": confidence,
        "health_report": report
    }


def create_session_report_pdf(session_id: str, data: Dict) -> str:
    """
    Generate a PDF report for a single session safely,
    handling different chat history formats.
    """
    filename = f"{session_id}.pdf"
    filepath = os.path.join(REPORT_DIR, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    w, h = A4
    y = h - 72

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, y, f"Dog Health AI Report (Session {session_id})")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(72, y, "This report covers only this session.")
    y -= 32

    # --- Image Analyses ---
    analyses = data.get("image_history", [])
    if analyses:
        for idx, item in enumerate(analyses, 1):
            c.setFont("Helvetica-Bold", 14)
            c.drawString(72, y, f"Image Analysis {idx}")
            y -= 20

            # ✅ fallback: use image_path if present, else filename
            image_path = item.get("image_path") or item.get("filename")

            if image_path and os.path.exists(image_path):
                try:

                    img = ImageReader(image_path)
                    iw, ih = img.getSize()
                    max_width, max_height = 3*inch, 3*inch
                    scale = min(max_width/iw, max_height/ih, 1.0)
                    iw, ih = iw*scale, ih*scale

                    if y - ih < 100:  # new page if not enough space
                        c.showPage()
                        y = h - 72
                    c.drawImage(img, 72, y-ih, width=iw, height=ih)
                    y -= ih + 10
                except Exception as e:
                    c.setFont("Helvetica-Oblique", 9)
                    c.drawString(72, y, f"[Could not render image: {e}]")
                    y -= 14

            # Analysis text
            analysis = item.get("analysis", {})
            c.setFont("Helvetica", 10)
            for k, v in analysis.items():
                for wrap in _wrap_line(f"{k}: {v}", 90):
                    c.drawString(72, y, wrap)
                    y -= 14
            y -= 10
            if y < 150:
                c.showPage()
                y = h - 72

    # --- Chat History (FIXED) ---
    chats = data.get("chat_history", [])
    if chats:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, "Chat History")
        y -= 20

        for item in chats:
            # Safely check if the item is a dictionary with role and text
            if not isinstance(item, dict) or 'role' not in item or 'text' not in item:
                continue 

            # Normalize role for display and set color
            role_key = item['role'].lower()
            content = item['text']
            
            if role_key == "user" or role_key == "human":
                role_label = "User"
                color_rgb = (0, 0, 0) # Black
            elif role_key == "assistant" or role_key == "bot":
                role_label = "Assistant"
                color_rgb = (0.2, 0.2, 0.7) # Dark Blue
            else:
                role_label = role_key.capitalize()
                color_rgb = (0.3, 0.3, 0.3) # Gray

            c.setFillColorRGB(*color_rgb) 
            
            # Start line with bold role
            ln_prefix = f"[{role_label}]: "
            is_first_line = True
            
            # Word wrap the content using the _wrap_line helper
            for wrap in _wrap_line(content, 90):
                if y < 72:
                    c.showPage()
                    y = h - 72
                
                # Draw the prefix only on the first line
                full_line = ""
                if is_first_line:
                    c.setFont("Helvetica-Bold", 10)
                    full_line = ln_prefix
                    is_first_line = False
                else:
                    c.setFont("Helvetica", 10)
                    full_line = " " * len(ln_prefix)
                        
                c.drawString(72, y, full_line + wrap)
                y -= 14
            
            c.setFillColorRGB(0, 0, 0) # Reset color to black
            y -= 6 # Small space between messages
            
            if y < 72:
                c.showPage()
                y = h - 72

    c.showPage()
    c.save()
    return filepath
