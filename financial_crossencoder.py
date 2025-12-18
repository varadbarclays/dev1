# Financial Cross-Encoder Fine-tuning for Re-ranking
# Fine-tune cross-encoder-ms-marco-MiniLM-L12-v2 on FinanceBench and FinDER

# Install required packages
!pip install -q sentence-transformers datasets transformers torch accelerate

import torch
from sentence_transformers import CrossEncoder, InputExample
from sentence_transformers.cross_encoder.evaluation import CERerankingEvaluator
from datasets import load_dataset
from torch.utils.data import DataLoader
import numpy as np
from typing import List, Tuple
import random

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

print(f"Using device: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")

# ============================================================================
# STEP 1: Load and Prepare Datasets
# ============================================================================

def load_financebench_data():
    """Load and process FinanceBench dataset"""
    print("Loading FinanceBench dataset...")
    dataset = load_dataset("PatronusAI/financebench")
    
    train_samples = []
    
    for split in dataset.keys():
        for item in dataset[split]:
            query = item.get('question', '')
            # FinanceBench has evidence as a list of dicts with evidence_text
            evidence_list = item.get('evidence', [])
            
            if query and evidence_list:
                for evidence_item in evidence_list:
                    evidence_text = evidence_item.get('evidence_text', '')
                    if evidence_text:
                        # Positive example: query matches evidence
                        train_samples.append(InputExample(texts=[query, evidence_text], label=1.0))
    
    print(f"Created {len(train_samples)} samples from FinanceBench")
    return train_samples

def load_finder_data():
    """Load and process FinDER dataset"""
    print("Loading FinDER dataset...")
    try:
        dataset = load_dataset("Linq-AI-Research/FinDER")
        
        train_samples = []
        
        for split in dataset.keys():
            for item in dataset[split]:
                # FinDER has: text (query), answer (gold answer), references (list of evidence)
                query = item.get('text', '')
                references = item.get('references', [])
                
                if query and references:
                    # Create positive samples from the references
                    for reference in references:
                        if reference:  # reference is a string
                            train_samples.append(InputExample(texts=[query, reference], label=1.0))
        
        print(f"Created {len(train_samples)} samples from FinDER")
        return train_samples
    except Exception as e:
        print(f"Error loading FinDER: {e}")
        return []

def create_hard_negatives(samples: List[InputExample], num_negatives: int = 2):
    """Create hard negative examples by pairing queries with random contexts"""
    all_contexts = [s.texts[1] for s in samples if s.label == 1.0]
    augmented_samples = list(samples)
    
    positive_samples = [s for s in samples if s.label == 1.0]
    
    for sample in positive_samples:
        query = sample.texts[0]
        # Sample random contexts as negatives
        neg_contexts = random.sample(all_contexts, min(num_negatives, len(all_contexts)))
        for neg_ctx in neg_contexts:
            if neg_ctx != sample.texts[1]:  # Don't use the same context
                augmented_samples.append(InputExample(texts=[query, neg_ctx], label=0.0))
    
    return augmented_samples

# Load both datasets
financebench_samples = load_financebench_data()
finder_samples = load_finder_data()

# Combine datasets
all_samples = financebench_samples + finder_samples
print(f"\nTotal samples before augmentation: {len(all_samples)}")

# Create hard negatives
all_samples = create_hard_negatives(all_samples, num_negatives=2)
print(f"Total samples after augmentation: {len(all_samples)}")

# Shuffle samples
random.shuffle(all_samples)

# Split into train/validation (90/10)
split_idx = int(0.9 * len(all_samples))
train_samples = all_samples[:split_idx]
val_samples = all_samples[split_idx:]

print(f"\nTraining samples: {len(train_samples)}")
print(f"Validation samples: {len(val_samples)}")

# ============================================================================
# STEP 2: Initialize Model
# ============================================================================

model_name = "cross-encoder/ms-marco-MiniLM-L-12-v2"
print(f"\nLoading pre-trained model: {model_name}")

model = CrossEncoder(
    model_name,
    num_labels=1,
    max_length=512,
    device='cuda' if torch.cuda.is_available() else 'cpu'
)

# ============================================================================
# STEP 3: Create Evaluator
# ============================================================================

