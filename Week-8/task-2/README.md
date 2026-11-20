# Week 8 — Task 2: Raised-arm detection

The Python script takes one JPEG or PNG path and prints `left`, `right`, `both`,
or `None`. Left and right refer to the person in the picture. No detected pose,
or no arm with enough visible evidence of being raised, returns the string `None`.

MediaPipe Pose Landmarker (Lite, CPU) gives us the coordinates of the shoulders
and wrists. Image Y increases downwards. An arm counts as raised if the wrist
is at least 0.02 image heights above its shoulder and both landmarks have
visibility of at least 0.5. This is a simple geometric rule for upright photos;
occluded wrists and camera tilt can affect the result.

## Run in Python

From `Week-8` in the existing WSL setup:

```bash
source ./activate.sh
cd task-2
bash download_model.sh
PHOTO="/mnt/c/Users/LENOVO/Downloads"
for n in 1 2 3; do python classify_arms.py "$PHOTO/pose-$n.jpg"; done
```

For a separate Linux setup, use Python 3.12 and install `requirements.txt` in a
virtual environment. The system packages required by the container are listed in
`cog.yaml`. The download script verifies the model checksum; the model and input
photographs do not need to be committed.

| Assigned image | Expected output |
| --- | --- |
| pose-1.jpg | left |
| pose-2.jpg | right |
| pose-3.jpg | both |

To save an annotated copy of one photo, run:

```bash
python classify_arms.py "$PHOTO/pose-1.jpg" --output outputs/pose-1-result.png
```

Green marks raised arms; orange marks the other visible arms. The command still
prints the same label. The Cog command returns the label as before.

## Run in Docker via Cog

Start Docker Desktop with WSL integration enabled and check `docker info` and
`cog --version`. From `Week-8/task-2`:

```bash
bash download_model.sh
cog build --use-cog-base-image=false -t ee471-week8-arms
PHOTO="/mnt/c/Users/LENOVO/Downloads"
for n in 1 2 3; do cog run ee471-week8-arms -i "image=@${PHOTO}/pose-$n.jpg"; done
```

If your Cog CLI uses the older prediction command, replace `cog run` with
`cog predict`. For the same images, the outputs should match the Python run.

## Recordings

- `task-2-demo.avi`: Open the three source photos and show the matching three
  container results. Explain that the labels use the person's own left/right.
- `task-2-explanation.avi`: In `classify_arms.py`, show image decoding, pose
  inference, the wrist/shoulder test and the four outputs. In `run.py` and
  `cog.yaml`, show how the same code runs in the container.
