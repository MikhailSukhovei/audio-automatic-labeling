import os


"""
Data structure names
"""
RAW_DATA_PATH = os.path.join('data', 'raw')  # raw audio files (.wav, .mp3)
INPUT_DATA_PATH = os.path.join('data', 'input')  # processed audio files (.wav)
ASR_DATA_PATH = os.path.join('data', 'asr')  # predicted texts (.json)
PUNC_DATA_PATH = os.path.join('data', 'punc')  # predicted text with punctuation and capital letters (.json)
WAVS_DATA_PATH = os.path.join('data', 'wavs')  # dataset samples (.wav)
METADATA_PATH = os.path.join('data', 'metadata.csv')  # dataset metadata
FILELISTS_PATH = os.path.join('data', 'filelists')  # train, val, test samples (https://github.com/NVIDIA/tacotron2)

"""
Train, val, test split
"""
TRAIN_PATH = os.path.join(FILELISTS_PATH, 'ljs_audio_text_train_filelist.txt')  # train names
VAL_PATH = os.path.join(FILELISTS_PATH, 'ljs_audio_text_val_filelist.txt')  # val names
TEST_PATH = os.path.join(FILELISTS_PATH, 'ljs_audio_text_test_filelist.txt')  # test names
TRAIN_FRAC = 0.95  # train fraction
VAL_FRAC = 0.05  # val fraction
TEST_FRAC = 0.0  # test fraction
assert TRAIN_FRAC + VAL_FRAC + TEST_FRAC == 1.0

"""
Vosk models
"""
# load model for required language from https://alphacephei.com/vosk/models
# you should use big models for the high-accuracy transcription
LANG = 'ru'  # language
ASR_MODEL = os.path.join('vosk_models', 'vosk-model-ru-0.22')  # automatic speech recognition model
PUNC_MODEL = os.path.join('vosk_models', 'vosk-recasepunc-ru-0.22', 'checkpoint')  # restore punctuation model

"""
Dataset settings
"""
SAMPLE_RATE = 22050  # Hz

MIN_CONF = 1.0  # minimal confidence level for text fragment (mean for all words)
MIN_TIME = 1.11  # minimal audio sample duration (sec)
MAX_TIME = 8.0  # maximal audio sample duration (sec)

# https://github.com/NVIDIA/tacotron2/issues/269
# Add silence at the end audio.
# The recommended size of silence is 5 hop_size.
# It will make learned attention alignments better.

# HOP_LENGTH = 256
# SILENCE_START = int((HOP_LENGTH * 5) / SAMPLE_RATE * 1000)  # ms
# SILENCE_END = int((HOP_LENGTH * 5) / SAMPLE_RATE * 1000)  # ms
SILENCE_START = 58  # ms
SILENCE_END = 58  # ms
