"""Selection-policy checks use fabricated metrics, not measured training data."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from optimize import select_winner


def trial(name, accuracy, loss, **extra):
    return {"id": name, "last_epoch": {"epoch": 2, "validation": {"accuracy": accuracy, "loss": loss}}, **extra}


class SelectionTests(unittest.TestCase):
    def test_test_scores_and_earlier_peaks_do_not_choose_winner(self):
        a = trial("a", .8, .5, test={"accuracy": 1.0}, epochs=[{"validation": {"accuracy": .99}}])
        b = trial("b", .81, .6, test={"accuracy": 0.0}, epochs=[{"validation": {"accuracy": .1}}])
        self.assertEqual(select_winner([a, b])["id"], "b")

    def test_accuracy_tie_uses_validation_loss(self):
        self.assertEqual(select_winner([trial("a", .85, .4), trial("b", .85, .3)])["id"], "b")

    def test_incomplete_or_nonfinite_metrics_rejected(self):
        a = trial("a", .9, .2)
        a["last_epoch"]["epoch"] = 1
        for values in ([], [a], [trial("bad", float("nan"), .2)]):
            with self.assertRaises(ValueError):
                select_winner(values)


if __name__ == "__main__":
    unittest.main()
