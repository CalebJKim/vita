from facedatamanager import FaceDatabaseManager
from detection import FaceRecognizer

if __name__ == "__main__":
    db_manager = FaceDatabaseManager()
    recognizer = FaceRecognizer(db_manager)
    recognizer.capture_and_recognize()
