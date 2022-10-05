import os
import sys
import json
import glob
import tqdm

import pydub
import pandas as pd
from transformers import logging

import settings
from models import SpeechToText, PunctuationPredictor
from utils.audio_utils import detect_leading_silence, normalize_audio
from utils.text_cleaners import english_cleaner
from utils.utils import dataset_stat

sys.path.insert(0, settings.PUNC_MODEL)
from recasepunc import CasePuncPredictor
from recasepunc import WordpieceTokenizer

logging.set_verbosity_error()


def obj_dict(obj):
    return obj.__dict__


def automatic_speech_recognition():
    """
    Read audio files and predict text fragments and start, end, confidence for each word

    Read .wav from INPUT_DATA_PATH

    Write .json to ASR_DATA_PATH
    """
    input_paths = glob.glob(os.path.join(settings.INPUT_DATA_PATH, '**', '*.wav'), recursive=True)
    output_paths = []
    for path in input_paths:
        local_path = os.path.relpath(path, settings.INPUT_DATA_PATH)
        local_path = local_path.replace('.wav', '.json')
        output_paths.append(os.path.join(settings.ASR_DATA_PATH, local_path))

    stt = SpeechToText(dir_model=settings.ASR_MODEL, lang=settings.LANG)

    for i_path, o_path in zip(input_paths, output_paths):
        print('processing:', i_path)
        predictions = stt.predict(i_path)

        dir_name = os.path.dirname(o_path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        with open(o_path, 'w') as f:
            json.dump(predictions, f, default=obj_dict, indent=4, ensure_ascii=False)


def restore_punctuation():
    """
    Predict punctuation and capital letters for each text fragment

    Read .json from ASR_DATA_PATH

    Write .json to PUNC_DATA_PATH
    """
    punc_predictor = PunctuationPredictor(settings.PUNC_MODEL, lang=settings.LANG)

    input_paths = sorted(glob.glob(os.path.join(settings.ASR_DATA_PATH, '**', '*.json'), recursive=True))
    output_paths = []
    for path in input_paths:
        local_path = os.path.relpath(path, settings.ASR_DATA_PATH)
        output_paths.append(os.path.join(settings.PUNC_DATA_PATH, local_path))

    for i_path, o_path in zip(input_paths, output_paths):
        with open(i_path, encoding='utf8') as f:
            data = json.load(f)

        data = punc_predictor.predict(data)

        dir_name = os.path.dirname(o_path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        with open(o_path, 'w') as f:
            json.dump(data, f, default=obj_dict, indent=4, ensure_ascii=False)


def process_samples():
    """
    Cut input audio files into samples by predicted start/end values

    Threshold samples by mean confidence of fragment and duration

    Read .json from PUNC_DATA_PATH

    :return: audio segments, samples volume, dataset file names and text label
    """
    asr_paths = sorted(glob.glob(os.path.join(settings.PUNC_DATA_PATH, '**', '*.json'), recursive=True))
    input_paths = sorted(glob.glob(os.path.join(settings.INPUT_DATA_PATH, '**', '*.wav'), recursive=True))

    dataframe_list = []
    samples = []
    gain = []
    source_id = 1
    sum_time = 0
    for asr_path, pdc_path in zip(asr_paths, input_paths):
        print("Processing files:")
        print(asr_path)
        print(pdc_path)
        wav_names = []
        texts = []
        start_list = []
        end_list = []

        with open(asr_path, encoding='utf8') as f:
            data = json.load(f)

        start, end, text = [], [], []
        for item in data:
            if not item['text'] == '':
                conf = [word['conf'] for word in item['result']]
                if min(conf) >= settings.MIN_CONF:
                    start.append(item['result'][0]['start'])
                    end.append(item['result'][-1]['end'])
                    text.append(item['text'])

        dataframe = pd.DataFrame({'start': start, 'end': end, 'text': text})

        wav_file = pydub.AudioSegment.from_file(file=pdc_path, format='wav')

        samples_film = []
        samples_gain = []
        i = 1
        for _, row in dataframe.iterrows():
            start = row['start']
            end = row['end']
            sample = wav_file[(start * 1000):(end * 1000)]

            # Delete silence in the beginning and the end of a sample
            begin_trim = detect_leading_silence(sample)
            end_trim = detect_leading_silence(sample.reverse())
            duration = len(sample)
            sample_trim = sample[begin_trim:(duration - end_trim)]
            sample_trim = pydub.AudioSegment.silent(duration=settings.SILENCE_START) + sample_trim + pydub.AudioSegment.silent(duration=settings.SILENCE_END)

            if settings.MIN_TIME < sample_trim.duration_seconds < settings.MAX_TIME:
                wav_name = 'PD%s-%s' % (str(source_id).zfill(3), str(i).zfill(4))

                samples_film.append(sample_trim)
                samples_gain.append(sample_trim.dBFS)
                wav_names.append(wav_name)
                texts.append(row['text'])
                start_list.append(start)
                end_list.append(end)
                sum_time += sample_trim.duration_seconds
                i += 1

        samples.append(samples_film)
        gain.append(samples_gain)
        dataframe_list.append(pd.DataFrame({'name': wav_names, 'text': texts}))
        source_id += 1

    return samples, gain, dataframe_list


def preprocess_audio(file_format):
    """
    Convert wav and mp3 files to wav mono with SAMPLE_RATE

    Read .wav or .mp3 from RAW_DATA_PATH

    Write .wav to INPUT_DATA_PATH

    :param file_format: file format for reading from RAW_DATA_PATH
    """
    assert file_format in ['wav', 'mp3']

    input_paths = glob.glob(os.path.join(settings.RAW_DATA_PATH, '**', '*.%s' % file_format), recursive=True)

    output_paths = []
    for path in input_paths:
        local_path = os.path.relpath(path, settings.RAW_DATA_PATH)
        local_path = local_path.replace('.%s' % file_format, '.wav')
        output_paths.append(os.path.join(settings.INPUT_DATA_PATH, local_path))

    for src, des in tqdm.tqdm(zip(input_paths, output_paths)):
        if file_format == 'mp3':
            sound = pydub.AudioSegment.from_mp3(src)
        else:
            sound = pydub.AudioSegment.from_wav(src)
        sound = sound.set_channels(1)
        sound = sound.set_frame_rate(settings.SAMPLE_RATE)

        dir_name = os.path.dirname(des)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        sound.export(des, format="wav")


if __name__ == "__main__":
    # Convert wav, mp3 files to wav mono
    preprocess_audio('wav')
    preprocess_audio('mp3')

    # Predict text
    automatic_speech_recognition()

    # Predict punctuation
    restore_punctuation()

    # Cut samples
    samples, gain, dataframe_list = process_samples()

    # Normalize samples by volume
    samples_norm = normalize_audio(samples, gain)

    metadata = pd.concat(dataframe_list, axis=0)
    # Clean text
    metadata['text'] = metadata['text'].apply(english_cleaner)
    # Write metadata file
    metadata.to_csv(settings.METADATA_PATH, sep='|', header=False, index=False)

    # Write samples
    if not os.path.exists(settings.WAVS_DATA_PATH):
        os.makedirs(settings.WAVS_DATA_PATH)
    for sample, wav_name in zip([item for sublist in samples_norm for item in sublist], metadata['name'].to_list()):
        sample.export(os.path.join(settings.WAVS_DATA_PATH, '%s.wav' % wav_name), format="wav")

    # Split samples on train, val, test
    # Using format from https://github.com/NVIDIA/tacotron2
    filelists = pd.read_csv(settings.METADATA_PATH, sep='|', header=None)
    filelists[0] = filelists[0].apply(lambda x: 'DUMMY/%s.wav' % x)

    train = filelists.sample(frac=settings.TRAIN_FRAC, random_state=0)
    val_and_test = filelists.drop(train.index)
    val = val_and_test.sample(frac=settings.VAL_FRAC/(1.0 - settings.TRAIN_FRAC), random_state=0)
    test = val_and_test.drop(val.index)

    if not os.path.exists(settings.FILELISTS_PATH):
        os.makedirs(settings.FILELISTS_PATH)

    train.to_csv(settings.TRAIN_PATH, sep='|', header=False, index=False)
    val.to_csv(settings.VAL_PATH, sep='|', header=False, index=False)
    test.to_csv(settings.TEST_PATH, sep='|', header=False, index=False)

    dataset_stat(settings.WAVS_DATA_PATH, settings.METADATA_PATH, settings.DATASET_STAT_PATH)
