"""Transcribe one local 16kHz mono PCM16 WAV with MediaPipe, without microphone."""
import argparse
import json
from pathlib import Path
import sys
import wave

from _paths import ROOT, OUTPUT
import mediapipe as mp
import numpy as np

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio',type=Path)
    parser.add_argument('--report',type=Path,help='Optional input/result PNG inside Week-8/task-1/output.')
    parser.add_argument('--model',type=Path,default=ROOT/'models/parakeet_tdt_0.6b_v3_5s_i8_stateful.litertlm')
    args=parser.parse_args()
    if not args.audio.is_file() or not args.model.is_file():
        parser.error('Audio/model missing. See Week-8/README.md for official downloads.')
    with wave.open(str(args.audio),'rb') as source:
        if (source.getnchannels(),source.getsampwidth(),source.getframerate(),source.getcomptype())!=(1,2,16000,'NONE'):
            raise ValueError('Use an uncompressed 16kHz mono signed PCM16 WAV; headers alone are not a conversion.')
        if not 0<source.getnframes()<=30*16000:
            raise ValueError('Use a non-empty clip no longer than 30 seconds.')
        frames=source.getnframes()
        raw=source.readframes(frames)
    if len(raw)!=frames*2:raise ValueError('Truncated WAV sample data.')
    samples=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.0
    cache=OUTPUT/'audio-cache'
    cache.mkdir(parents=True,exist_ok=True)
    options=mp.tasks.audio.AudioTranscriberOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model),delegate=mp.tasks.BaseOptions.Delegate.CPU),
        sample_rate_hz=16000,cache_dir=str(cache))
    with mp.tasks.audio.AudioTranscriber.create_from_options(options) as transcriber:
        result=transcriber.transcribe(samples,end_of_stream=True)
    if not result.text.strip():raise RuntimeError('MediaPipe returned no transcript; no substitute text is used.')
    payload={'audio':args.audio.name,'seconds':len(samples)/16000,'text':result.text}
    if args.report:
        from _presentation import report
        report(args,payload,wav=str(args.audio),sample_rate_hz=16000)
    print(json.dumps(payload,indent=2,ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError,ValueError,wave.Error) as error:
        print(f'{type(error).__name__}: {error}',file=sys.stderr)
        sys.exit(1)
