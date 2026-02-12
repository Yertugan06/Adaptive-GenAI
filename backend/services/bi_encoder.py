import torch.nn.functional as F
import torch

from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from typing import List

device = "cuda" if torch.cuda.is_available() else "cpu"
model = AutoModel.from_pretrained("backend/ml_models/multilingual-e5-base").to(device)
tokenizer = AutoTokenizer.from_pretrained("backend/ml_models/multilingual-e5-base")

def average_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

def create_embedding(input_text : str) -> List[float]:
    batch_dict = tokenizer([input_text], max_length=512, padding=True, truncation=True, return_tensors='pt')

    batch_dict = {k: v.to(device) for k, v in batch_dict.items()}
    outputs = model(**batch_dict)
    embedding = average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
    embedding = F.normalize(embedding, p=2, dim=1)

    return embedding[0].cpu().tolist()

def count_tokens(text: str) -> int:
    tokens = tokenizer.encode(text)
    return len(tokens)

if __name__ == "__main__":
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CrossEncoder device: {model.device}")
    test_pairs = [
        ("I love this movie", "I do not love this movie"),               
        ("The dog bit the man", "The man bit the dog"),                 
        ("A cat is sleeping on the rug", "The feline is napping on the carpet"), 
        ("He went to the bank to deposit money", "He sat on the river bank") 
    ]

    print(f"{'Sentence A':<40} | {'Sentence B':<40} | {'Score'}")
    print("-" * 100)

    for s1, s2 in test_pairs:
        emb1 = torch.tensor(create_embedding(s1)).to(device)
        emb2 = torch.tensor(create_embedding(s2)).to(device)

        # Cosine similarity using torch
        score = F.cosine_similarity(emb1.unsqueeze(0), emb2.unsqueeze(0)).item()
        print(f"{s1:<40} | {s2:<40} | {score:.4f}")
