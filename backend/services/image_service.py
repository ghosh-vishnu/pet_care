import os
import cv2
import numpy as np
from typing import Tuple, List
from PIL import Image

def _calc_brightness(img: np.ndarray) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(gray.mean() / 255.0)

def _calc_clarity(img: np.ndarray) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    var_lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Normalize variance to 0..1 using soft scale
    score = 1.0 - np.exp(-var_lap / 500.0)
    return float(np.clip(score, 0.0, 1.0))

def _calc_color_balance(img: np.ndarray) -> float:
    # 1.0 = perfectly balanced channels
    chans = cv2.mean(img)[:3]  # B,G,R
    std = np.std(chans)
    max_std = 40.0
    score = 1.0 - min(std, max_std)/max_std
    return float(np.clip(score, 0.0, 1.0))

def analyze_image(path: str) -> Tuple[float, float, float, str, List[str]]:
    # Try to read image using PIL first (supports more formats like AVIF, WebP, etc.)
    try:
        pil_img = Image.open(path).convert("RGB")
        # Convert PIL image to numpy array for OpenCV
        img_array = np.array(pil_img)
        # Convert RGB to BGR for OpenCV
        img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    except Exception as e:
        # Fallback to OpenCV's imread
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Cannot read image: {str(e)}")

    brightness = _calc_brightness(img)
    clarity = _calc_clarity(img)
    color_balance = _calc_color_balance(img)

    notes = []
    health_notes = []
    
    if brightness < 0.35:
        notes.append("Image is quite dark; ensure good lighting when assessing coat/skin.")
        health_notes.append("Poor lighting may hide skin conditions or coat issues.")
    elif brightness > 0.7:
        notes.append("Image is well-lit; good for visual health assessment.")
    
    if clarity < 0.4:
        notes.append("Image appears a bit blurry; retake a sharper photo for better assessment.")
        health_notes.append("Blurry images make it difficult to assess skin, eyes, and coat condition accurately.")
    elif clarity > 0.6:
        notes.append("Image is sharp and clear; excellent for health assessment.")
    
    if color_balance < 0.6:
        notes.append("Color cast detected; natural daylight helps assess coat/skin color accurately.")
        health_notes.append("Color accuracy is important for detecting skin redness, coat discoloration, or eye issues.")

    # Enhanced health-focused summary
    summary_bits = []
    if brightness > 0.4 and clarity > 0.5 and color_balance > 0.6:
        summary_bits.append("Photo quality is excellent for health assessment.")
        summary_bits.append("Good lighting and clarity allow for better evaluation of coat, skin, eyes, and overall condition.")
    elif brightness > 0.4 and clarity > 0.5:
        summary_bits.append("Photo quality is adequate for basic health visual check.")
    else:
        summary_bits.append("Photo quality may limit accurate health assessment.")
    
    if health_notes:
        summary_bits.append("Note: " + " ".join(health_notes))
    
    summary = " ".join(summary_bits) if summary_bits else "Photo quality limitations may affect assessment."

    # Enhanced nutrition tips with health focus
    nutrition = [
        "Feed a complete, AAFCO-compliant diet appropriate for your dog's life stage and breed.",
        "Keep treats under 10% of daily calories to maintain healthy weight.",
        "Ensure fresh water is available at all times for proper hydration.",
        "Maintain a consistent feeding schedule to support digestive health.",
        "Monitor your dog's body condition score regularly - ribs should be felt but not seen.",
    ]

    return brightness, clarity, color_balance, summary, nutrition
