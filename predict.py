import torch
import torchvision.transforms as transforms
from PIL import Image
import torchvision.models as models
from torch import nn
import os

# 1. Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# 2. Model structure initialize karo aur trained weights load karo
model = models.resnet18(weights=None)
num_classes = 104  # Total classes trained on this dataset
model.fc = nn.Linear(model.fc.in_features, num_classes)

# Save ki hui .pth file load karo
model.load_state_dict(torch.load('flower_model.pth', map_location=device))
model = model.to(device)
model.eval()  # Evaluation mode on

# 3. Image preprocessing pipeline
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_flower(image_path):
    if not os.path.exists(image_path):
        # Agar sirf 'rose' diya hai aur extension nahi mila, toh .jpg try karenge
        if os.path.exists(image_path + '.jpg'):
            image_path = image_path + '.jpg'
        else:
            print(f"Error: '{image_path}' file nahi mili! Sahi path do.")
            return

    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0)  # Batch dimension add karo
    image = image.to(device)
    
    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)
        
    print(f"Predicted Flower Class Index: {predicted.item()}")

# Test karne ke liye image ka naam yahan likha hai
predict_flower('rose')