"""Shared training/inference contract: 28x28 L image -> [1,28,28] float [0,1]."""
from torchvision.transforms import ToTensor

CLASSES = ("T-shirt/top", "Trouser", "Pullover", "Dress", "Coat", "Sandal",
           "Shirt", "Sneaker", "Bag", "Ankle boot")
_to_tensor = ToTensor()


def preprocess(image):
    if image.size != (28, 28):
        raise ValueError("Expected a 28x28 image; no implicit resize/crop is applied.")
    return _to_tensor(image.convert("L"))
