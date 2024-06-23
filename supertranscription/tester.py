import os
import json
import pyaudio
import wave
import speech_recognition as sr
import threading
import gspread
from dotenv import load_dotenv
from groq import Groq
from oauth2client.service_account import ServiceAccountCredentials
import time

load_dotenv()

def create_appointment(date):
    db["next_appointment"] = date
    return json.dumps({
        "status": "success",
        "message": f"Next appointment scheduled for {date}.",
        "appointment": date
    })

def create_prescription(medication):
    db["prescriptions"].append(medication)
    return json.dumps({
        "status": "success",
        "message": f"Prescription created for {medication}.",
        "medication": medication
    })

def add_condition(condition):
    db["conditions"].append(condition)
    return json.dumps({
        "status": "success",
        "message": f"Condition added: {condition}.",
        "condition": condition
    })

def add_visit_summary(date, summary):
    db["appointments"].append({
        "date": date,
        "summary": summary
    })
    return json.dumps({
        "status": "success",
        "message": f"Visit summary added for {date}.",
        "summary": summary
    })

def add_emotional_state(date, emotion):
    db["emotional_states"].append({
        "date": date,
        "emotion": emotion
    })
    return json.dumps({
        "status": "success",
        "message": f"Emotional state '{emotion}' added for {date}.",
        "emotion": emotion
    })

class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama3-8b-8192'

    def summarize(self, text):
        messages = [
            {"role": "system", "content": "You are a helpful medical assistant. You will be given transcription of a conversation between a doctor and a patient. Concisely summarize relevant information such as symptoms, prescriptions, appointment schedulings, etc. in a very short single bullet point. If there is no important medical information or transcript, you must respond with only '-'."},
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

    def process_prescription(self, summary):
        messages = [
            {"role": "system", "content": "You are a multi-function calling LLM that helps with creating prescriptions based on a medical summary."},
            {"role": "user", "content": summary}
        ]
        tools = [
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
        tool_calls = response_message.tool_calls

        if tool_calls:
            available_functions = {
                "create_prescription": create_prescription
            }
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                print(json.loads(function_response)["message"])

    def process_condition(self, summary):
        messages = [
            {"role": "system", "content": "You are a multi-function calling LLM that helps with adding conditions based on a medical summary."},
            {"role": "user", "content": summary}
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_condition",
                    "description": "Add a condition or symptom.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "condition": {
                                "type": "string",
                                "description": "The condition or symptom to be added."
                            },
                        },
                        "required": ["condition"]
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
        tool_calls = response_message.tool_calls

        if tool_calls:
            available_functions = {
                "add_condition": add_condition
            }
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                print(json.loads(function_response)["message"])

    def process_appointment(self, summary):
        messages = [
            {"role": "system", "content": "You are a multi-function calling LLM that helps with creating appointments based on a medical summary."},
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
        tool_calls = response_message.tool_calls

        if tool_calls:
            available_functions = {
                "create_appointment": create_appointment
            }
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                print(json.loads(function_response)["message"])

    def process_visit_summary(self, summary, date):
        messages = [
            {"role": "system", "content": "You are a multi-function calling LLM that helps with adding visit summaries based on a medical summary."},
            {"role": "user", "content": summary}
        ]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_visit_summary",
                    "description": "Add a visit summary for the given date.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "The date of the visit (e.g. '2023-06-30')."
                            },
                            "summary": {
                                "type": "string",
                                "description": "The summary of the visit."
                            }
                        },
                        "required": ["date", "summary"]
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
        tool_calls = response_message.tool_calls

        if tool_calls:
            available_functions = {
                "add_visit_summary": add_visit_summary
            }
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                print(json.loads(function_response)["message"])

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

        transcript = self.real_time_processor.transcript_manager.get_transcript()
        print("Transcript:", transcript)

        print("Summarizing the conversation into a paragraph...")
        paragraph_summary = self.groq_client.summarize_bullets(transcript)
        print("Paragraph Summary:", paragraph_summary)

        # Adding visit summary to database
        visit_date = time.strftime("%Y-%m-%d")
        add_visit_summary(visit_date, paragraph_summary)

        print("Processing summary to create prescriptions...")
        self.groq_client.process_prescription(paragraph_summary)

        print("Processing summary to add conditions...")
        self.groq_client.process_condition(paragraph_summary)

        print("Processing summary to schedule the next appointment...")
        self.groq_client.process_appointment(paragraph_summary)

        print("Processing summary to add visit summary...")
        self.groq_client.process_visit_summary(paragraph_summary, visit_date)

        self.audio_recorder.terminate()
        print("Summary saved to summary.txt")

# Database setup
db = {
    "user": {
        "name": "sophia",
        "age": 20,
        "height": "5'6\"",
        "weight": "115 lbs",
        "sex": "Female"
    },
    "prescriptions": [],
    "next_appointment": None,
    "conditions": [],
    "appointments": [],
    "emotional_states": []
}

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(credentials)
spreadsheet_id = '1Ri1HVSWuwNyD5Mdr7chvcCgUWucgm7SLcQSs6rABkzE'
sheet = client.open_by_key(spreadsheet_id).sheet1

def update_google_sheet():
    sheet.update_acell('A1', 'Name')
    sheet.update_acell('B1', 'Age')
    sheet.update_acell('C1', 'Height')
    sheet.update_acell('D1', 'Weight')
    sheet.update_acell('E1', 'Sex')
    sheet.update_acell('F1', 'Prescriptions')
    sheet.update_acell('G1', 'Next Appointment')
    sheet.update_acell('H1', 'Conditions')
    sheet.update_acell('I1', 'Appointments')
    sheet.update_acell('J1', 'Emotional States')

    sheet.update_acell('A2', db["user"]["name"])
    sheet.update_acell('B2', db["user"]["age"])
    sheet.update_acell('C2', db["user"]["height"])
    sheet.update_acell('D2', db["user"]["weight"])
    sheet.update_acell('E2', db["user"]["sex"])
    sheet.update_acell('F2', ', '.join(db["prescriptions"]))
    sheet.update_acell('G2', db["next_appointment"])
    sheet.update_acell('H2', ', '.join(db["conditions"]))
    
    appointments = "\n".join([f'{appt["date"]}: {appt["summary"]}' for appt in db["appointments"]])
    sheet.update_acell('I2', appointments)

    emotional_states = "\n".join([f'{state["date"]}: {state["emotion"]}' for state in db["emotional_states"]])
    sheet.update_acell('J2', emotional_states)

if __name__ == "__main__":
    listener = Listener()
    listener.start()

    # Example manual call to add emotional state
    add_emotional_state(time.strftime("%Y-%m-%d"), "nervous, hopeful, relieved, tired")
    
    update_google_sheet()
