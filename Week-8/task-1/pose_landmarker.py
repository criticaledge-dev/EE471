"""Print MediaPipe landmarks from one unchanged image; no arm classification."""
import argparse
import json
from pathlib import Path
import sys

from _paths import ROOT
import mediapipe as mp

POINTS={11:'left_shoulder',12:'right_shoulder',13:'left_elbow',14:'right_elbow',15:'left_wrist',16:'right_wrist'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',type=Path)
    parser.add_argument('--output',type=Path,help='Optional annotated PNG inside Week-8/task-1/output.')
    parser.add_argument('--model',type=Path,default=ROOT/'models/pose_landmarker_lite.task')
    args=parser.parse_args()
    if not args.image.is_file() or not args.model.is_file():
        parser.error('Image/model missing. See Week-8/README.md for local model paths.')
    options=mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model),delegate=mp.tasks.BaseOptions.Delegate.CPU),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,num_poses=4)
    with mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
        result=detector.detect(mp.Image.create_from_file(str(args.image)))
    if args.output:
        from _presentation import landmarks
        landmarks(args.image,args.output,[('pose',points) for points in result.pose_landmarks])
    poses=[]
    for landmarks in result.pose_landmarks:
        selected={name:{field:getattr(landmarks[index],field) for field in ('x','y','z','visibility','presence')}
                  for index,name in POINTS.items()}
        poses.append({'landmark_count':len(landmarks),'sample_landmarks':selected})
    print(json.dumps({'image':args.image.name,'pose_count':len(poses),'poses':poses},indent=2))


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError) as error:
        print(f'{type(error).__name__}: {error}',file=sys.stderr)
        sys.exit(1)
