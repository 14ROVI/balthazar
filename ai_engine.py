from google import genai
from google.genai.types import EmbedContentConfig
from domain.post import Post
from typing import List
import re
import numpy as np
from numpy import float64
from numpy.typing import NDArray
import joblib
from strategy import Signal

from env import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, GEMINI_EMBEDDING_LENGTH

def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors."""
    # Ensure vectors are numpy arrays and not None
    if v1 is None or v2 is None:
        return 0.0
    v1 = np.array(v1)
    v2 = np.array(v2)
    if v1.shape != v2.shape:
        # Or handle this error more gracefully
        raise ValueError("Vectors must have the same shape.")
    
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return dot_product / (norm_v1 * norm_v2)

class GeminiAnalyst:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_EMBEDDING_MODEL
        try:
            self.buy_anchors = joblib.load("buy_anchors.pkl")
            self.sell_anchors = joblib.load("sell_anchors.pkl")
            self.noise_anchors = joblib.load("noise_anchors.pkl")
        except FileNotFoundError:
            print("Anchor files not found. Please run anchors.py to create them.")
            self.buy_anchors, self.sell_anchors, self.noise_anchors = [], [], []

    async def get_embedding(self, text: str) -> NDArray[float64] | None:
        clean_text = self._clean_for_embedding(text)

        try:
            response = await self.client.aio.models.embed_content(
                model=self.model,
                contents=clean_text,
                config=EmbedContentConfig(
                    output_dimensionality=GEMINI_EMBEDDING_LENGTH,
                    task_type="CLASSIFICATION"
                )
            )
            if response.embeddings is None: return None
            embedding_values_np = np.array(response.embeddings[0].values)
            normed_embedding = embedding_values_np / np.linalg.norm(embedding_values_np)
            return normed_embedding
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None

    def get_signal_from_embedding(self, embedding: NDArray[float64]) -> Signal:
        """
        Classifies an embedding into a BUY, SELL, or HOLD signal
        by comparing it to the pre-loaded anchor embeddings.
        """
        if embedding is None or not any([len(self.buy_anchors), len(self.sell_anchors), len(self.noise_anchors)]):
            return Signal.HOLD

        # Calculate max similarity to each anchor category
        max_buy_sim = max([cosine_similarity(embedding, anchor) for anchor in self.buy_anchors], default=0)
        max_sell_sim = max([cosine_similarity(embedding, anchor) for anchor in self.sell_anchors], default=0)
        max_noise_sim = max([cosine_similarity(embedding, anchor) for anchor in self.noise_anchors], default=0)

        # Basic classifier: which anchor category is the post most similar to?
        similarities = {
            Signal.BUY: max_buy_sim,
            Signal.SELL: max_sell_sim,
            Signal.HOLD: max_noise_sim
        }

        # A minimum confidence threshold to avoid classifying pure noise
        confidence_threshold = 0.4 
        
        # Find the signal with the highest similarity
        best_signal = max(similarities, key=similarities.get)
        best_sim_score = similarities[best_signal]

        if best_sim_score < confidence_threshold:
            return Signal.HOLD

        # If it's most similar to noise, it's a HOLD
        if best_signal == Signal.HOLD and best_sim_score > max(max_buy_sim, max_sell_sim):
             return Signal.HOLD

        # Return the strongest signal (BUY or SELL)
        if max_buy_sim > max_sell_sim:
            return Signal.BUY
        else:
            return Signal.SELL

    def _clean_for_embedding(self, text: str) -> str:
        text = text.replace("\n", " ")
        # 1. STRIP MARKDOWN LINKS: [Text](url) -> Text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 2. STRIP IMAGES: ![Alt](url) -> ""
        text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)
        # 3. NUKE RAW URLS
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # 4. FIX HASHTAGS
        def split_hashtag(match):
            tag = match.group(0)[1:] # Remove #
            return " " + " ".join(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', tag))
        text = re.sub(r'#[A-Za-z0-9_]+', split_hashtag, text)
        # 5. CLEAN WHITESPACE
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    async def get_signal_for_post(self, post: Post) -> Signal:
        """High-level method to get a signal for a Post object."""
        # Construct a meaningful payload from the post
        payload = f"Post by author {post.author_id}. Content: {post.content}"
        embedding = await self.get_embedding(payload)
        return self.get_signal_from_embedding(embedding)