import speech_recognition as sr
from transcriptmanager import TranscriptManager
import time
import wave
import threading

class RealTimeProcessor:
    def __init__(self, audio_recorder, groq_client):
        self.audio_recorder = audio_recorder
        self.speech_recognizer = sr.Recognizer()
        self.groq_client = groq_client
        self.running = False
        self.transcript_manager = TranscriptManager()

    def process_audio(self):
        while self.running:
            chunk = self.audio_recorder.get_chunk()
            if chunk:
                audio_file = self.save_chunk_to_file(chunk)
                text = self.transcribe_audio(audio_file)
                if text:
                    summary = self.groq_client.summarize(text)
                    self.append_to_file(summary)
                    self.transcript_manager.add_to_transcript(text)
            time.sleep(3)  # Process every 3 seconds

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
        self.thread = threading.Thread(target=self.process_audio)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
