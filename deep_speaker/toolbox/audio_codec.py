import av
import numpy as np
import scipy.io.wavfile as wavfile
from io import BytesIO


def decode_audio(data):
    decoded_audio = b''
    data = BytesIO(data)
    container = av.open(data)
    resampler = av.AudioResampler('s16', 'mono', 16000)

    audio_stream = next(s for s in container.streams if s.type == 'audio')
    for packet in container.demux(audio_stream):
        for frame in packet.decode():
            frame = resampler.resample(frame)
            decoded_audio += frame.planes[0].to_bytes()

    return np.frombuffer(decoded_audio, dtype=np.int16)


def encode_wav(data):
    data_file = BytesIO()
    wavfile.write(data_file, 16000, data)
    return data_file.getvalue()
