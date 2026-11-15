"""One importable transform for dataset training and PNG inference."""
from torchvision.transforms import Compose, Normalize, ToTensor

CLASSES = ("airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck")
TRANSFORM = Compose([ToTensor(), Normalize((.5, .5, .5), (.5, .5, .5))])


def preprocess(image):
    if image.size != (32, 32):
        raise ValueError("Expected a 32x32 CIFAR10-style image; no resizing is applied.")
    return TRANSFORM(image.convert("RGB"))
