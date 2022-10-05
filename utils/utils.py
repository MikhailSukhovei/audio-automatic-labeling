import os
import re
import glob
import wave
import contextlib
import pandas as pd
import numpy as np


def words_count(txt):
    txt = txt.lower()
    txt = re.sub('[,.!?]', '', txt)
    return len(txt.split(' '))


def char_count(txt):
    return len(txt)


def distinct_words_count(text_series):
    text_series = text_series.apply(lambda x: re.sub('[,.!?]', '', x))
    results = set()
    text_series.str.lower().str.split().apply(results.update)
    return len(results)


def format_time(time_sec):
    hours = int(time_sec // 3600)
    minutes = int((time_sec - 3600 * hours) // 60)
    seconds = int(time_sec - 3600 * hours - 60 * minutes)
    return "%s:%s:%s" % (str(hours).zfill(2), str(minutes).zfill(2), str(seconds).zfill(2))


def format_number(number):
    return f"{number:,}"


def dataset_stat(audio_dir, metadata_dir, stat_dir):
    """
    Total Clips	        13,100
    Total Words	        225,715
    Total Characters	1,308,678
    Total Duration	    23:55:17
    Mean Clip Duration	6.57 sec
    Min Clip Duration	1.11 sec
    Max Clip Duration	10.10 sec
    Mean Words per Clip	17.23
    Distinct Words	    13,821
    """
    audio_paths = glob.glob(os.path.join(audio_dir, '*.wav'))
    sample_durations = []
    for path in audio_paths:
        with contextlib.closing(wave.open(path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            sample_durations.append(duration)

    metadata = pd.read_csv(metadata_dir, sep='|', header=None)
    metadata['words'] = metadata[1].apply(words_count)
    metadata['chars'] = metadata[1].apply(char_count)

    total_clips = len(audio_paths)
    total_words = np.sum(metadata['words'].values)
    total_characters = np.sum(metadata['chars'].values)
    total_duration = np.sum(sample_durations)
    mean_clip_duration = np.mean(sample_durations)
    min_clip_duration = np.min(sample_durations)
    max_lip_duration = np.max(sample_durations)
    mean_words_per_clip = np.mean(metadata['words'].values)
    distinct_words = distinct_words_count(metadata[1])

    with contextlib.closing(open(stat_dir, 'w')) as stat_file:
        print("Total Clips", format_number(total_clips), file=stat_file)
        print("Total Words", format_number(total_words), file=stat_file)
        print("Total Characters", format_number(total_characters), file=stat_file)
        print("Total Duration", format_time(total_duration), file=stat_file)
        print("Mean Clip Duration", "%.2f" % mean_clip_duration, "sec", file=stat_file)
        print("Min Clip Duration", "%.2f" % min_clip_duration, "sec", file=stat_file)
        print("Max Clip Duration", "%.2f" % max_lip_duration, "sec", file=stat_file)
        print("Mean Words per Clip", "%.2f" % mean_words_per_clip, file=stat_file)
        print("Distinct Words", format_number(distinct_words), file=stat_file)
