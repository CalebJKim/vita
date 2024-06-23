from groq import Groq
import json
import os

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