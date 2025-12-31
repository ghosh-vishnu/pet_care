# backend/services/dog_detector.py
import os
from functools import lru_cache

import torch
from torchvision import models, transforms
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LABELS_PATH = os.path.join(ASSETS_DIR, "imagenet_classes.txt")

# Preprocessing for ImageNet models
_preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

@lru_cache(maxsize=1)
def _load_model():
    # Small & fast model, good for CPU
    weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
    model = models.mobilenet_v3_small(weights=weights)
    model.eval()
    return model

@lru_cache(maxsize=1)
def _labels():
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        return [l.strip() for l in f]

# Comprehensive keywords that cover most dog breeds (ImageNet names don't always include "dog")
DOG_KEYWORDS = {
    "dog", "dogs", "puppy", "puppies", "canine", "canines",
    "retriever", "retrievers", "terrier", "terriers", "poodle", "poodles",
    "beagle", "beagles", "husky", "huskies", "pug", "pugs", "spaniel", "spaniels",
    "mastiff", "mastiffs", "shepherd", "shepherds", "setter", "setters",
    "collie", "collies", "bulldog", "bulldogs", "chihuahua", "chihuahuas",
    "malamute", "malamutes", "samoyed", "samoyeds", "greyhound", "greyhounds",
    "whippet", "whippets", "boxer", "boxers", "rottweiler", "rottweilers",
    "doberman", "dobermans", "pinscher", "pinschers", "dalmatian", "dalmatians",
    "ridgeback", "ridgebacks", "newfoundland", "newfoundlands", "pointer", "pointers",
    "labrador", "labradors", "pomeranian", "pomeranians", "papillon", "papillons",
    "akita", "akitas", "saluki", "salukis", "borzoi", "borzois", "weimaraner", "weimaraners",
    "keeshond", "keeshonds", "vizsla", "vizslas", "schipperke", "schipperkes",
    "affenpinscher", "affenpinschers", "briard", "briards", "komondor", "komondors",
    "pekinese", "pekineses", "shihtzu", "shih-tzu", "schnauzer", "schnauzers",
    "great dane", "great danes", "corgi", "corgis", "dachshund", "dachshunds",
    "hound", "hounds", "wolfhound", "wolfhounds", "springer", "springers",
    "basset", "bassets", "bloodhound", "bloodhounds", "eskimo", "eskimos",
    "shiba", "shibas", "chow", "chows", "shar-pei", "shar pei", "basenji", "basenjis"
}

def predict_label(image: Image.Image):
    """Return (top_label, confidence_float)."""
    model = _load_model()
    tensor = _preprocess(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        conf, idx = probs.max(0)
    label = _labels()[int(idx)]
    return label, float(conf)

def is_dog_image(image: Image.Image, threshold: float = 0.25):
    """
    Enhanced dog detection using ImageNet classes with multiple checks.
    Returns (is_dog: bool, top_label: str, confidence: float, detection_method: str).
    """
    label, conf = predict_label(image)
    name = label.lower()
    
    # Method 1: Direct keyword matching in top prediction
    if conf >= threshold:
        if any(k in name for k in DOG_KEYWORDS):
            return (True, label, conf, "keyword_match")
    
    # Method 2: Check top 5 predictions for dog-related keywords
    model = _load_model()
    tensor = _preprocess(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        top5_probs, top5_indices = torch.topk(probs, 5)
        labels_list = _labels()
        
        for prob, idx in zip(top5_probs, top5_indices):
            pred_label = labels_list[int(idx)].lower()
            if any(k in pred_label for k in DOG_KEYWORDS):
                # If any of top 5 predictions is dog-related with decent confidence
                if float(prob) >= 0.15:  # Lower threshold for top-5
                    return (True, labels_list[int(idx)], float(prob), "top5_match")
    
    return (False, label, conf, "no_match")

def validate_dog_image(image_path: str) -> tuple:
    """
    Comprehensive dog image validation with multiple checks.
    Returns (is_valid: bool, confidence: float, message: str, detected_label: str)
    """
    try:
        pil_img = Image.open(image_path).convert("RGB")
        is_dog, label, conf, method = is_dog_image(pil_img)
        
        if is_dog:
            confidence_pct = round(conf * 100, 1)
            return (True, conf, f"Dog detected: {label} ({confidence_pct}% confidence)", label)
        else:
            # Provide helpful error message
            confidence_pct = round(conf * 100, 1) if conf > 0 else 0
            detected_item = label if label else "unknown object"
            return (False, conf, f"Image does not appear to contain a dog. Detected object: {detected_item} ({confidence_pct}% confidence)", label)
    except Exception as e:
        print(f"Dog validation error: {e}")
        return (False, 0.0, f"Error validating image: {str(e)}", "unknown")
