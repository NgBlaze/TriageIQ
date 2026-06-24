"""
Retrieval over the resolved-ticket corpus for the RAG pipeline.

Mirrors the pluggable LLMClient design: a minimal `Retriever` interface with
two interchangeable backends selected by configuration, so the suggestion
service never depends on *how* similar tickets are found.

- TfidfRetriever  (prod default): pure-python TF-IDF cosine similarity. Zero
  extra dependencies and no persistent storage, so it runs fine on Vercel's
  ephemeral serverless filesystem and stays well under the bundle size limit.
- ChromaRetriever (local dev): a Chroma vector store with embeddings — the
  "vector database" described in the design doc, demoable locally.

Both load the corpus once per process (a process-level singleton via
get_retriever), which is the idempotent "ingestion" for this small corpus.
"""
import json
import math
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

# Tiny stopword list — enough to stop the most common words from dominating
# similarity on such a small corpus without pulling in an NLP dependency.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "to", "of", "in", "on", "for",
    "is", "are", "was", "were", "be", "been", "it", "this", "that", "i", "my",
    "me", "we", "our", "you", "your", "they", "them", "with", "at", "by", "from",
    "as", "so", "no", "not", "can", "cant", "could", "would", "do", "does", "did",
    "have", "has", "had", "get", "got", "im", "ive", "please", "any", "even",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class RetrievedTicket:
    """A resolved ticket returned from retrieval, with its similarity score."""
    id: int
    subject: str
    body: str
    category: str
    resolution: str
    score: float


def _tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


def _resolve_corpus_path(path: str) -> Path:
    """Resolve the corpus path, falling back to repo-root-relative if needed.

    On Vercel the working directory may differ from the repo root, so if the
    configured (relative) path doesn't exist as-is, try it relative to the
    project root inferred from this file's location.
    """
    p = Path(path)
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / path


def _load_corpus() -> list[dict]:
    corpus_path = _resolve_corpus_path(settings.rag_corpus_path)
    with open(corpus_path) as f:
        return json.load(f)


class Retriever(ABC):
    """Minimal interface every retrieval backend must satisfy."""

    @abstractmethod
    def query(self, text: str, k: int) -> list[RetrievedTicket]:
        """Return up to k resolved tickets most similar to `text`, score-sorted."""
        raise NotImplementedError


class TfidfRetriever(Retriever):
    """TF-IDF cosine-similarity retriever (pure python, no dependencies)."""

    def __init__(self, corpus: list[dict]):
        self._corpus = corpus
        # Documents are indexed on the problem text (subject + body), since the
        # query is a new ticket's subject + body; the resolution is the payload.
        docs_tokens = [_tokenize(f"{t['subject']} {t['body']}") for t in corpus]

        n_docs = len(corpus)
        df: dict[str, int] = {}
        for tokens in docs_tokens:
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        # Smoothed idf, always positive.
        self._idf = {term: math.log((1 + n_docs) / (1 + d)) + 1.0 for term, d in df.items()}

        self._doc_vectors = [self._vectorize(tokens) for tokens in docs_tokens]

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        tf: dict[str, float] = {}
        for term in tokens:
            tf[term] = tf.get(term, 0.0) + 1.0
        vec = {term: count * self._idf.get(term, 0.0) for term, count in tf.items()}
        norm = math.sqrt(sum(w * w for w in vec.values()))
        if norm == 0:
            return {}
        return {term: w / norm for term, w in vec.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        # Both vectors are L2-normalized, so the dot product is the cosine.
        if len(a) > len(b):
            a, b = b, a
        return sum(w * b.get(term, 0.0) for term, w in a.items())

    def query(self, text: str, k: int) -> list[RetrievedTicket]:
        q_vec = self._vectorize(_tokenize(text))
        scored = []
        for doc, doc_vec in zip(self._corpus, self._doc_vectors):
            score = self._cosine(q_vec, doc_vec)
            scored.append((score, doc))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [
            RetrievedTicket(
                id=doc["id"],
                subject=doc["subject"],
                body=doc["body"],
                category=doc["category"],
                resolution=doc["resolution"],
                score=round(score, 4),
            )
            for score, doc in scored[:k]
        ]


class ChromaRetriever(Retriever):
    """Chroma vector-store retriever (local dev / design-doc 'vector database').

    Uses an in-memory Chroma collection seeded from the corpus at construction;
    Chroma's default embedding function provides the vectors, so no extra model
    needs to be wired up for a local demo.
    """

    def __init__(self, corpus: list[dict]):
        import chromadb  # lazy: only needed when this backend is selected

        self._corpus_by_id = {str(t["id"]): t for t in corpus}
        client = chromadb.EphemeralClient()
        self._collection = client.create_collection(name="resolved_tickets")
        self._collection.add(
            ids=[str(t["id"]) for t in corpus],
            documents=[f"{t['subject']} {t['body']}" for t in corpus],
            metadatas=[{"category": t["category"]} for t in corpus],
        )

    def query(self, text: str, k: int) -> list[RetrievedTicket]:
        res = self._collection.query(query_texts=[text], n_results=k)
        ids = res["ids"][0]
        distances = res.get("distances", [[None] * len(ids)])[0]
        out = []
        for doc_id, dist in zip(ids, distances):
            t = self._corpus_by_id[doc_id]
            # Convert distance (lower = closer) to a 0..1 similarity score.
            score = 1.0 / (1.0 + dist) if dist is not None else 0.0
            out.append(
                RetrievedTicket(
                    id=t["id"],
                    subject=t["subject"],
                    body=t["body"],
                    category=t["category"],
                    resolution=t["resolution"],
                    score=round(score, 4),
                )
            )
        return out


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    """Return the configured retriever, building it once per process."""
    global _retriever
    if _retriever is not None:
        return _retriever

    corpus = _load_corpus()
    if settings.retriever == "chroma":
        _retriever = ChromaRetriever(corpus)
    elif settings.retriever == "tfidf":
        _retriever = TfidfRetriever(corpus)
    else:
        raise ValueError(f"Unsupported retriever: {settings.retriever}")
    return _retriever


def reset_retriever() -> None:
    """Clear the cached retriever (used by tests)."""
    global _retriever
    _retriever = None
