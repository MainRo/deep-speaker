import av
from io import BytesIO


def decode_audio(data):
    decoded_audio = []
    data = BytesIO(data)
    container = av.open(data)
    resampler = av.AudioResampler('s16', 'mono', 16000)

    audio_stream = next(s for s in container.streams if s.type == 'audio')
    for packet in container.demux(audio_stream):
        for frame in packet.decode():
            frame = resampler.resample(frame)
            decoded_audio.extend(frame.planes[0].to_bytes())

    return decoded_audio


def encode_wav(data):
    pass