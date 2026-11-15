"""Synthetic smoke/unit checks only, not a full dataset training result."""
import io
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image
import torch
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import ROOT, split_indices, versions
from engine import run_epoch
from evaluate import load_model
from model import NeuralNetwork
from preprocessing import preprocess


class CoreTests(unittest.TestCase):
    def test_versions_and_preprocessing_png_roundtrip(self):
        self.assertEqual(versions()["torch"], "2.6.0+cpu")
        self.assertEqual(versions()["torchvision"], "0.21.0+cpu")
        image = Image.new("L", (28, 28), 128)
        tensor = preprocess(image)
        self.assertEqual(tuple(tensor.shape), (1, 28, 28))
        torch.testing.assert_close(tensor, torch.full((1, 28, 28), 128 / 255))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        with Image.open(buffer) as loaded:
            torch.testing.assert_close(preprocess(loaded), tensor, rtol=0, atol=0)
        with self.assertRaises(ValueError):
            preprocess(Image.new("L", (32, 32)))

    def test_seeded_split_is_complete_disjoint_and_repeatable(self):
        train, validation = split_indices(60000, 42)
        self.assertEqual((len(train), len(validation)), (54000, 6000))
        self.assertFalse(set(train) & set(validation))
        self.assertEqual(set(train) | set(validation), set(range(60000)))
        self.assertEqual((train, validation), split_indices(60000, 42))
        self.assertNotEqual(train[:20], split_indices(60000, 43)[0][:20])

    def test_gradient_and_state_dict_reload(self):
        torch.set_num_threads(2)
        torch.manual_seed(42)
        model = NeuralNetwork()
        images = torch.rand(3, 1, 28, 28)
        loss = torch.nn.CrossEntropyLoss()(model(images), torch.tensor([0, 1, 2]))
        loss.backward()
        self.assertIsNotNone(model.linear_relu_stack[0].weight.grad)
        self.assertEqual(tuple(model(images).shape), (3, 10))
        folder = ROOT / "outputs"
        folder.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temp:
            checkpoint = Path(temp) / "synthetic.pth"
            torch.save(model.state_dict(), checkpoint)
            restored = load_model(checkpoint)
            with torch.inference_mode():
                torch.testing.assert_close(restored(images), model(images), rtol=0, atol=0)

    def test_metrics_weight_partial_batches_by_sample_count(self):
        logits = torch.tensor([[4., 0.], [0., 4.], [4., 0.]])
        labels = torch.tensor([0, 1, 1])
        loader = DataLoader(TensorDataset(logits, labels), batch_size=2)
        result = run_epoch(torch.nn.Identity(), loader, "cpu")
        self.assertEqual(result["samples"], 3)
        self.assertAlmostEqual(result["accuracy"], 2 / 3)
        self.assertAlmostEqual(result["loss"], torch.nn.functional.cross_entropy(logits, labels).item(), places=6)


if __name__ == "__main__":
    unittest.main()
