import os
import pyaudio
import wave
import speech_recognition as sr
import threading
from dotenv import load_dotenv
from groq import Groq
import json
import time
import asyncio
from hume import HumeStreamClient
from hume.models.config import ProsodyConfig, BurstConfig

class HumeEmotionAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = HumeStreamClient(api_key)
        self.configs = [ProsodyConfig(), BurstConfig()]

    async def analyze_emotions(self, audio_file):
        async with self.client.connect(self.configs) as socket:
            result = await socket.send_file(audio_file)
            return result

# Load environment variables
load_dotenv()

def create_appointment(date):
    return json.dumps({
        "status": "success",
        "message": f"Appointment created for {date}."
    })

def create_prescription(medication):
    return json.dumps({
        "status": "success",
        "message": f"Prescription created for {medication}."
    })

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
        self.chunk_duration = 4.5  # seconds
        self.chunk_size = int(self.rate * self.chunk_duration)

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        while self.is_recording:
            data = self.stream.read(self.chunk_size)
            with self.lock:
                self.frames = [data]  # Only keep the latest chunk

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

class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe(self, audio_file):
        with sr.AudioFile(audio_file) as source:
            audio = self.recognizer.record(source)
            try:
                return self.recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return "Google Speech Recognition could not understand audio"
            except sr.RequestError as e:
                return f"Could not request results from Google Speech Recognition service; {e}"

class TranscriptManager:
    def __init__(self):
        self.transcript = ""

    def add_to_transcript(self, text):
        self.transcript += text + " "

    def get_transcript(self):
        return self.transcript

    def save_transcript(self, filename="transcript.txt"):
        with open(filename, "w") as f:
            f.write(self.transcript)

    def load_transcript(self, filename="transcript.txt"):
        with open(filename, "r") as f:
            self.transcript = f.read()

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
            max_tokens=1024,
            temperature=0.2,
            top_p=1
        )

        return response.choices[0].message.content
    
    def summarize_bullets(self, text):
        messages = [
            {"role": "system", "content": "You are a helpful medical assistant. Summarize the given bullet points taken during a doctor's appointment into a single paragraph for the doctor to refer to later."},
            {"role": "user", "content": text}
        ]

        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            max_tokens=1024,
            temperature=0.5,
            top_p=1
        )

        return response.choices[0].message.content

    def process_summary(self, summary):
        messages = [
            {"role": "system", "content": "You are a multi-function calling LLM that helps with creating appointments and prescriptions based on a medical summary."},
            {"role": "user", "content": summary}
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_appointment",
                    "description": "Create an appointment with the given date.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "The date of the appointment (e.g. '2023-06-30')."
                            },
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_prescription",
                    "description": "Create a prescription with the given medication.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "medication": {
                                "type": "string",
                                "description": "The name of the medication."
                            },
                        },
                        "required": ["medication"]
                    }
                }
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1024
        )

        response_message = response.choices[0].message
        print(response_message)
        tool_calls = response_message.tool_calls

        # Check if the model wanted to call a function
        if tool_calls:
            available_functions = {
                "create_appointment": create_appointment,
                "create_prescription": create_prescription
            }
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                print(json.loads(function_response)["message"])

class RealTimeProcessor:
    def __init__(self, audio_recorder, groq_client, hume_emotion_analyzer):
        self.audio_recorder = audio_recorder
        self.speech_recognizer = sr.Recognizer()
        self.groq_client = groq_client
        self.hume_emotion_analyzer = hume_emotion_analyzer
        self.running = False
        self.transcript_manager = TranscriptManager()
        self.loop = asyncio.get_event_loop()

    async def process_audio(self):
        while self.running:
            chunk = self.audio_recorder.get_chunk()
            if chunk:
                audio_file = self.save_chunk_to_file(chunk)
                text = self.transcribe_audio(audio_file)
                if text:
                    summary = self.groq_client.summarize(text)
                    self.append_to_file(summary)
                    self.transcript_manager.add_to_transcript(text)
                    emotions = await self.hume_emotion_analyzer.analyze_emotions(audio_file)
                    self.handle_emotions(emotions)
                await asyncio.sleep(3) # Process every 3 seconds

    def handle_emotions(self, emotions):
        # Process and log the emotional analysis results
        print("Emotional Analysis Results:", emotions)

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

class Listener:
    def __init__(self):
        self.audio_recorder = AudioRecorder()
        self.groq_client = GroqClient()
        self.hume_emotion_analyzer = HumeEmotionAnalyzer(api_key=os.getenv('HUME_API_KEY'))
        self.real_time_processor = RealTimeProcessor(self.audio_recorder, self.groq_client, self.hume_emotion_analyzer)
        self.recording_thread = threading.Thread(target=self.audio_recorder.start_recording)

    def start(self):
        print("Recording started. Press 'q' and then Enter to stop.")
        self.recording_thread.start()
        self.real_time_processor.start()
        while True:
            key = input()
            if key == 'q':
                break
        self.audio_recorder.stop_recording()
        self.real_time_processor.stop()
        print("Recording stopped.")

        # Post-processing after recording stops
        transcript = self.real_time_processor.transcript_manager.get_transcript()
        print("Transcript:", transcript)
        bullets_path = "summary.txt"
        with open(bullets_path, 'r') as file:
            bullet_points = file.read()

        # Generate paragraph summary from transcript
        print("Summarizing the entire conversation...")
        paragraph_summary = self.groq_client.summarize_bullets(bullet_points)
        print("Paragraph Summary:", paragraph_summary)

        # Process the paragraph summary to create appointments and prescriptions
        print("Processing paragraph summary to create appointments and prescriptions...")
        self.groq_client.process_summary(paragraph_summary)

        self.audio_recorder.terminate()
        print("Summary saved to summary.txt")

if __name__ == "__main__":
    listener = Listener()
    listener.start()