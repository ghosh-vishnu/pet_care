# Dog Breed Detection Model Training Guide

## Overview
यह guide आपको अपनी own dog images के साथ breed detection model को train करने में help करेगा।

## Current Setup
- **Model Architecture**: EfficientNet-B0
- **Classes**: 120 dog breeds (from Stanford Dogs Dataset)
- **Model File**: `backend/services/dog_breed_weights.pth`
- **Class List**: `backend/assets/dog_breeds_120.txt`

## How It Currently Works

### 1. Image Upload से Breed Detection
जब user image upload करता है:
- Model automatically breed detect करता है
- Confidence score के साथ breed return होता है
- अगर pet profile में breed missing/unknown है, तो **auto-update हो जाती है** (confidence > 50%)

### 2. FAQ Responses में Breed Usage
- FAQ responses अब fully personalized हैं
- Breed-specific advice automatically include होती है
- Pet profile data (weight, age, gender, medical conditions) के साथ combined responses

## Custom Model Training Steps

### Step 1: Prepare Your Image Dataset

#### Option A: अपनी images को existing classes में organize करें

1. **Folder Structure तैयार करें:**
```
backend/data/Images/
  ├── breed_1_name/
  │   ├── image1.jpg
  │   ├── image2.jpg
  │   └── ...
  ├── breed_2_name/
  │   ├── image1.jpg
  │   └── ...
  └── ...
```

2. **Important Points:**
   - हर breed का अपना folder होना चाहिए
   - Folder name = breed name (spaces को underscore से replace करें)
   - Minimum 50-100 images per breed recommend किए जाते हैं (more = better accuracy)

#### Option B: नए breeds add करें

1. Existing `dog_breeds_120.txt` file को check करें:
   ```bash
   cat backend/assets/dog_breeds_120.txt
   ```

2. अपनी नई breeds को folders में organize करें (same structure as above)

### Step 2: Update Class List (अगर नए breeds add कर रहे हैं)

1. `backend/assets/dog_breeds_120.txt` file edit करें:
   - हर line = एक breed name
   - Alphabetical order में रखें (optional, लेकिन better organization)

2. Example:
   ```
   Afghan Hound
   Beagle
   Border Collie
   Your New Breed Name
   ...
   ```

### Step 3: Train the Model

1. **Training script चलाएं:**
   ```bash
   cd backend
   python train_classifier.py
   ```

2. **Training Settings (edit कर सकते हैं `train_classifier.py` में):**
   ```python
   NUM_EPOCHS = 40  # Training iterations (more = better but slower)
   BATCH_SIZE = 16  # Images per batch
   LEARNING_RATE = 0.001
   DATA_DIR = './data/Images'  # Your images folder
   ```

3. **Training Process:**
   - Model automatically data को train (80%) और validation (20%) में split करेगा
   - हर epoch के बाद accuracy दिखेगी
   - Best model automatically save होगा

4. **Training Time:**
   - CPU पर: कई घंटे/दिन लग सकते हैं (depends on dataset size)
   - GPU पर: बहुत faster (recommended if possible)

### Step 4: Verify Model

1. **Test breed prediction:**
   ```python
   from services.breed_classifier import predict_breed
   
   breed, confidence = predict_breed("path/to/test/image.jpg")
   print(f"Breed: {breed}, Confidence: {confidence*100:.2f}%")
   ```

2. **Expected Output:**
   - Breed name
   - Confidence score (0-1, higher = more confident)

## Integration with FAQ Responses

### Current Features

1. **Auto-Breed Detection:**
   - Image upload होते ही breed detect होती है
   - Pet profile में automatically save हो जाती है (अगर missing थी)

2. **Breed-Specific FAQ Responses:**
   - Health questions में breed-specific health concerns
   - Nutrition में breed-specific dietary needs
   - Exercise में breed-specific activity requirements
   - Grooming में breed-specific coat care

### Example FAQ Responses

**Nutrition Question:**
```
Nutrition advice for Max:

🔸 Breed-specific guidance: Labradors/Retrievers tend to gain weight easily, 
   so portion control is important. They benefit from high-protein, low-fat diets.

General Nutrition Guidelines:
1. Feed high-quality dog food appropriate for their age and size
2. Current weight: 30kg - adjust portions to maintain healthy weight
...

*Based on Max's profile: Breed: Labrador Retriever | Age: 3 years | Weight: 30kg*
```

## Tips for Better Accuracy

1. **Image Quality:**
   - High resolution images use करें
   - Clear, well-lit photos
   - Dog clearly visible होना चाहिए

2. **Dataset Size:**
   - Minimum 50 images per breed
   - 200+ images per breed = excellent accuracy
   - Variety: different angles, lighting, ages

3. **Data Augmentation:**
   - Training script automatically augment करता है (rotation, flipping, etc.)
   - This helps model generalize better

4. **Fine-Tuning:**
   - Start with pre-trained EfficientNet-B0
   - Fine-tune only last layer initially (faster)
   - Full fine-tuning = better but slower

## Troubleshooting

### Model नहीं load हो रहा:
- Check `dog_breed_weights.pth` file exists
- Verify file path in `breed_classifier.py`

### Low accuracy:
- Increase training epochs
- Add more images per breed
- Check image quality
- Verify class names match folder names

### Breed not detected correctly:
- Model को उस breed के साथ retrain करें
- More training images add करें
- Check if breed name matches exactly

## File Structure Reference

```
backend/
  ├── services/
  │   ├── breed_classifier.py       # Breed prediction logic
  │   └── dog_breed_weights.pth     # Trained model weights
  ├── assets/
  │   └── dog_breeds_120.txt        # Breed class names
  ├── data/
  │   └── Images/                   # Training images (organized by breed)
  └── train_classifier.py           # Training script
```

## Next Steps

1. अपनी dog images organize करें
2. Training शुरू करें
3. Model को test करें
4. FAQ responses automatically breed-specific हो जाएंगी!

## Questions?

- Training में issue आए तो logs check करें
- Model accuracy improve करने के लिए more data add करें
- Custom breeds add करने के लिए class list update करें

