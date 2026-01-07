from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class PaperProcessor:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def rank_papers(self, papers, user_interests):
        """Ranks papers based on semantic similarity to user interests."""
        interest_embedding = self.model.encode([user_interests])
        ranked_list = []

        for paper in papers:
            abstract_embedding = self.model.encode([paper['abstract']])
            similarity = cosine_similarity(interest_embedding, abstract_embedding)[0][0]
            ranked_list.append({'metadata': paper, 'similarity': float(similarity)})

        ranked_list.sort(key=lambda x: x['similarity'], reverse=True)
        return ranked_list
