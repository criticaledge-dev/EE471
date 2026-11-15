"""Quickstart MLP; importable without downloading data or starting training."""
from torch import nn


class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.flatten = nn.Flatten()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(28 * 28, 512), nn.ReLU(),
            nn.Linear(512, 512), nn.ReLU(), nn.Linear(512, 10),
        )

    def forward(self, x):
        return self.linear_relu_stack(self.flatten(x))
