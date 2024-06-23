import os
import pyaudio
import wave
import speech_recognition as sr
import threading
from dotenv import load_dotenv
from groq import Groq
import json

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

# Load environment variables
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

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.stream.start_stream()
        while self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()

    def save_recording(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()

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


class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama3-8b-8192'

    def summarize(self, text):
        messages = [
            {"role": "system", "content": "You are a helpful assistant specialized in medical conversations."},
            {"role": "user", "content": f"Summarize the following medical conversation: {text}"}
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
            {"role": "system", "content": "You are a function calling LLM that helps with creating appointments and prescriptions based on a medical summary."},
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
        # print(response_message)
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
    



class Listener:
    def __init__(self):
        self.audio_recorder = AudioRecorder()
        self.speech_recognizer = SpeechRecognizer()
        self.transcript_manager = TranscriptManager()
        self.groq_client = GroqClient()
        self.recording_thread = threading.Thread(target=self.audio_recorder.start_recording)

    def start(self):
        print("Recording started. Press 'q' and then Enter to stop and get the transcript.")
        self.recording_thread.start()
        while True:
            key = input()
            if key == 'q':
                break
        self.audio_recorder.stop_recording()
        print("Recording stopped. Transcribing...")

        filename = 'temp_audio.wav'
        self.audio_recorder.save_recording(filename)
        text = self.speech_recognizer.transcribe(filename)
        self.transcript_manager.add_to_transcript(text)
        print("Transcription complete.")
        transcript = self.transcript_manager.get_transcript()
        print("Transcript:", transcript)

        print("Summarizing the conversation...")
        summary = self.groq_client.summarize(transcript)
        print("Summary:", summary)

        print("Processing summary to create appointments and prescriptions...")
        self.groq_client.process_summary(summary)

        self.audio_recorder.terminate()




if __name__ == "__main__":
    listener = Listener()
    listener.start()
