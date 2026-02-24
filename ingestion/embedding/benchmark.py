"""
Embedding Model Benchmark for EU Fact Force

Compares multilingual embedding models on the project's scientific corpus.
Evaluates retrieval quality (Precision@k, MRR), cross-language capability,
and practical metrics (speed, dimensions).
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

EXTRACTED_TEXTS_DIR = Path(__file__).parent.parent / "parsing" / "output" / "extracted_texts"
OUTPUT_DIR = Path(__file__).parent / "output"
GROUND_TRUTH_PATH = Path(__file__).parent / "data" / "ground_truth.json"
CHUNK_SIZE_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200

CANDIDATE_MODELS = {
    "multilingual-e5-base": {
        "model_id": "intfloat/multilingual-e5-base",
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
    "bge-m3": {
        "model_id": "BAAI/bge-m3",
        "query_prefix": "",
        "passage_prefix": "",
    },
    "labse": {
        "model_id": "sentence-transformers/LaBSE",
        "query_prefix": "",
        "passage_prefix": "",
    },
}

def load_documents() -> dict[str, str]:
    """Load the LlamaParse markdown extractions (base variant, no clean/column)."""
    docs = {}
    for path in sorted(EXTRACTED_TEXTS_DIR.glob("*__llamaparse_markdown.txt")):
        doc_id = path.stem.replace("__llamaparse_markdown", "")
        text = path.read_text(encoding="utf-8").strip()
        if text:
            docs[doc_id] = text
    print(f"Loaded {len(docs)} documents:")
    for doc_id in docs:
        print(f"  - {doc_id} ({len(docs[doc_id]):,} chars)")
    return docs


def load_ground_truth(path: Path = GROUND_TRUTH_PATH) -> list[dict]:
    """Load and validate benchmark ground truth queries."""
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Ground truth must be a JSON array of query objects.")

    required_keys = {"query", "lang", "relevant_docs"}
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Ground truth item at index {idx} must be an object.")
        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(
                f"Ground truth item at index {idx} missing keys: {sorted(missing)}"
            )
        if not isinstance(item["relevant_docs"], list) or not item["relevant_docs"]:
            raise ValueError(
                f"Ground truth item at index {idx} must have a non-empty relevant_docs list."
            )

    print(f"Loaded {len(data)} ground-truth queries from {path}")
    return data


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """Split text into overlapping fixed-size character chunks."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be strictly greater than overlap.")
    chunks: list[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_len:
            break
        start = end - overlap
    return chunks


def build_chunks(docs: dict[str, str]) -> list[dict]:
    """Build chunk records with document and position metadata."""
    chunk_records: list[dict] = []
    for doc_id, text in docs.items():
        doc_chunks = chunk_text(text)
        for idx, chunk in enumerate(doc_chunks):
            chunk_records.append(
                {
                    "chunk_id": f"{doc_id}::chunk_{idx}",
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "text": chunk,
                }
            )
    print(
        f"Built {len(chunk_records)} chunks "
        f"(size={CHUNK_SIZE_CHARS}, overlap={CHUNK_OVERLAP_CHARS})"
    )
    return chunk_records


def load_model(model_config: dict):
    """Load an embedding model via sentence-transformers."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_config["model_id"])


def embed_texts(model, texts: list[str], model_config: dict) -> np.ndarray:
    """Embed a list of texts using the given model."""
    prefix = model_config.get("passage_prefix", "")
    prefixed = [f"{prefix}{t}" for t in texts]
    return model.encode(prefixed, show_progress_bar=False, normalize_embeddings=True)


def embed_queries(model, queries: list[str], model_config: dict) -> np.ndarray:
    """Embed queries (may use different prefix than passages)."""
    prefix = model_config.get("query_prefix", "")
    prefixed = [f"{prefix}{q}" for q in queries]
    return model.encode(prefixed, show_progress_bar=False, normalize_embeddings=True)


def compute_retrieval_metrics(
    query_embeddings: np.ndarray,
    chunk_embeddings: np.ndarray,
    chunks: list[dict],
    ground_truth: list[dict],
    k_values: list[int] = [3, 5, 10],
) -> dict:
    """
    Compute Precision@k and MRR from chunk retrieval.

    We retrieve by chunk vectors, then collapse ranked chunks to unique ranked docs
    for evaluation against doc-level relevance labels.
    """
    sim_matrix = cosine_similarity(query_embeddings, chunk_embeddings)

    metrics = {f"precision@{k}": [] for k in k_values}
    metrics["mrr"] = []
    per_query_results = []

    for i, gt in enumerate(ground_truth):
        scores = sim_matrix[i]
        ranked_indices = np.argsort(scores)[::-1]
        ranked_chunks = [chunks[idx] for idx in ranked_indices]
        ranked_docs: list[str] = []
        seen_docs = set()
        for chunk in ranked_chunks:
            doc_id = chunk["doc_id"]
            if doc_id not in seen_docs:
                ranked_docs.append(doc_id)
                seen_docs.add(doc_id)
        relevant = set(gt["relevant_docs"])

        for k in k_values:
            top_k = ranked_docs[:k]
            hits = len(set(top_k) & relevant)
            metrics[f"precision@{k}"].append(hits / min(k, len(relevant)))

        rr = 0.0
        for rank, doc_id in enumerate(ranked_docs, 1):
            if doc_id in relevant:
                rr = 1.0 / rank
                break
        metrics["mrr"].append(rr)

        per_query_results.append(
            {
                "query": gt["query"],
                "lang": gt["lang"],
                "top_5_docs": ranked_docs[:5],
                "top_5_chunks": [
                    {
                        "chunk_id": c["chunk_id"],
                        "doc_id": c["doc_id"],
                        "chunk_index": c["chunk_index"],
                    }
                    for c in ranked_chunks[:5]
                ],
                "relevant": list(relevant),
                "first_relevant_rank": next(
                    (r for r, d in enumerate(ranked_docs, 1) if d in relevant),
                    -1,
                ),
            }
        )

    averaged = {}
    for key, values in metrics.items():
        averaged[key] = float(np.mean(values))

    return {"averaged": averaged, "per_query": per_query_results}


def benchmark_model(
    model_name: str,
    model_config: dict,
    chunks: list[dict],
    ground_truth: list[dict],
) -> dict:
    """Run the full benchmark for a single model."""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {model_name}")
    print(f"  Model ID: {model_config['model_id']}")
    print(f"{'='*60}")

    print("  Loading model...")
    t0 = time.time()
    model = load_model(model_config)
    load_time = time.time() - t0
    print(f"  Model loaded in {load_time:.1f}s")

    chunk_texts = [chunk["text"] for chunk in chunks]

    print(f"  Embedding {len(chunk_texts)} chunks...")
    t0 = time.time()
    chunk_embeddings = embed_texts(model, chunk_texts, model_config)
    embed_time = time.time() - t0
    chunks_per_sec = len(chunk_texts) / embed_time
    print(f"  Chunks embedded in {embed_time:.2f}s ({chunks_per_sec:.1f} chunks/s)")

    queries = [gt["query"] for gt in ground_truth]
    print(f"  Embedding {len(queries)} queries...")
    t0 = time.time()
    query_embeddings = embed_queries(model, queries, model_config)
    query_time = time.time() - t0
    print(f"  Queries embedded in {query_time:.2f}s")

    print("  Computing retrieval metrics...")
    results = compute_retrieval_metrics(
        query_embeddings, chunk_embeddings, chunks, ground_truth
    )

    embedding_dim = chunk_embeddings.shape[1]

    summary = {
        "model_name": model_name,
        "model_id": model_config["model_id"],
        "embedding_dim": int(embedding_dim),
        "load_time_s": round(load_time, 1),
        "embed_time_s": round(embed_time, 2),
        "chunks_per_second": round(chunks_per_sec, 1),
        "query_time_s": round(query_time, 2),
        **results["averaged"],
        "per_query_results": results["per_query"],
    }

    print(f"\n  Results for {model_name}:")
    print(f"    Embedding dim:    {embedding_dim}")
    print(f"    Precision@3:      {results['averaged']['precision@3']:.3f}")
    print(f"    Precision@5:      {results['averaged']['precision@5']:.3f}")
    print(f"    MRR:              {results['averaged']['mrr']:.3f}")
    print(f"    Embed speed:      {chunks_per_sec:.1f} chunks/s")

    return summary


def print_comparison_table(all_results: list[dict]):
    """Print a comparison table of all models."""
    print(f"\n{'='*80}")
    print("COMPARISON TABLE")
    print(f"{'='*80}")

    header = f"{'Model':<25} {'Dim':>5} {'P@3':>6} {'P@5':>6} {'MRR':>6} {'Speed':>10} {'Load':>7}"
    print(header)
    print("-" * len(header))

    for r in all_results:
        print(
            f"{r['model_name']:<25} "
            f"{r['embedding_dim']:>5} "
            f"{r['precision@3']:>6.3f} "
            f"{r['precision@5']:>6.3f} "
            f"{r['mrr']:>6.3f} "
            f"{r['chunks_per_second']:>7.1f}c/s "
            f"{r['load_time_s']:>5.1f}s"
        )

    print(f"\n  Cross-language breakdown:")
    for r in all_results:
        en_mrr = np.mean(
            [q["first_relevant_rank"] for q in r["per_query_results"] if q["lang"] == "en"]
        )
        fr_mrr = np.mean(
            [q["first_relevant_rank"] for q in r["per_query_results"] if q["lang"] == "fr"]
        )
        print(f"    {r['model_name']:<25} EN avg first hit rank: {en_mrr:.1f}  |  FR avg first hit rank: {fr_mrr:.1f}")


def main():
    ground_truth = load_ground_truth()
    docs = load_documents()
    if not docs:
        print("ERROR: No documents found. Check EXTRACTED_TEXTS_DIR path.")
        return
    chunks = build_chunks(docs)
    if not chunks:
        print("ERROR: No chunks built from input documents.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    for model_name, model_config in CANDIDATE_MODELS.items():
        try:
            result = benchmark_model(model_name, model_config, chunks, ground_truth)
            all_results.append(result)
        except Exception as e:
            print(f"\n  ERROR benchmarking {model_name}: {e}")
            import traceback
            traceback.print_exc()

    if all_results:
        print_comparison_table(all_results)

        output_path = OUTPUT_DIR / "embedding_benchmark_results.json"
        serializable = []
        for r in all_results:
            s = {k: v for k, v in r.items()}
            serializable.append(s)
        with open(output_path, "w") as f:
            json.dump(serializable, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {output_path}")

        summary_rows = [
            {k: v for k, v in r.items() if k != "per_query_results"}
            for r in all_results
        ]
        df = pd.DataFrame(summary_rows)
        csv_path = OUTPUT_DIR / "embedding_benchmark_summary.csv"
        df.to_csv(csv_path, index=False)
        print(f"Summary CSV saved to: {csv_path}")


if __name__ == "__main__":
    main()
