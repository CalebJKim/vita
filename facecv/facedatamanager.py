import faiss
import pickle
import numpy as np
import os

class FaceDatabaseManager:
    def __init__(self, db_path="face_recognition.db"):
        self.db_path = db_path
        self.index = faiss.IndexFlatL2(128)  # 128 is the dimension of face vectors
        self.names = []
        self.embeddings = {}

        if os.path.exists(db_path):
            with open(db_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, tuple) and len(data) == 3:
                    self.index, self.names, self.embeddings = data
                elif isinstance(data, tuple) and len(data) == 2:
                    self.index, self.names = data
                    self.embeddings = {name: [] for name in self.names}
                else:
                    print("Unknown database format. Starting fresh.")
            print(f"Loaded {len(self.names)} faces from database.")
        else:
            print("No existing database found. Starting fresh.")

    def add_face(self, face_vector, name):
        if name in self.embeddings:
            self.embeddings[name].append(face_vector)
            average_embedding = np.mean(self.embeddings[name], axis=0)
            index_pos = self.names.index(name)
            self.index.remove_ids(np.array([index_pos]))
            self.index.add(np.array([average_embedding]))
        else:
            self.index.add(np.array([face_vector]))
            self.names.append(name)
            self.embeddings[name] = [face_vector]
        self.save_database()
        print(f"Added face for {name} to database.")

    def search_face(self, face_vector, threshold=0.000003):  # Stricter threshold
        if self.index.ntotal > 0:
            D, I = self.index.search(np.array([face_vector]), 1)
            print(f"Search distances: {D}, indices: {I}")
            if D[0][0] < threshold:
                print(f"Face recognized as {self.names[I[0][0]]} with distance {D[0][0]}")
                return self.names[I[0][0]], D[0][0]
            print(f"Face not recognized, closest distance {D[0][0]} is above threshold {threshold}.")
        return None, None

    def save_database(self):
        with open(self.db_path, 'wb') as f:
            pickle.dump((self.index, self.names, self.embeddings), f)
        print("Database saved.")