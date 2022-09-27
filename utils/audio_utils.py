import numpy as np


def detect_leading_silence(sound, silence_threshold=-30.0, chunk_size=10):
    """
        sound is a pydub.AudioSegment
        silence_threshold in dB
        chunk_size in ms

        iterate over chunks until you find the first one with sound
    """

    trim_ms = 0  # ms
    silence_threshold = sound.dBFS + silence_threshold

    assert chunk_size > 0  # to avoid infinite loop
    while sound[trim_ms:trim_ms + chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms


def normalize_audio(samples, gain):
    # Calculate mean and std gain for every file
    means = []
    stds = []
    for gains in gain:
        means.append(np.mean(gains))
        stds.append(np.std(gains))

    # Rescale gain to common mean and std
    samples_norm = []
    for samples_film, mean, std in zip(samples, means, stds):
        samples_norm.append(
            [s - (s.dBFS - (np.mean(stds) * ((s.dBFS - mean) / std) + np.mean(means))) for s in samples_film])

    return samples_norm
