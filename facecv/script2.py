import cv2
from deepface import DeepFace
import numpy as np
from facedatamanager import FaceDatabaseManager

# Initialize the FaceDatabaseManager
db_manager = FaceDatabaseManager(db_path="face_recognition.db")

# Load the face image from a file
face_image_path = "bjordan.jpg"  # Replace with the path to your face image
face_img = cv2.imread(face_image_path)

if face_img is None:
    print("Failed to load the face image.")
else:
    # Preprocess the face image
    def preprocess_face(face_img):
        try:
            face_img = cv2.resize(face_img, (160, 160))
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            face_img = face_img.astype(np.float32) / 255.0  # Normalize to [0, 1]
            return face_img
        except Exception as e:
            print(f"Error in preprocessing face: {e}")
            return None

    preprocessed_face = preprocess_face(face_img)

    if preprocessed_face is not None:
        # Vectorize the face image
        def vectorize_face(face_img):
            try:
                # Using DeepFace to get face embedding
                face_embedding = DeepFace.represent(face_img, model_name="Facenet", enforce_detection=False)[0]["embedding"]
                print(f"Face embedding: {face_embedding}")
                return np.array(face_embedding)
            except Exception as e:
                print(f"Error in vectorizing face: {e}")
                return None

        face_vector = vectorize_face(preprocessed_face)

        if face_vector is not None:
            # Add the face vector to the database
            name = "Michael B Jordan"  # Replace with the name of the person
            db_manager.add_face(face_vector, name)
            print(f"Added face for {name} to the database.")
        else:
            print("Failed to vectorize the face image.")
    else:
        print("Failed to preprocess the face image.")
