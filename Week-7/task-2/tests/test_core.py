"""Synthetic correctness checks, not full CIFAR10 training metrics."""
import io
import sys
import unittest
from pathlib import Path

from PIL import Image
import torch
from torch.utils.data import DataLoader, TensorDataset
from torchvision.transforms import v2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import split_indices
from engine import run_epoch
from model import Net
from preprocessing import preprocess


class CoreTests(unittest.TestCase):
    def test_transform_matches_tutorial_and_png_roundtrip(self):
        original = Image.new("RGB", (32, 32), (0, 128, 255))
        expected = v2.Compose([v2.ToImage(), v2.ToDtype(torch.float32, scale=True),
                               v2.Normalize((.5,)*3, (.5,)*3)])(original)
        self.assertTrue(torch.equal(preprocess(original), expected))
        buffer = io.BytesIO()
        original.save(buffer, format="PNG")
        buffer.seek(0)
        with Image.open(buffer) as png:
            self.assertTrue(torch.equal(preprocess(png), expected))
        self.assertEqual(tuple(expected.shape), (3, 32, 32))
        self.assertEqual(expected[0, 0, 0].item(), -1)
        self.assertEqual(expected[2, 0, 0].item(), 1)
        with self.assertRaises(ValueError):
            preprocess(Image.new("RGB", (28, 28)))

    def test_split_complete_disjoint_repeatable(self):
        train, validation = split_indices(50000, 42)
        self.assertEqual((len(train), len(validation)), (45000, 5000))
        self.assertFalse(set(train) & set(validation))
        self.assertEqual(set(train) | set(validation), set(range(50000)))
        self.assertEqual((train, validation), split_indices(50000, 42))

    def test_cnn_shape_and_state_reload(self):
        model = Net().eval()
        self.assertEqual(sum(p.numel() for p in model.parameters()), 62006)
        inputs = torch.zeros(2, 3, 32, 32)
        with torch.inference_mode():
            before = model(inputs)
        buffer = io.BytesIO()
        torch.save(model.state_dict(), buffer)
        buffer.seek(0)
        reloaded = Net().eval()
        reloaded.load_state_dict(torch.load(buffer, weights_only=True))
        with torch.inference_mode():
            torch.testing.assert_close(reloaded(inputs), before)
        self.assertEqual(tuple(before.shape), (2, 10))

    def test_metrics_weight_partial_batch_by_samples(self):
        logits = torch.tensor([[4., 0.], [0., 4.], [0., 4.]])
        labels = torch.tensor([0, 1, 0])
        result = run_epoch(torch.nn.Identity(), DataLoader(TensorDataset(logits, labels), batch_size=2), "cpu")
        self.assertEqual(result["samples"], 3)
        self.assertAlmostEqual(result["accuracy"], 2/3)
        self.assertAlmostEqual(result["loss"], torch.nn.functional.cross_entropy(logits, labels).item(), places=6)


if __name__ == "__main__":
    torch.set_num_threads(2)
    unittest.main()
