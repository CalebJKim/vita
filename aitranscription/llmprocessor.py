import os
import json
from groq import Groq
from dbhandler import DatabaseHandler

client = Groq(api_key='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')
MODEL = 'llama3-70b-8192'

def update_patient_info(patient_id, field, value):
    db_handler = DatabaseHandler()
    result = db_handler.update_patient_info(patient_id, field, value)
    print(f"Update Patient Info - Patient ID: {patient_id}, Field: {field}, Value: {value}, Result: {result}")
    if result:
        return json.dumps({"status": "success", "patient_id": patient_id, "field": field, "value": value})
    else:
        return json.dumps({"status": "error", "message": "Invalid field", "field": field})

def prescribe_medication(patient_id, medication):
    print(f"Prescribing medication {medication} to patient ID {patient_id}")
    return json.dumps({"status": "success", "patient_id": patient_id, "medication": medication})

def schedule_checkup(patient_id, date):
    print(f"Scheduling check-up for patient ID {patient_id} on {date}")
    return json.dumps({"status": "success", "patient_id": patient_id, "date": date})

class LLMProcessor:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    async def summarize_appointment(self, full_transcript):
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Summarize the following appointment in a paragraph, extracting all relevant symptoms and context:"},
                {"role": "user", "content": full_transcript}
            ],
            model="llama3-70b-8192",
            max_tokens=200,
            temperature=0.5
        )

        if response.choices and response.choices[0].message.content:
            summary = response.choices[0].message.content.strip()
            return summary
        return ""

    async def handle_function_calls(self, summary):
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Based on the following summary, perform necessary function calls to update patient records, prescribe medication, and schedule check-ups:"},
                {"role": "user", "content": summary}
            ],
            model="llama3-70b-8192",
            max_tokens=150,
            temperature=0.5,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "update_patient_info",
                        "description": "Update specific fields in the patient's record based on the notes.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "patient_id": {"type": "integer"},
                                "field": {"type": "string", "enum": list(DatabaseHandler.valid_fields)},
                                "value": {"type": "string"}
                            },
                            "required": ["patient_id", "field", "value"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "prescribe_medication",
                        "description": "Prescribe medication to the patient.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "patient_id": {"type": "integer"},
                                "medication": {"type": "string"}
                            },
                            "required": ["patient_id", "medication"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "schedule_checkup",
                        "description": "Schedule the next check-up for the patient.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "patient_id": {"type": "integer"},
                                "date": {"type": "string"}
                            },
                            "required": ["patient_id", "date"]
                        }
                    }
                }
            ],
            tool_choice="auto"
        )

        if response.choices and response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                if function_name == "update_patient_info":
                    result = update_patient_info(arguments["patient_id"], arguments["field"], arguments["value"])
                elif function_name == "prescribe_medication":
                    result = prescribe_medication(arguments["patient_id"], arguments["medication"])
                elif function_name == "schedule_checkup":
                    result = schedule_checkup(arguments["patient_id"], arguments["date"])
                print(f"Tool Call Result: {result}")
