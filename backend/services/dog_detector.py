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
    "shiba", "shibas", "chow", "chows", "shar-pei", "shar pei", "basenji", "basenjis",
    "mexican hairless", "hairless", "xoloitzcuintli", "xolo"
}

# Keywords for NON-DOG animals that should be explicitly rejected
NON_DOG_ANIMALS = {
    "goat", "goats", "sheep", "ram", "ewe", "lamb", "lambs",
    "cat", "cats", "kitten", "kittens", "feline", "felines",
    "cow", "cows", "bull", "bulls", "cattle", "calf", "calves",
    "horse", "horses", "pony", "ponies", "mare", "stallion",
    "pig", "pigs", "swine", "boar", "sow",
    "chicken", "chickens", "rooster", "hen",
    "duck", "ducks", "goose", "geese",
    "rabbit", "rabbits", "bunny", "bunnies",
    "hamster", "hamsters", "guinea pig", "guinea pigs",
    "bird", "birds", "parrot", "parrots"
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
    Explicitly rejects non-dog animals like goats, sheep, cats, etc.
    Returns (is_dog: bool, top_label: str, confidence: float, detection_method: str).
    """
    label, conf = predict_label(image)
    name = label.lower()
    
    # FIRST: Check if it's explicitly a NON-DOG animal - reject immediately (STRICT CHECK)
    # Check both exact match and partial match for better detection
    for non_dog in NON_DOG_ANIMALS:
        if non_dog in name or name in non_dog:
            print(f"[VALIDATION] ✗ Rejecting non-dog animal: {label} (matched keyword: {non_dog}, confidence: {conf:.2%})")
            return (False, label, conf, "non_dog_animal_detected")
    
    # SPECIAL CHECK: Reject "ram" (male goat/sheep) which ImageNet has as a class
    if "ram" in name and conf >= 0.1:  # Even low confidence for ram = reject
        print(f"[VALIDATION] ✗ Rejecting ram (goat): {label} (confidence: {conf:.2%})")
        return (False, label, conf, "ram_detected")
    
    # Method 1: Direct keyword matching in top prediction
    if conf >= threshold:
        if any(k in name for k in DOG_KEYWORDS):
            return (True, label, conf, "keyword_match")
    
    # Method 2: Check top 10 predictions (expanded from 5) for better detection
    model = _load_model()
    tensor = _preprocess(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        top10_probs, top10_indices = torch.topk(probs, 10)  # Check top 10 instead of 5
        labels_list = _labels()
        
        # First check: Reject if any of top 10 is a non-dog animal (EXTREMELY LOW threshold)
        for prob, idx in zip(top10_probs, top10_indices):
            pred_label = labels_list[int(idx)].lower()
            
            # SPECIAL: Reject "ram" (goat) even more aggressively
            if "ram" in pred_label and float(prob) >= 0.02:  # Even 2% confidence = reject
                print(f"[VALIDATION] ✗ Rejecting ram (goat) in top10: {labels_list[int(idx)]} (confidence: {float(prob):.2%})")
                return (False, labels_list[int(idx)], float(prob), "ram_in_top10")
            
            # Check both exact and partial matches for other non-dog animals
            for non_dog in NON_DOG_ANIMALS:
                if non_dog in pred_label or pred_label in non_dog:
                    # Extremely low threshold (0.03) - be ULTRA aggressive in rejecting non-dog animals
                    if float(prob) >= 0.03:  # Even 3% confidence it's a non-dog animal = reject
                        print(f"[VALIDATION] ✗ Rejecting non-dog animal in top10: {labels_list[int(idx)]} (confidence: {float(prob):.2%}, matched: {non_dog})")
                        return (False, labels_list[int(idx)], float(prob), "non_dog_in_top10")
        
        # Second check: Look for dog keywords in top 10
        dog_found = False
        dog_confidence = 0.0
        dog_label = None
        for prob, idx in zip(top10_probs, top10_indices):
            pred_label = labels_list[int(idx)].lower()
            if any(k in pred_label for k in DOG_KEYWORDS):
                # Track the highest dog confidence
                if float(prob) > dog_confidence:
                    dog_confidence = float(prob)
                    dog_label = labels_list[int(idx)]
                if float(prob) >= 0.15:  # Decent confidence for dog
                    dog_found = True
        
        # Only accept if we found a dog with decent confidence AND no non-dog animals were found
        # INCREASED threshold from 0.15 to 0.25 for better accuracy
        if dog_found and dog_confidence >= 0.25:
            print(f"[VALIDATION] ✓ Dog confirmed: {dog_label} (confidence: {dog_confidence:.2%})")
            return (True, dog_label, dog_confidence, "top10_dog_match")
    
    return (False, label, conf, "no_match")

def validate_dog_image(image_path: str) -> tuple:
    """
    Comprehensive dog image validation with multiple checks.
    Returns (is_valid: bool, confidence: float, message: str, detected_label: str)
    """
    try:
        pil_img = Image.open(image_path).convert("RGB")
        is_dog, label, conf, method = is_dog_image(pil_img)
        
        print(f"[VALIDATION] Dog detector result: is_dog={is_dog}, label='{label}', confidence={conf:.2%}, method='{method}'")
        
        if is_dog:
            confidence_pct = round(conf * 100, 1)
            print(f"[VALIDATION] ✓ Dog confirmed: {label} ({confidence_pct}% confidence)")
            return (True, conf, f"Dog detected: {label} ({confidence_pct}% confidence)", label)
        else:
            # Provide helpful error message
            confidence_pct = round(conf * 100, 1) if conf > 0 else 0
            detected_item = label if label else "unknown object"
            print(f"[VALIDATION] ✗ Rejected: {detected_item} ({confidence_pct}% confidence) - {method}")
            return (False, conf, f"Image does not appear to contain a dog. Detected object: {detected_item} ({confidence_pct}% confidence)", label)
    except Exception as e:
        print(f"[VALIDATION] ERROR: Dog validation error: {e}")
        import traceback
        traceback.print_exc()
        return (False, 0.0, f"Error validating image: {str(e)}", "unknown")
