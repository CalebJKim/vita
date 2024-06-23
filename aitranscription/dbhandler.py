import sqlite3

class DatabaseHandler:
    valid_fields = {"name", "sex", "age", "race", "diagnoses", "conditions", "reason_for_visit", "medications", "allergies", "height", "weight", "other_notes"}

    def __init__(self, db_name="patient_data.db"):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY,
                name TEXT,
                sex TEXT,
                age INTEGER,
                race TEXT,
                diagnoses TEXT,
                conditions TEXT,
                reason_for_visit TEXT,
                medications TEXT,
                allergies TEXT,
                height REAL,
                weight REAL,
                other_notes TEXT
            )
        """)
        self.connection.commit()

    def update_patient_info(self, patient_id, field, value):
        if field in self.valid_fields:
            query = f"UPDATE patients SET {field} = ? WHERE id = ?"
            self.cursor.execute(query, (value, patient_id))
            self.connection.commit()
            return True
        return False

    def get_patient_info(self, patient_id):
        self.cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        return self.cursor.fetchone()

    def get_all_patients(self):
        self.cursor.execute("SELECT * FROM patients")
        return self.cursor.fetchall()
