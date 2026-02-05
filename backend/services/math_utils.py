
def calculate_bayesian_rating(item_reviews_count: int, item_avg_rating: float,global_avg_rating: float,min_reviews_threshold: int = 5) -> float:
    """
    Formula: (v / (v + m)) * R + (m / (v + m)) * C
    """
    total_weight = item_reviews_count + min_reviews_threshold
    
    if total_weight == 0:
        return 0.0

    item_trust_weight = item_reviews_count / total_weight
    global_trust_weight = min_reviews_threshold / total_weight

    return (item_trust_weight * item_avg_rating) + (global_trust_weight * global_avg_rating)

def determine_status(reuse_count: int, bayesian_rating: float) -> str:
    if reuse_count < 5:
        return "candidate"
    
    if bayesian_rating >= 4.0:
        return "canonical"
    
    if bayesian_rating <= 2.0:
        return "quarantine"
    
    return "DELETE"