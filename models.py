import os
import sys
import wave
import json
import tqdm

import settings
from utils.text_cleaners import russian_restore_punc_cleaner

from vosk import Model, KaldiRecognizer
from vosk import SetLogLevel
SetLogLevel(-1)

sys.path.insert(0, settings.PUNC_MODEL)
from recasepunc import CasePuncPredictor
from recasepunc import WordpieceTokenizer


class SpeechToText:
    """
    Read .wav file and predict text fragments (automatic speech recognition) and start, end, confidence for every word

    Results in .json format
    [
        {
            "result": [
                {
                    "conf": 1.0,
                    "end": 1.68,
                    "start": 1.02,
                    "word": "hello"
                },
                {
                    "conf": 1.0,
                    "end": 2.13,
                    "start": 1.84,
                    "word": "world"
                }
            ],
            "text": "hello world"
        }
    ]
    """

    def __init__(self, dir_model="model-en", lang='en'):
        if not os.path.exists(dir_model):
            print("Please download the model from https://github.com/alphacep/kaldi-android-demo/releases and"
                  "unpack as '" + dir_model + "' in the current folder.")
            exit(1)

        self.model = Model(dir_model)

    def predict(self, dir_wav):
        wf = wave.open(dir_wav, "rb")

        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            print("Audio file" + dir_wav + "must be WAV format mono PCM.")
            exit(1)

        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)

        result = []
        with tqdm.tqdm(total=wf.getnframes()) as pbar:
            while True:
                data = wf.readframes(1000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result.append(json.loads(rec.Result()))
                else:
                    rec.PartialResult()
                pbar.update(1000)

        rec.FinalResult()
        return result


class PunctuationPredictor:
    """
    Read .json file with transcribed text fragments, concatenate it and predict punctuation and capital letters
    Then text with punctuation is adding to input .json file

    Results in .json format
    [
        {
            "result": [
                {
                    "conf": 1.0,
                    "end": 1.68,
                    "start": 1.02,
                    "word": "Hello,"
                },
                {
                    "conf": 1.0,
                    "end": 2.13,
                    "start": 1.84,
                    "word": "world!"
                }
            ],
            "text": "Hello, world!"
        }
    ]
    """

    def __init__(self, dir_model=None, lang='en'):
        self.model = CasePuncPredictor(os.path.join(dir_model, 'checkpoint'), lang=lang)
        self.lang = lang

    def predict(self, json_data):
        texts_ = []
        word_sums = []

        for item_ in json_data:
            texts_.append(item_['text'])
            word_sums.append(len(item_['text'].split(' ')))

        text_ = ' '.join(texts_)
        tokens_ = list(enumerate(self.model.tokenize(text_)))

        results = ''
        for token, case_label, punc_label in self.model.predict(tokens_, lambda x: x[1]):
            prediction = self.model.map_punc_label(
                self.model.map_case_label(token[1], case_label), punc_label
            )
            if token[1][0] != '#':
                results = results + ' ' + prediction
            else:
                results = results + prediction

        results = results[1:]
        if self.lang == 'ru':
            results = russian_restore_punc_cleaner(results)
        result_words = results.split(' ')

        for i in range(len(json_data)):
            if not json_data[i]['text'] == '':
                words = []
                for j in range(len(json_data[i]['result'])):
                    word = result_words.pop(0)
                    json_data[i]['result'][j]['word'] = word
                    words.append(word)
                json_data[i]['text'] = ' '.join(words)

        return json_data
