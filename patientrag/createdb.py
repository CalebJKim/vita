import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import AsyncGroq
import asyncio
import json

class FAISSDatabase:
    def __init__(self, index_file, metadata_file):
        self.index_file = index_file
        self.metadata_file = metadata_file
        self.dimension = 384  # Dimension of the vectors, should match the encoder output
        self.index = self._load_or_create_index()
        self.metadata = self._load_or_create_metadata()

    def _load_or_create_index(self):
        if os.path.exists(self.index_file):
            print("Loading existing index...")
            return faiss.read_index(self.index_file)
        else:
            print("Creating new index...")
            index = faiss.IndexFlatL2(self.dimension)  # L2 distance index
            self._create_sample_data(index)
            faiss.write_index(index, self.index_file)
            return index

    def _load_or_create_metadata(self):
        if os.path.exists(self.metadata_file):
            print("Loading existing metadata...")
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        else:
            print("Creating new metadata...")
            metadata = self._create_sample_metadata()
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f)
            return metadata

    def _create_sample_data(self, index):
        print("Adding sample data to index...")
        vectors = np.random.rand(10, self.dimension).astype('float32')
        index.add(vectors)

    def _create_sample_metadata(self):
        print("Creating sample metadata...")
        return [
            {"text": f"retrieved text {i+1}", "source": f"source {i+1}"}
            for i in range(10)
        ]

    async def query(self, query_embeddings, top_k=5):
        D, I = self.index.search(np.array([query_embeddings]), k=top_k)
        matches = [self.metadata[i] for i in I[0]]
        return matches


class QueryEncoder:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        print("Loading Sentence Transformer model...")
        self.model = SentenceTransformer(model_name)

    async def encode(self, query):
        print("Encoding query...")
        return self.model.encode(query)


class GroqAPI:
    def __init__(self, model_name='llama3-8b-8192'):
        self.client = AsyncGroq()
        self.model_name = model_name

    async def get_response(self, user_prompt, system_prompt):
        stream = await self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.model_name,
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=True
        )

        response = ""
        async for chunk in stream:
            response += chunk.choices[0].delta.content
        return response


class RAGSystem:
    def __init__(self, faiss_db, query_encoder, groq_api):
        self.faiss_db = faiss_db
        self.query_encoder = query_encoder
        self.groq_api = groq_api

    def generate_system_prompt(self, matched_info, sources):
        return f"""
        Instructions:
        - Be helpful and answer questions concisely. If you don't know the answer, say 'I don't know'
        - Utilize the context provided for accurate and specific information.
        - Incorporate your preexisting knowledge to enhance the depth and relevance of your response.
        - Cite your sources
        Context: {matched_info} and the sources: {sources}
        """

    async def get_response(self, user_query):
        query_embeddings = await self.query_encoder.encode(user_query)
        matches = await self.faiss_db.query(query_embeddings)
        matched_info = ' '.join(item['text'] for item in matches)
        sources = [item['source'] for item in matches]
        system_prompt = self.generate_system_prompt(matched_info, sources)
        return await self.groq_api.get_response(user_query, system_prompt)


# Usage example
async def main():
    faiss_db = FAISSDatabase('name-of-index.faiss', 'metadata-file.json')
    query_encoder = QueryEncoder()
    groq_api = GroqAPI()

    rag_system = RAGSystem(faiss_db, query_encoder, groq_api)
    user_query = "Explain the importance of fast language models"
    response = await rag_system.get_response(user_query)
    print(response)

# Run the async main function
asyncio.run(main())
