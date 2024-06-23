import asyncio
import sys
import termios
import tty
from voicerecognition import VoiceRecognizer
from llmprocessor import LLMProcessor

class NoteTaker:
    def __init__(self, api_key):
        self.voice_recognizer = VoiceRecognizer()
        self.llm_processor = LLMProcessor(api_key)

    async def take_notes(self, patient_id):
        # Listen to the conversation until 'q' is pressed
        full_transcript = await self.voice_recognizer.listen_until_quit()
        # End the appointment and process the transcript
        await self.end_appointment(patient_id, full_transcript)

    async def end_appointment(self, patient_id, full_transcript):
        # Summarize the full transcript
        summary = await self.llm_processor.summarize_appointment(full_transcript)
        print(f"Appointment Summary: {summary}")
        # Handle function calls based on the summary
        await self.llm_processor.handle_function_calls(summary)

def display_all_patients():
    db_handler = DatabaseHandler()
    patients = db_handler.get_all_patients()
    for patient in patients:
        print(f"Patient ID: {patient[0]}")
        print(f"Name: {patient[1]}")
        print(f"Sex: {patient[2]}")
        print(f"Age: {patient[3]}")
        print(f"Race: {patient[4]}")
        print(f"Diagnoses: {patient[5]}")
        print(f"Conditions: {patient[6]}")
        print(f"Reason for Visit: {patient[7]}")
        print(f"Medications: {patient[8]}")
        print(f"Allergies: {patient[9]}")
        print(f"Height: {patient[10]}")
        print(f"Weight: {patient[11]}")
        print(f"Other Notes: {patient[12]}")
        print("========================================")

# Usage example
api_key = "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"
note_taker = NoteTaker(api_key)
patient_id = 1  # Example patient ID

# To start taking notes asynchronously
asyncio.run(note_taker.take_notes(patient_id))

# To end the appointment and process the summary
# asyncio.run(note_taker.end_appointment(patient_id))

# Display all patient data
# display_all_patients()
