"""File-only presentation regressions; these do not replace real model runs."""
from argparse import Namespace
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from _common import present, output_path
from _presentation import ROOT, OUTPUT, classification, comparison, destination, report, validate_artifact


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUTPUT.mkdir(parents=True, exist_ok=True)

    def test_output_cannot_replace_input_or_escape_outputs(self):
        for path in (ROOT / "task-1/test.png", OUTPUT / "../README.png", OUTPUT / "not-png.jpg", ROOT / "outputs/old.png"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                destination(path)

    def test_shared_output_validator_rejects_old_root(self):
        self.assertEqual(output_path(OUTPUT / "new.wav"), OUTPUT / "new.wav")
        with self.assertRaises(ValueError):
            output_path(ROOT / "outputs" / "old.wav")

    def test_no_report_keeps_original_cli_payload(self):
        result = {"dimension": 100, "cosine_similarity": 0.5}
        self.assertIs(present(Namespace(report=None), result, text="example"), result)

    def test_photo_panels_keep_exact_pixels_and_low_scores(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT) as directory:
            directory = Path(directory)
            source = directory / "source.png"
            pixels = np.zeros((100, 140, 3), dtype=np.uint8)
            pixels[:, :50] = [239, 53, 47]
            pixels[:, 50:] = [12, 83, 200]
            Image.fromarray(pixels).save(source)
            target = directory / "classification.png"
            scores = [{"label": "low score", "score": 0.01953}]
            classification(source, target, scores)
            self.assertEqual(validate_artifact(target)["source_matching_pixel_fraction"], [1.0])
            metadata = json.loads(target.with_suffix(".png.json").read_text())
            self.assertEqual(metadata["details"]["top_three"], scores)
            with Image.open(target) as image:
                np.testing.assert_array_equal(np.asarray(image)[:100,:140], pixels)
            compared = directory / "comparison.png"
            result = {"dimension":1024, "cosine_similarity":0.90741}
            comparison(source, source, compared, result)
            self.assertEqual(validate_artifact(compared)["source_matching_pixel_fraction"], [1.0, 1.0])

    def test_report_pairs_actual_input_and_result_without_changing_payload(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT) as directory:
            target = Path(directory) / "report.png"
            result = {"recognized_text":"A real result supplied by the caller."}
            self.assertIs(report(Namespace(report=target), result, wav="example.wav"), result)
            metadata = json.loads(target.with_suffix(".png.json").read_text())
            self.assertEqual(metadata["details"], {"input":{"wav":"example.wav"}, "result":result})
            validate_artifact(target)


if __name__ == "__main__":
    unittest.main()
