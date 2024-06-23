import pyaudio
import threading
from dotenv import load_dotenv

load_dotenv()


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

import os
import wave
import time
from threading import Thread
import speech_recognition as sr
from groq import Groq

class RealTimeProcessor:
    def __init__(self, audio_recorder, groq_client):
        self.audio_recorder = audio_recorder
        self.speech_recognizer = sr.Recognizer()
        self.groq_client = groq_client
        self.running = False

    def process_audio(self):
        while self.running:
            chunk = self.audio_recorder.get_chunk()
            if chunk:
                audio_file = self.save_chunk_to_file(chunk)
                text = self.transcribe_audio(audio_file)
                if text:
                    summary = self.groq_client.summarize(text)
                    self.append_to_file(summary)
            time.sleep(3)  # Process every second

    def save_chunk_to_file(self, chunk):
        filename = 'temp_chunk.wav'
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.audio_recorder.channels)
            wf.setsampwidth(self.audio_recorder.p.get_sample_size(self.audio_recorder.sample_format))
            wf.setframerate(self.audio_recorder.rate)
            wf.writeframes(chunk)
        return filename

    def transcribe_audio(self, audio_file):
        with sr.AudioFile(audio_file) as source:
            audio = self.speech_recognizer.record(source)
            try:
                return self.speech_recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                return None

    def append_to_file(self, summary):
        with open("summary.txt", "a") as f:
            f.write(f"• {summary}\n")

    def start(self):
        self.running = True
        self.thread = Thread(target=self.process_audio)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama3-8b-8192'

    def summarize(self, text):
        messages = [
            {"role": "system", "content": "You are a helpful medical assistant. You will be given transcription of a conversation between a doctor and a patient. Concisely summarize relevant information such as symptoms, prescriptions, appointment schedulings, etc. in a very short single bullet point. If there is no important medical information, do not respond anything at all. If there is no conversation transcript, also do not respond anything at all."},
            {"role": "user", "content": text}
        ]

        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            max_tokens=150,
            temperature=0.5,
            top_p=1
        )

        return response.choices[0].message.content.strip()

class Listener:
    def __init__(self):
        self.audio_recorder = AudioRecorder()
        self.groq_client = GroqClient()
        self.real_time_processor = RealTimeProcessor(self.audio_recorder, self.groq_client)
        self.recording_thread = threading.Thread(target=self.audio_recorder.start_recording)

    def start(self):
        print("Recording started. Press 'q' and then Enter to stop and get the transcript.")
        self.recording_thread.start()
        self.real_time_processor.start()
        while True:
            key = input()
            if key == 'q':
                break
        self.audio_recorder.stop_recording()
        self.real_time_processor.stop()
        print("Recording stopped.")

        self.audio_recorder.terminate()
        print("Summary saved to summary.txt")

if __name__ == "__main__":
    listener = Listener()
    listener.start()
