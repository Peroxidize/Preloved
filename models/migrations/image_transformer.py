import torch
import torchvision.transforms as transforms
from torchvision.models import vgg16, VGG16_Weights
from PIL import Image
import io

class VGGFeatureExtractor:
    def __init__(self, model_name='vgg16', use_pretrained=True):
        if use_pretrained:
            weights = VGG16_Weights.DEFAULT
        else:
            weights = None

        self.model = vgg16(weights=weights)

        # Remove the final fully connected layer
        self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
        self.model.eval()

        # Define image preprocessing
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])


    def extract_features(self, image_binary):
        # Convert binary data to PIL Image
        image = Image.open(io.BytesIO(image_binary))

        # Convert to RGB if it's not already
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Preprocess the image
        x = self.preprocess(image)

        # Add batch dimension
        x = x.unsqueeze(0)

        with torch.no_grad():
            return self.model(x).view(x.size(0), -1)[0]

# Example usage:
# extractor = VGGFeatureExtractor()
# with open("path/to/your/image.jpg", "rb") as f:
#     image_binary = f.read()
# features = extractor.extract_features(image_binary)


import requests

def download_image(url):
    print('Downloading image...', "https://preloved.westus2.cloudapp.azure.com/media/" + url)
    response = requests.get("https://preloved.westus2.cloudapp.azure.com/media/" + url)
    return response.content