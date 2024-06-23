import json
from dbmanager import MedicalRecord

def create_appointment(medical_record, user_id, date):
    medical_record.add_appointment(user_id, date)
    return json.dumps({
        "status": "success",
        "message": f"Appointment created for {date}."
    })

def create_prescription(medical_record, user_id, medication):
    medical_record.add_prescription(user_id, medication)
    return json.dumps({
        "status": "success",
        "message": f"Prescription created for {medication}."
    })
