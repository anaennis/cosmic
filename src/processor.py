from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class PaperProcessor:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """Initializes the transformer model for embedding generation."""
        self.model = SentenceTransformer(model_name)

    def rank_papers(self, papers, user_interests):
        """
        Ranks papers based on semantic similarity to user interests using 
        vectorized batch processing.
        """
        if not papers:
            return []

        # 1. Batch encode all abstracts at once (Efficiency: O(1) model call)
        abstracts = [paper['abstract'] for paper in papers]
        
        # interest_embedding shape: (1, embedding_dim)
        # abstract_embeddings shape: (num_papers, embedding_dim)
        interest_embedding = self.model.encode([user_interests])
        abstract_embeddings = self.model.encode(abstracts)

        # 2. Compute similarities in one vectorized operation
        # This returns a 2D array: (1, num_papers)
        similarities = cosine_similarity(interest_embedding, abstract_embeddings)[0]

        # 3. Reconstruct the list with scores
        ranked_list = []
        for i, paper in enumerate(papers):
            ranked_list.append({
                'metadata': paper, 
                'similarity': float(similarities[i])
            })

        # 4. Sort by highest similarity
        ranked_list.sort(key=lambda x: x['similarity'], reverse=True)
        return ranked_list