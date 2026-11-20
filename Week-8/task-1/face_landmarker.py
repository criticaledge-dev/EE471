"""Print MediaPipe face landmark coordinates; no looking-direction classifier."""
import argparse
import json
from pathlib import Path
import sys

from _paths import ROOT
import mediapipe as mp



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',type=Path)
    parser.add_argument('--output',type=Path,help='Optional annotated PNG inside Week-8/task-1/output.')
    parser.add_argument('--model',type=Path,default=ROOT/'models/face_landmarker.task')
    args=parser.parse_args()
    if not args.image.is_file() or not args.model.is_file():
        parser.error('Image/model missing. See Week-8/README.md for local model paths.')
    options=mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model),delegate=mp.tasks.BaseOptions.Delegate.CPU),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,num_faces=4,
        output_face_blendshapes=False,output_facial_transformation_matrixes=False)
    with mp.tasks.vision.FaceLandmarker.create_from_options(options) as detector:
        result=detector.detect(mp.Image.create_from_file(str(args.image)))
    if args.output:
        from _presentation import landmarks
        landmarks(args.image,args.output,[('face',points) for points in result.face_landmarks])
    faces=[]
    for landmarks in result.face_landmarks:
        selected={str(index):{field:getattr(landmarks[index],field) for field in ('x','y','z')}
                  for index in (1,33,263,61,291)}
        faces.append({'landmark_count':len(landmarks),'sample_landmarks':selected})
    print(json.dumps({'image':args.image.name,'face_count':len(faces),'faces':faces},indent=2))


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError) as error:
        print(f'{type(error).__name__}: {error}',file=sys.stderr)
        sys.exit(1)
