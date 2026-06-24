"""
RAG resolution-suggestion service.

Retrieves the most similar resolved tickets from the corpus and asks the LLM to
draft a suggested resolution grounded *only* in those past resolutions. If
nothing sufficiently similar is found, it declines to guess and flags the ticket
for manual handling — a generic hallucinated answer is worse than none.
"""
from app.config import settings
from app.models.ticket import (
    ResolutionSuggestion,
    SuggestionSource,
    TicketCategory,
)
from app.services.llm_client import get_llm_client
from app.services.retriever import RetrievedTicket, get_retriever

SYSTEM_PROMPT = """You are a customer support assistant that drafts a suggested resolution for a new ticket.

You are given the new ticket and a few similar PAST tickets that were already resolved, each with its resolution. Write a concise, friendly suggested response the support agent can review and send.

Rules:
- Ground your suggestion ONLY in the resolutions of the past tickets provided. Do not invent product features, prices, URLs, or steps that are not supported by them.
- NEVER supply outside/general knowledge. If the past tickets do not actually address the new ticket's topic, do not answer from your own knowledge — instead reply with exactly: "No relevant past resolution was found for this ticket; it should be handled manually by an agent." and nothing else.
- If the past tickets only partially cover the new ticket, address what they cover and note what the agent should confirm.
- Keep it to a short paragraph or a few steps. Do not include a subject line or signature.
- Respond with the suggested resolution text only — no preamble, no JSON.
"""


def _build_prompt(subject: str, body: str, retrieved: list[RetrievedTicket]) -> str:
    examples = []
    for i, t in enumerate(retrieved, start=1):
        examples.append(
            f"Past ticket {i} (category: {t.category}):\n"
            f"Problem: {t.subject} — {t.body}\n"
            f"Resolution: {t.resolution}"
        )
    examples_block = "\n\n".join(examples)
    return (
        f"New ticket:\nSubject: {subject}\nBody: {body}\n\n"
        f"Similar resolved tickets:\n{examples_block}\n\n"
        f"Suggested resolution:"
    )


def suggest_resolution(subject: str, body: str) -> ResolutionSuggestion:
    """Generate a resolution suggestion for a new ticket via retrieval + LLM."""
    retriever = get_retriever()
    retrieved = retriever.query(f"{subject} {body}", k=settings.rag_top_k)

    confident = [r for r in retrieved if r.score >= settings.rag_min_score]

    if not confident:
        return ResolutionSuggestion(
            has_match=False,
            suggestion=None,
            sources=[],
            note=(
                "No sufficiently similar past ticket was found. This ticket likely "
                "needs manual handling by an agent."
            ),
        )

    llm = get_llm_client()
    suggestion_text = llm.generate(
        prompt=_build_prompt(subject, body, confident),
        system=SYSTEM_PROMPT,
    ).strip()

    sources = [
        SuggestionSource(
            id=r.id,
            subject=r.subject,
            category=TicketCategory(r.category),
            score=r.score,
        )
        for r in confident
    ]
    return ResolutionSuggestion(has_match=True, suggestion=suggestion_text, sources=sources)
