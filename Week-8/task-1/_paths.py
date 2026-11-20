"""Task 1 output location; input assets remain at their existing paths."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "task-1" / "output"

# Override the shared shell's Matplotlib cache for Task 1 only, before imports.
os.environ["MPLCONFIGDIR"] = str(OUTPUT / "matplotlib")
# Demo execution should not create new bytecode files beside source/venv files.
sys.dont_write_bytecode = True
