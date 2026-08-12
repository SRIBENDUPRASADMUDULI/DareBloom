import streamlit as st
import torch
import torchvision.transforms as transforms
from PIL import Image
import torchvision.models as models
from torch import nn

# Page configuration
st.set_page_config(page_title="Flower Classification App", page_icon="🌸", layout="centered")

st.title("🌸 Flower Classification App")
st.write("Upload an image of a flower to classify it using your trained ResNet18 model!")

# 1. Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 2. Load Model (Cached taaki baar-baar load na karna pade)
@st.cache_resource
def load_model():
    model = models.resnet18(weights=None)
    num_classes = 104  
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model.load_state_dict(torch.load('flower_model.pth', map_location=device))
    model = model.to(device)
    model.eval()
    return model

model = load_model()

# 3. Image preprocessing transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 4. File uploader widget
uploaded_file = st.file_uploader("Choose a flower image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Image display karo
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption='Uploaded Image', use_column_width=True)
    
    st.write("Classifying...")
    
    # Preprocess & Predict
    img_tensor = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(img_tensor)
        _, predicted = torch.max(outputs, 1)
        class_idx = predicted.item()
        
    st.success(f"Prediction Complete!")
    st.markdown(f"### Predicted Flower Class Index: **{class_idx}**")