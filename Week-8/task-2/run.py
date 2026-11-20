"""Cog wrapper around the same code used by the Python CLI."""
from cog import BaseRunner, Input, Path

from classify_arms import load_model, predict


class Runner(BaseRunner):
    def setup(self) -> None:
        self.detector = load_model()

    def run(self, image: Path = Input(description="An upright JPEG or PNG with one person")) -> str:
        return predict(self.detector, image)
