import torch
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
print(f"Done {type(tts).__name__} torch version: {torch.__version__}")
