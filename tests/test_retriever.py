"""
Unit tests for the TF-IDF retriever over the resolved-ticket corpus.
"""
from app.services.retriever import TfidfRetriever

CORPUS = [
    {"id": 1, "subject": "Charged twice for my subscription",
     "body": "I was billed twice for this month's plan. Please refund the duplicate.",
     "category": "billing", "resolution": "Refunded the duplicate charge."},
    {"id": 2, "subject": "Can't reset my password",
     "body": "The password reset email never arrives and I'm locked out.",
     "category": "account", "resolution": "Whitelisted the sending domain; email arrived."},
    {"id": 3, "subject": "How do I export my data?",
     "body": "I need to export all my project data to CSV but can't find the option.",
     "category": "product", "resolution": "Export lives under Settings > Data > Export."},
]


def test_ranks_most_similar_first():
    r = TfidfRetriever(CORPUS)
    hits = r.query("I was charged twice and need a refund for the duplicate charge", k=3)
    assert hits[0].id == 1
    assert hits[0].score >= hits[1].score >= hits[2].score


def test_password_query_retrieves_account_ticket():
    r = TfidfRetriever(CORPUS)
    hits = r.query("password reset email not arriving, locked out", k=1)
    assert hits[0].id == 2
    assert hits[0].category == "account"


def test_respects_k():
    r = TfidfRetriever(CORPUS)
    assert len(r.query("export data csv", k=2)) == 2


def test_unrelated_query_scores_zero():
    r = TfidfRetriever(CORPUS)
    hits = r.query("zxqw foobar nonsense gibberish", k=3)
    assert hits[0].score == 0.0
