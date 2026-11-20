"""Download official MediaPipe assets into this project's ignored models directory."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
MODELS={
    'pose':('pose_landmarker_lite.task','https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task','59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a'),
    'face':('face_landmarker.task','https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task','64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff'),
    'audio':('parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm','https://huggingface.co/litert-community/parakeet-tdt-0.6b-v3/resolve/cd95f7bb97fd0757ab1bd6d5eff513cfcd7a2a10/parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm','66c5a74cf6c2c1d2b990901f6cece5bb53e3214dbceafa0989900a6f0eeb3504'),
}


def checksum(path):
    digest=hashlib.sha256()
    with path.open('rb') as source:
        while chunk:=source.read(1048576):digest.update(chunk)
    return digest.hexdigest()


def download(name):
    filename,url,expected=MODELS[name]
    revision=None
    if name=='audio':
        revision='cd95f7bb97fd0757ab1bd6d5eff513cfcd7a2a10'
    destination=ROOT/'models'/filename
    destination.parent.mkdir(exist_ok=True)
    partial=destination.with_suffix(destination.suffix+'.part')
    if destination.exists():
        if checksum(destination)!=expected:raise ValueError(f'{filename}: existing file SHA256 mismatch')
    else:
        for attempt in range(3):
            start=partial.stat().st_size if partial.exists() else 0
            request_url=url+('?download=true&t='+str(time.time_ns()) if name=='audio' else '')
            request=urllib.request.Request(request_url,headers={'Range':f'bytes={start}-'} if start else {})
            try:
                with urllib.request.urlopen(request,timeout=60) as response:
                    if start and (response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {start}-')):
                        raise ValueError('Server did not honor the resume offset; partial file preserved')
                    with partial.open('ab' if start else 'wb') as output:
                        last=0
                        while chunk:=response.read(1048576):
                            output.write(chunk)
                            start+=len(chunk)
                            if time.monotonic()-last>20:
                                print(filename,start,'bytes',file=sys.stderr,flush=True)
                                last=time.monotonic()
                if checksum(partial)!=expected:raise ValueError(f'{filename}: downloaded SHA256 mismatch')
                partial.replace(destination)
                break
            except Exception as error:
                print(f'{filename}: attempt {attempt+1}/3: {type(error).__name__}',file=sys.stderr,flush=True)
                if attempt==2:raise
    return {'model':name,'filename':filename,'url':url,'revision':revision,'sha256':expected,'bytes':destination.stat().st_size}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models',nargs='+',choices=tuple(MODELS))
    args=parser.parse_args()
    records=[download(name) for name in args.models]
    print(json.dumps(records,indent=2))
