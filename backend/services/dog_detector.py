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

# Keywords that cover most dog breeds (ImageNet names don’t always include “dog”)
DOG_KEYWORDS = {
    "dog","retriever","terrier","poodle","beagle","husky","pug","spaniel","mastiff",
    "shepherd","setter","collie","bulldog","chihuahua","malamute","samoyed",
    "greyhound","whippet","boxer","rottweiler","doberman","pinscher","dalmatian",
    "ridgeback","newfoundland","pointer","labrador","pomeranian","papillon","akita",
    "saluki","borzoi","weimaraner","keeshond","vizsla","schipperke","affenpinscher",
    "briard","komondor","pekinese","shihtzu","shih-tzu","schnauzer","great dane",
    "corgi","dachshund","hound","wolfhound","springer","basset","bloodhound",
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

def is_dog_image(image: Image.Image, threshold: float = 0.30):
    """
    Heuristic check using ImageNet classes.
    Returns (is_dog: bool, top_label: str, confidence: float).
    """
    label, conf = predict_label(image)
    name = label.lower()
    if conf < threshold:
        return (False, label, conf)
    if any(k in name for k in DOG_KEYWORDS):
        return (True, label, conf)
    return (False, label, conf)
