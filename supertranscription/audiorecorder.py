import pyaudio
import threading

class AudioRecorder:
    def __init__(self):
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.sample_format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  frames_per_buffer=self.chunk,
                                  input=True)
        self.frames = []
        self.is_recording = False
        self.lock = threading.Lock()

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        while self.is_recording:
            data = self.stream.read(self.chunk)
            with self.lock:
                self.frames.append(data)

    def get_chunk(self):
        with self.lock:
            chunk = b''.join(self.frames)
            self.frames = []
        return chunk

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()

    def terminate(self):
        self.stream.close()
        self.p.terminate()