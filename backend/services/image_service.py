import os
import cv2
import numpy as np
from typing import Tuple, List

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
    img = cv2.imread(path)
    if img is None:
        raise ValueError("Cannot read image")

    brightness = _calc_brightness(img)
    clarity = _calc_clarity(img)
    color_balance = _calc_color_balance(img)

    notes = []
    if brightness < 0.35:
        notes.append("Image is quite dark; ensure good lighting when assessing coat/skin.")
    if clarity < 0.4:
        notes.append("Image appears a bit blurry; retake a sharper photo for better assessment.")
    if color_balance < 0.6:
        notes.append("Color cast detected; natural daylight helps assess coat/skin color accurately.")

    # Very rough health hints (non-diagnostic)
    summary_bits = []
    if brightness > 0.4 and clarity > 0.5:
        summary_bits.append("Overall photo quality is adequate for a quick visual check.")
    if len(notes) == 0:
        summary_bits.append("No obvious visual issues from the photo alone (not a diagnosis).")
    summary = " ".join(summary_bits) if summary_bits else "Photo quality limitations may affect assessment."

    # Generic nutrition tips (could be tailored later)
    nutrition = [
        "Feed a complete, AAFCO-compliant diet appropriate for your dog’s life stage.",
        "Keep treats under 10% of daily calories.",
        "Ensure fresh water at all times.",
        "Maintain a consistent feeding schedule.",
    ]

    return brightness, clarity, color_balance, summary, nutrition
