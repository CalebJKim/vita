import faiss

faiss.init(
    api_key='xxxx',
    environment='xxxx'
)
faiss_index = faiss.Index('faiss_index.index')

