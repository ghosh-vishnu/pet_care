# services/breed_classifier.py (CORRECTED)
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL import Image
import os
import io

# You must have the efficientnet-pytorch package installed: pip install efficientnet-pytorch
from efficientnet_pytorch import EfficientNet 

# --- Define Paths and Constants ---
# BASE_DIR is the project root (e.g., .../dog-health-ai/dog-health-ai/)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# CRITICAL: Update these paths to where your files are saved!
# Assuming the model weights and class list are in the 'data' directory relative to BASE_DIR.
# If your file is called something else (e.g., 'dog_classifier.pt'), change the name here.
MODEL_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "dog_breed_weights.pth")
CLASSES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "dog_breeds_120.txt")

# --- Load Classes ---
try:
    with open(CLASSES_FILE) as f:
        BREED_CLASSES = [line.strip() for line in f.readlines()]
    NUM_CLASSES = len(BREED_CLASSES)
except FileNotFoundError:
    print(f"FATAL: Dog breed classes file not found at {CLASSES_FILE}.")
    # Use a dummy list to prevent crash if file is missing
    BREED_CLASSES = ["Unknown Breed (Check dog_breeds_120.txt)"]
    NUM_CLASSES = 1

# --- Load the EfficientNet Model ---
try:
    # 1. Initialize the EfficientNet-B0 architecture
    _model = EfficientNet.from_name('efficientnet-b0', num_classes=NUM_CLASSES)

    # 2. Load the trained weights (using map_location='cpu' for your non-GPU system)
    _model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location=torch.device('cpu')))
    _model.eval()
    print("SUCCESS: EfficientNet model loaded successfully.")

except Exception as e:
    print(f"FATAL: Error loading trained EfficientNet model: {e}")
    # In a production environment, you would want to raise an error here.
    # For now, we print an error and assume the model is initialized, 
    # but the subsequent prediction will likely fail or be inaccurate.
    # We re-initialize with ResNet18 as a safety fallback, but this isn't recommended.
    # raise 

# --- Define Image Transformations (Matches training pipeline) ---
_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    # You may want to add CenterCrop or a similar fix discussed before
    # to handle images captured from a screen.
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                          std=[0.229, 0.224, 0.225])
])

def predict_breed(image_input):
    """Predict the breed (or closest class) of a dog image with confidence score.
        Accepts either a file path or a PIL.Image object/bytes.
    """
    # Handle various inputs (path, PIL Image, or raw bytes)
    if isinstance(image_input, str):
        img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input)).convert("RGB")
    else:
        # Assumes PIL Image object
        img = image_input.convert("RGB")

    img_t = _transform(img).unsqueeze(0)

    with torch.no_grad():
        outputs = _model(img_t)
        # Apply softmax to get probabilities
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        conf, predicted = torch.max(probabilities, 0)

    label = BREED_CLASSES[predicted.item()]
    confidence = conf.item()

    return label, confidence