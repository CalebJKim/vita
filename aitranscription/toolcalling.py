import os
import json
from groq import Groq
from dbhandler import DatabaseHandler

client = Groq(api_key='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')
MODEL = 'llama3-70b-8192'

# Example function to update patient information in the database
def update_patient_info(patient_id, field, value):
    db_handler = DatabaseHandler()
    db_handler.update_patient_info(patient_id, field, value)
    return json.dumps({"status": "success", "patient_id": patient_id, "field": field, "value": value})

def run_conversation(user_prompt):
    # Step 1: send the conversation and available functions to the model
    messages=[
        {
            "role": "system",
            "content": "You are a function calling LLM that updates patient records based on the conversation. Only take notes on medically relevant information."
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "update_patient_info",
                "description": "Update specific fields in the patient's record based on the notes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The ID of the patient."
                        },
                        "field": {
                            "type": "string",
                            "description": "The field in the patient's record to update."
                        },
                        "value": {
                            "type": "string",
                            "description": "The value to update the field with."
                        }
                    },
                    "required": ["patient_id", "field", "value"]
                }
            }
        }
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        available_functions = {
            "update_patient_info": update_patient_info,
        }
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                patient_id=function_args.get("patient_id"),
                field=function_args.get("field"),
                value=function_args.get("value")
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        second_response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )  # get a new response from the model where it can see the function response
        return second_response.choices[0].message.content

user_prompt = "Patient reports experiencing chest pain and shortness of breath."
print(run_conversation(user_prompt))
