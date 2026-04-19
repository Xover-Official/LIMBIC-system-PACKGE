import faiss
import numpy as np
import os

class VectorStore:
    def __init__(self, dimension=128, index_path="data/hippocampus.index"):
        self.dimension = dimension
        self.index_path = index_path
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        else:
            self.index = faiss.IndexFlatL2(dimension)
        self.metadata = [] # Simple list to store associated data

    def add(self, embedding, data):
        embedding = np.array([embedding]).astype('float32')
        self.index.add(embedding)
        self.metadata.append(data)
        faiss.write_index(self.index, self.index_path)

    def search(self, embedding, k=5):
        embedding = np.array([embedding]).astype('float32')
        distances, indices = self.index.search(embedding, k)
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx != -1 and idx < len(self.metadata):
                results.append((self.metadata[idx], distances[0][i]))
        return results
