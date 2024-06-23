import sqlite3
import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

DATABASE_FILE = 'medical_records.db'

# Setting up Google Sheets API
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# DatabaseManager class to handle all database operations
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    height REAL,
                    weight REAL,
                    sex TEXT
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS prescriptions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    medication TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS conditions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    condition TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

    def add_user(self, name, age, height, weight, sex):
        with self.conn:
            self.conn.execute('''
                INSERT INTO users (name, age, height, weight, sex) 
                VALUES (?, ?, ?, ?, ?)
            ''', (name, age, height, weight, sex))

    def add_prescription(self, user_id, medication):
        with self.conn:
            self.conn.execute('''
                INSERT INTO prescriptions (user_id, medication)
                VALUES (?, ?)
            ''', (user_id, medication))

    def add_appointment(self, user_id, date):
        with self.conn:
            self.conn.execute('''
                INSERT INTO appointments (user_id, date)
                VALUES (?, ?, ?)
            ''', (user_id, date))

    def add_condition(self, user_id, condition):
        with self.conn:
            self.conn.execute('''
                INSERT INTO conditions (user_id, condition)
                VALUES (?, ?)
            ''', (user_id, condition))

    def get_user(self, user_id):
        user = self.conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        prescriptions = self.conn.execute('SELECT medication FROM prescriptions WHERE user_id = ?', (user_id,)).fetchall()
        appointments = self.conn.execute('SELECT date, summary FROM appointments WHERE user_id = ?', (user_id,)).fetchall()
        conditions = self.conn.execute('SELECT condition FROM conditions WHERE user_id = ?', (user_id,)).fetchall()
        return user, prescriptions, appointments, conditions

# User class to represent a user
class User:
    def __init__(self, user_id, name, age, height, weight, sex):
        self.user_id = user_id
        self.name = name
        self.age = age
        self.height = height
        self.weight = weight
        self.sex = sex

# Appointment class to represent an appointment
class Appointment:
    def __init__(self, user_id, date):
        self.user_id = user_id
        self.date = date

# MedicalRecord class to handle adding and updating records
class MedicalRecord:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_user(self, name, age, height, weight, sex):
        self.db_manager.add_user(name, age, height, weight, sex)

    def add_prescription(self, user_id, medication):
        self.db_manager.add_prescription(user_id, medication)

    def add_appointment(self, user_id, date):
        self.db_manager.add_appointment(user_id, date)

    def add_condition(self, user_id, condition):
        self.db_manager.add_condition(user_id, condition)

    def get_user_record(self, user_id):
        return self.db_manager.get_user(user_id)

    def visualize_data(self):
        # Implement Google Sheets integration for visualization
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)

        # The ID and range of a sample spreadsheet.
        SAMPLE_SPREADSHEET_ID = '1Ri1HVSWuwNyD5Mdr7chvcCgUWucgm7SLcQSs6rABkzE'
        SAMPLE_RANGE_NAME = 'Sheet1!A1'

        user_records = self.db_manager.conn.execute('SELECT * FROM users').fetchall()
        values = [['ID', 'Name', 'Age', 'Height', 'Weight', 'Sex']]
        for record in user_records:
            values.append(list(record))

        data = {'values': values}
        service.spreadsheets().values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=SAMPLE_RANGE_NAME,
            valueInputOption='RAW',
            body=data
        ).execute()

if __name__ == "__main__":
    db_manager = DatabaseManager()
    medical_record = MedicalRecord(db_manager)

    # Example usage
    medical_record.add_user("John Doe", 30, 175.3, 70.5, "Male")
    user_id = 1
    medical_record.add_prescription(user_id, "")
    medical_record.add_appointment(user_id, "")
    medical_record.add_condition(user_id, "")

    user, prescriptions, appointments, conditions = medical_record.get_user_record(user_id)
    print("User:", user)
    print("Prescriptions:", prescriptions)
    print("Appointments:", appointments)
    print("Conditions:", conditions)

    # Visualize data in Google Sheets
    medical_record.visualize_data()
