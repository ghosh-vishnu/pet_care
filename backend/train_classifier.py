# train_classifier.py

# This script is designed to perform fine-tuning on the Stanford Dogs Dataset.
# It is set to run on CPU only, which will take a very long time (days/weeks).

import torch
from torchvision import datasets, transforms
from efficientnet_pytorch import EfficientNet
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
import os

# --- 1. CONFIGURATION ---
NUM_CLASSES = 120
# Path to the Images folder you created in the 'data' directory:
DATA_DIR = './data/Images' 
SAVE_PATH = './services/dog_breed_weights.pth'
# Batch size must be small for CPU memory
BATCH_SIZE = 16 
NUM_EPOCHS = 40 # Running more epochs increases accuracy (>70% target)
LEARNING_RATE = 0.001
DEVICE = torch.device("cpu") # FORCED CPU TRAINING

# --- 2. DATA PREPARATION ---
# Training requires transformations and augmentation (crucial for high accuracy!)
data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# Load the entire dataset
print("Loading all images from dataset...")
try:
    full_dataset = datasets.ImageFolder(DATA_DIR, data_transforms['train'])
except FileNotFoundError as e:
    print(f"ERROR: Cannot find dataset folder. Check DATA_DIR path: {DATA_DIR}")
    print("Ensure you moved the 'Images' folder into the 'data' directory.")
    exit()

# Split dataset into training (80%) and validation (20%)
train_size = int(0.8 * len(full_dataset))
val_size = len(full_dataset) - train_size
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

# Apply validation transforms to the validation set split
val_dataset.dataset.transform = data_transforms['val']

image_datasets = {'train': train_dataset, 'val': val_dataset}

dataloaders = {x: DataLoader(image_datasets[x], batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
               for x in ['train', 'val']}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}

# Save the class names (in the correct order) to the label file
class_names = [item[0].replace('_', ' ').replace('-', ' ') for item in sorted(full_dataset.class_to_idx.items(), key=lambda item: item[1])]
with open('./assets/dog_breeds_120.txt', 'w') as f:
    f.write('\n'.join(class_names))
print(f"Saved {len(class_names)} class names to dog_breeds_120.txt.")


# --- 3. MODEL SETUP (Fine-Tuning) ---
print("Setting up EfficientNet model...")
model_ft = EfficientNet.from_pretrained('efficientnet-b0')

# Freeze the base layers (we only train the top layer initially)
for param in model_ft.parameters():
    param.requires_grad = False

# Replace the final classification layer for our 120 classes
num_ftrs = model_ft._fc.in_features
model_ft._fc = nn.Linear(num_ftrs, NUM_CLASSES)

model_ft = model_ft.to(DEVICE)
criterion = nn.CrossEntropyLoss()
# Optimizer only trains the new final layer (since others are frozen)
optimizer_ft = torch.optim.Adam(model_ft.parameters(), lr=LEARNING_RATE)


# --- 4. TRAINING FUNCTION ---
def train_model(model, criterion, optimizer, num_epochs, phase_name):
    print(f"\n--- Starting Training Phase: {phase_name} ({num_epochs} Epochs) ---")
    
    # Reload best weights if available before starting fine-tuning
    if os.path.exists(SAVE_PATH):
        model.load_state_dict(torch.load(SAVE_PATH, map_location=DEVICE))
    
    best_acc = 0.0
    start_time = torch.zeros(1) # Placeholder for timer

    for epoch in range(num_epochs):
        # We check the validation set after every training epoch
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Start timer for CPU warning
            if phase == 'train' and epoch == 0:
                start_time = torch.tensor(os.times().system + os.times().user)
                print(f"WARNING: CPU training is extremely slow. Est. time per epoch: {len(dataloaders[phase]) * 0.5:.0f} mins or more.")


            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(DEVICE)
                labels = labels.to(DEVICE)

                optimizer.zero_grad()

                # forward
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'Epoch {epoch}: {phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            # Save the best model based on validation accuracy
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                torch.save(model.state_dict(), SAVE_PATH) # Save the best weights!

    # Final CPU Time Check (Approximation)
    end_time = torch.tensor(os.times().system + os.times().user)
    print(f'Total CPU time for training: {(end_time - start_time) / 60:.2f} minutes.')
    print(f'Best validation Acc achieved: {best_acc:.4f}')
    return model


# --- 5. EXECUTION ---
if __name__ == '__main__':
    # Phase 1: Train ONLY the final classification layer (Fastest step)
    print("PHASE 1: Training only the final classifier layer.")
    model_ft = train_model(model_ft, criterion, optimizer_ft, num_epochs=3, phase_name="Classifier Head")
    
    # PHASE 2: Unfreeze and Retrain (The long step for high accuracy)
    print("\nPHASE 2: Unfreezing top blocks for full fine-tuning (CRITICAL for >70% accuracy).")
    
    # Unfreeze the top 3-4 blocks of the model to learn dog-specific features
    for name, param in model_ft.named_parameters():
        if '_blocks.6' in name or '_blocks.5' in name or '_fc' in name:
            param.requires_grad = True

    # Use a much lower learning rate for the full fine-tuning
    optimizer_ft = torch.optim.Adam(filter(lambda p: p.requires_grad, model_ft.parameters()), lr=1e-5)

    # Run the main training phase (this is the step that takes days on CPU)
    train_model(model_ft, criterion, optimizer_ft, num_epochs=NUM_EPOCHS, phase_name="Full Fine-Tuning")