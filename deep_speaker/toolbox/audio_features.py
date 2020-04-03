import numpy as np
from scipy.fftpack import dct


def pre_emphasis(data, pre_emphasis=0.97):
    return np.append(data[0], data[1:] - pre_emphasis * data[:-1])


def frame(data, sample_rate=16000, frame_size=0.025, frame_stride=0.01):
    frame_length, frame_step = frame_size * sample_rate, frame_stride * sample_rate  # Convert from seconds to samples
    signal_length = len(data)
    frame_length = int(round(frame_length))
    frame_step = int(round(frame_step))
    num_frames = int(np.ceil(float(np.abs(signal_length - frame_length)) / frame_step))  # Make sure that we have at least 1 frame

    pad_signal_length = num_frames * frame_step + frame_length
    z = np.zeros((pad_signal_length - signal_length))
    pad_signal = np.append(data, z) # Pad Signal to make sure that all frames have equal number of samples without truncating any samples from the original signal

    indices = np.tile(np.arange(0, frame_length), (num_frames, 1)) + np.tile(np.arange(0, num_frames * frame_step, frame_step), (frame_length, 1)).T
    frames = pad_signal[indices.astype(np.int32, copy=False)]
    return frames, frame_length


def filter_banks(data, sample_rate=16000, nfilt=40, nfft=512):
    low_freq_mel = 0
    high_freq_mel = (2595 * np.log10(1 + (sample_rate / 2) / 700))  # Convert Hz to Mel
    mel_points = np.linspace(low_freq_mel, high_freq_mel, nfilt + 2)  # Equally spaced in Mel scale
    hz_points = (700 * (10**(mel_points / 2595) - 1))  # Convert Mel to Hz
    bin = np.floor((nfft + 1) * hz_points / sample_rate)

    fbank = np.zeros((nfilt, int(np.floor(nfft / 2 + 1))))
    for m in range(1, nfilt + 1):
        f_m_minus = int(bin[m - 1])   # left
        f_m = int(bin[m])             # center
        f_m_plus = int(bin[m + 1])    # right

        for k in range(f_m_minus, f_m):
            fbank[m - 1, k] = (k - bin[m - 1]) / (bin[m] - bin[m - 1])
        for k in range(f_m, f_m_plus):
            fbank[m - 1, k] = (bin[m + 1] - k) / (bin[m + 1] - bin[m])
    filter_banks = np.dot(data, fbank.T)
    filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)  # Numerical Stability
    filter_banks = 20 * np.log10(filter_banks)  # dB
    return filter_banks


def compute_filter_bank(data, nfft=512, nfilt=64):
    data = pre_emphasis(data)
    data, frame_length = frame(data)
    data *= np.hamming(frame_length)
    data = np.absolute(np.fft.rfft(data, nfft))  # Magnitude of the FFT
    data = ((1.0 / nfft) * ((data) ** 2))  # Power Spectrum
    data = filter_banks(data, nfilt=nfilt, nfft=nfft)
    return data


def compute_mfcc(data, nfft=512, nfilt=64, num_ceps=20, cep_lifter=22):
    data = pre_emphasis(data)
    data, frame_length = frame(data)
    data *= np.hamming(frame_length)
    data = np.absolute(np.fft.rfft(data, nfft))  # Magnitude of the FFT
    data = ((1.0 / nfft) * ((data) ** 2))  # Power Spectrum
    data = filter_banks(data, nfilt=nfilt, nfft=nfft)
    data = dct(data, type=2, axis=1, norm='ortho')[:, 1:(num_ceps + 1)]  # mfcc

    # liftering
    (nframes, ncoeff) = data.shape
    n = np.arange(ncoeff)
    lift = 1 + (cep_lifter / 2) * np.sin(np.pi * n / cep_lifter)
    data *= lift

    return data

