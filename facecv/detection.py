import cv2
from deepface import DeepFace
import numpy as np
import time
from sklearn.preprocessing import normalize
from mtcnn import MTCNN
from PIL import Image

class FaceRecognizer:
    def __init__(self, db_manager):
        self.detector = MTCNN()
        self.db_manager = db_manager
        self.recent_faces = {}

    def capture_and_recognize(self):
        cap = cv2.VideoCapture(0)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            faces = self.detector.detect_faces(frame)
            print(f"Detected {len(faces)} face(s).")
            
            for face in faces:
                x, y, w, h = face['box']
                face_img = frame[y:y+h, x:x+w]
                face_img = self.preprocess_face(face_img, face['keypoints'])
                if face_img is None:
                    continue  # Skip to the next face if preprocessing failed
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                face_vector = self.vectorize_face(face_img)
                
                if face_vector is not None:
                    face_vector = normalize(face_vector.reshape(1, -1)).flatten()
                    result, distance = self.db_manager.search_face(face_vector)
                    
                    print(f"Recognition result: {result}, Distance: {distance}")
                    
                    if result and distance < 0.3:  # Even stricter threshold
                        name = result
                        cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
                        self.recent_faces[face_vector.tobytes()] = time.time()
                    else:
                        if face_vector.tobytes() not in self.recent_faces or time.time() - self.recent_faces[face_vector.tobytes()] > 5:
                            name = input("New face detected. Enter name: ")
                            num_images = int(input("Enter number of images to capture: "))
                            self.add_multiple_images(name, num_images)
                            cv2.putText(frame, "New face added", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
                            self.recent_faces[face_vector.tobytes()] = time.time()
                else:
                    print("Failed to vectorize face.")
            
            cv2.imshow('Face Recognition', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

    def add_multiple_images(self, name, num_images):
        cap = cv2.VideoCapture(0)
        collected_images = 0
        while collected_images < num_images:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            faces = self.detector.detect_faces(frame)
            print(f"Detected {len(faces)} face(s).")
            
            for face in faces:
                x, y, w, h = face['box']
                face_img = frame[y:y+h, x:x+w]
                face_img = self.preprocess_face(face_img, face['keypoints'])
                if face_img is None:
                    continue  # Skip to the next face if preprocessing failed
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                face_vector = self.vectorize_face(face_img)
                
                if face_vector is not None:
                    face_vector = normalize(face_vector.reshape(1, -1)).flatten()
                    self.db_manager.add_face(face_vector, name)
                    collected_images += 1
                    print(f"Collected {collected_images}/{num_images} images for {name}.")
                else:
                    print("Failed to vectorize face.")
            
            cv2.imshow('Face Capture', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

    def preprocess_face(self, face_img, keypoints):
        try:
            left_eye = keypoints['left_eye']
            right_eye = keypoints['right_eye']

            left_eye_center = np.array([left_eye[0], left_eye[1]], dtype=np.float32)
            right_eye_center = np.array([right_eye[0], right_eye[1]], dtype=np.float32)

            dy = right_eye_center[1] - left_eye_center[1]
            dx = right_eye_center[0] - left_eye_center[0]
            angle = np.degrees(np.arctan2(dy, dx))

            eye_center = (int((left_eye_center[0] + right_eye_center[0]) // 2),
                          int((left_eye_center[1] + right_eye_center[1]) // 2))

            print(f"Left Eye: {left_eye_center}, Right Eye: {right_eye_center}, Center: {eye_center}, Angle: {angle}")

            rotation_matrix = cv2.getRotationMatrix2D(eye_center, angle, 1.0)

            aligned_face = cv2.warpAffine(face_img, rotation_matrix, (face_img.shape[1], face_img.shape[0]))

            face_img = cv2.resize(aligned_face, (160, 160))
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            face_img = face_img.astype(np.float32) / 255.0  # Normalize to [0, 1]
            return face_img
        except Exception as e:
            print(f"Error in preprocessing face: {e}")
            return None 

    def vectorize_face(self, face_img):
        try:
            face_embedding = DeepFace.represent(face_img, model_name="Facenet", enforce_detection=False)[0]["embedding"]
            return np.array(face_embedding)
        except Exception as e:
            print(f"Error in vectorizing face: {e}")
            return None