def create_evaluation_data(val_samples: List[InputExample], num_queries: int = 50):
    """Create evaluation data in the format needed by CERerankingEvaluator"""
    queries = {}
    corpus = {}
    relevant_docs = {}
    
    positive_samples = [s for s in val_samples if s.label == 1.0][:num_queries]
    
    for idx, sample in enumerate(positive_samples):
        query_id = f"q{idx}"
        doc_id = f"d{idx}"
        
        queries[query_id] = sample.texts[0]
        corpus[doc_id] = sample.texts[1]
        relevant_docs[query_id] = {doc_id}
    
    return queries, corpus, relevant_docs

queries, corpus, relevant_docs = create_evaluation_data(val_samples)

evaluator = CERerankingEvaluator(
    queries=queries,
    corpus=corpus,
    relevant_docs=relevant_docs,
    name='financial-reranker-eval'
)

# ============================================================================
# STEP 4: Fine-tune Model
# ============================================================================

print("\n" + "="*60)
print("Starting Fine-tuning")
print("="*60)

# Training configuration
num_epochs = 3
train_batch_size = 16
warmup_steps = int(len(train_samples) * num_epochs * 0.1 / train_batch_size)

print(f"\nTraining Configuration:")
print(f"- Epochs: {num_epochs}")
print(f"- Batch size: {train_batch_size}")
print(f"- Warmup steps: {warmup_steps}")
print(f"- Learning rate: 2e-5")

model.fit(
    train_dataloader=DataLoader(train_samples, shuffle=True, batch_size=train_batch_size),
    evaluator=evaluator,
    epochs=num_epochs,
    warmup_steps=warmup_steps,
    output_path='./financial-cross-encoder',
    evaluation_steps=500,
    save_best_model=True,
    show_progress_bar=True,
    optimizer_params={'lr': 2e-5}
)

print("\n" + "="*60)
print("Training Complete!")
print("="*60)

# ============================================================================
# STEP 5: Test the Fine-tuned Model
# ============================================================================

print("\n" + "="*60)
print("Testing Fine-tuned Model")
print("="*60)

# Load the best model
best_model = CrossEncoder('./financial-cross-encoder', max_length=512)

# Test examples
test_queries = [
    "What was Apple's revenue growth in Q4?",
    "Explain the impact of interest rate changes on bank profitability",
    "What are the key risks mentioned in Tesla's annual report?"
]

test_passages = [
    "Apple Inc. reported a 8% year-over-year revenue increase in the fourth quarter, reaching $89.5 billion.",
    "The company's smartphone sales declined by 3% in the European market during the same period.",
    "Rising interest rates typically improve net interest margins for banks, leading to higher profitability.",
    "Tesla's 10-K filing highlights supply chain disruptions and regulatory challenges as primary risk factors.",
    "The automotive sector faces increasing competition from new electric vehicle manufacturers."
]

for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 60)
    
    # Create query-passage pairs
    pairs = [[query, passage] for passage in test_passages]
    
    # Get relevance scores
    scores = best_model.predict(pairs)
    
    # Rank passages
    ranked_indices = np.argsort(scores)[::-1]
    
    for rank, idx in enumerate(ranked_indices[:3], 1):
        print(f"{rank}. [Score: {scores[idx]:.4f}] {test_passages[idx][:100]}...")

# ============================================================================
# STEP 6: Save Model
# ============================================================================

print("\n" + "="*60)
print("Saving Model")
print("="*60)

# Save to Hugging Face Hub (optional - uncomment and add your token)
# from huggingface_hub import login
# login(token="your_hf_token_here")
# best_model.save_pretrained("your-username/financial-cross-encoder-reranker")
# best_model.push_to_hub("your-username/financial-cross-encoder-reranker")

print("\nModel saved locally to: ./financial-cross-encoder")
print("\nTo use the model for re-ranking:")
print("""
from sentence_transformers import CrossEncoder

# Load model
reranker = CrossEncoder('./financial-cross-encoder')

# Re-rank passages for a query
query = "Your financial query"
passages = ["passage 1", "passage 2", "passage 3"]
pairs = [[query, p] for p in passages]
scores = reranker.predict(pairs)

# Get ranked results
ranked_idx = np.argsort(scores)[::-1]
for idx in ranked_idx:
    print(f"Score: {scores[idx]:.4f} - {passages[idx]}")
""")