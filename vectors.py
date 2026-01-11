import numpy as np
from numpy import float64
from numpy.typing import NDArray
from typing import List

def cosine_similarity(vec_a:  NDArray[float64], vec_b: NDArray[float64]) -> float:    
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return np.dot(vec_a, vec_b) / (norm_a * norm_b)

def get_signal_probability(post_vector: NDArray[float64], high_anchors_vectors: List[NDArray[float64]], low_anchors_vectors: List[NDArray[float64]]) -> tuple[float, float, float]:
    high_score = np.max([np.dot(post_vector, anchor) for anchor in high_anchors_vectors])
    
    low_score = np.max([np.dot(post_vector, anchor) for anchor in low_anchors_vectors])
    
    temperature = 0.05
    scores = np.array([high_score, low_score])
    
    exp_scores = np.exp(scores / temperature)
    probs = exp_scores / np.sum(exp_scores)
    
    return probs[0], high_score, low_score
