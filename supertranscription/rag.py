import os
import gspread
import json
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from groq import Groq

load_dotenv()

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
client = gspread.authorize(credentials)
spreadsheet_id = '1Ri1HVSWuwNyD5Mdr7chvcCgUWucgm7SLcQSs6rABkzE'
sheet = client.open_by_key(spreadsheet_id).sheet1

# Load data from Google Sheets
def load_data_from_sheets():
    data = {
        "user": {
            "name": sheet.cell(2, 1).value,
            "age": sheet.cell(2, 2).value,
            "height": sheet.cell(2, 3).value,
            "weight": sheet.cell(2, 4).value,
            "sex": sheet.cell(2, 5).value
        },
        "prescriptions": sheet.cell(2, 6).value.split(', '),
        "next_appointment": sheet.cell(2, 7).value,
        "conditions": sheet.cell(2, 8).value.split(', '),
        "appointments": [
            {
                "date": line.split(": ")[0],
                "summary": line.split(": ")
            }
            for line in sheet.cell(2, 9).value.split('\n')
        ],
        "emotional_states": [
            {
                "date": line.split(": ")[0],
                "emotion": line.split(": ")[1]
            }
            for line in sheet.cell(2, 10).value.split('\n')
        ]
    }
    return data

# Initialize GroqClient
class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama3-8b-8192'
    
    def answer_question(self, context, question):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context: {context}"},
            {"role": "user", "content": f"Question: {question}"}
        ]
        
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            max_tokens=150,
            temperature=0.7,
            top_p=1
        )
        
        return response.choices[0].message.content.strip()

if __name__ == "__main__":
    data = load_data_from_sheets()
    groq_client = GroqClient()
    
    context = json.dumps(data, indent=2)
    print("Data loaded from Google Sheets into GroqClient context.")
    print(context)
    
    while True:
        question = input("Ask a question about the data (or type 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        answer = groq_client.answer_question(context, question)
        print("Answer:", answer)
