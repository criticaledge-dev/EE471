# Week 8 — Task 3: Head direction

Give the script one JPEG/PNG with a visible face. It returns `left`, `right`
or `straight`, using the viewer's left and right in the upright image.
This measures the head turn. It does not estimate where the eyes are looking.
An image with no detected face gives an explicit error.

The MediaPipe Face Landmarker returns a 3D face transformation. The horizontal
angle of its forward axis is estimated with `atan2(x, z)`. Angles within
±15° count as straight; larger turns choose a side by the sign.

From `Week-8` in the existing WSL setup:

```bash
source ./activate.sh
cd task-3
bash download_model.sh
PHOTO="/mnt/c/Users/LENOVO/Downloads"
for n in 1 2 3; do python classify_face.py "$PHOTO/face-$n.png"; done
```

For a separate Linux environment, use Python 3.12 and install `requirements.txt`
in a virtual environment. The model script verifies the download checksum.
The required system packages are listed in `cog.yaml`.

| Input | Expected output |
| --- | --- |
| face-1.png | left |
| face-2.png | right |
| face-3.png | straight |

To save the photos with the estimated angle and direction, run from
`Week-8/task-3` after setting `PHOTO` as above:

```bash
for n in 1 2 3; do
    python classify_face.py "$PHOTO/face-$n.png" --output "outputs/face-$n-result.png" || break
done
```

Open the PNGs under `outputs/`. Arrows indicate left or right; a centered dot
indicates straight. The input photos are preserved and the CLI/Cog string
outputs stay the same. Preview generation is a local Python option.

With Docker Desktop running and WSL integration enabled, from `Week-8/task-3`:

```bash
bash download_model.sh
cog build --use-cog-base-image=false -t ee471-week8-face-direction
PHOTO="/mnt/c/Users/LENOVO/Downloads"
for n in 1 2 3; do
    cog run ee471-week8-face-direction -i "image=@${PHOTO}/face-$n.png" || break
done
```

The Cog runner calls the same inference function used by the Python command.
