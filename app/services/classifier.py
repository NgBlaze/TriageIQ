"""
Ticket classification service.

Uses a few-shot prompt against the configured LLM to classify a ticket's
category and priority. Prompt-based classification was chosen over fine-tuning
for Sprint 1 to avoid requiring labeled training data and a training pipeline
up front — see docs/DESIGN_AND_TESTING.md for the full tradeoff discussion.
"""
import json
import re

from app.models.ticket import ClassificationResult, TicketCategory, TicketPriority
from app.services.llm_client import get_llm_client

SYSTEM_PROMPT = """You are a customer support ticket classification assistant.

Given a ticket's subject and body, classify it into exactly one category and one priority level.

Categories:
- billing: payment issues, charges, refunds, invoices, subscription/pricing questions
- product: how-to questions, feature requests, general product usage questions
- account: login issues, password resets, access/permissions problems
- bug_report: something is broken, error messages, unexpected behavior
- other: anything that doesn't clearly fit the above

Priority levels:
- critical: service completely unusable, security issue, data loss, affects many users
- high: significant functionality broken or blocked, no workaround, single user/account
- medium: issue present but workaround exists, or moderate inconvenience
- low: minor issue, cosmetic, or general question with no urgency

Respond with ONLY a JSON object in this exact format, no other text:
{"category": "<category>", "priority": "<priority>", "confidence": <0.0-1.0>, "reasoning": "<one short sentence>"}
"""

FEW_SHOT_EXAMPLES = """
Example 1:
Subject: Can't log into my account
Body: I've tried resetting my password three times but the reset email never arrives. I need access today for an important client call.
Response: {"category": "account", "priority": "high", "confidence": 0.92, "reasoning": "Login access blocked with time pressure but single-user impact."}

Example 2:
Subject: Charged twice this month
Body: I noticed two identical charges on my card for this month's subscription. Please refund the duplicate.
Response: {"category": "billing", "priority": "medium", "confidence": 0.88, "reasoning": "Billing error with clear resolution path, not urgent outage."}

Example 3:
Subject: App crashes on startup for all users
Body: Since this morning's update, the app crashes immediately on launch. Our whole team is affected and we can't work.
Response: {"category": "bug_report", "priority": "critical", "confidence": 0.95, "reasoning": "Total outage affecting multiple users, no workaround."}
"""


def _parse_llm_response(raw_response: str) -> dict:
    """Extract a JSON object from the LLM's response, tolerating minor formatting noise."""
    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find JSON in LLM response: {raw_response!r}")
    return json.loads(match.group(0))


def classify_ticket(subject: str, body: str) -> ClassificationResult:
    """
    Classify a ticket's category and priority using the configured LLM.

    Raises ValueError if the LLM response cannot be parsed or contains
    invalid category/priority values, so callers can decide how to handle
    a failed classification (e.g., flag for manual review).
    """
    llm = get_llm_client()

    prompt = f"""{FEW_SHOT_EXAMPLES}

Now classify this ticket:
Subject: {subject}
Body: {body}
Response:"""

    raw_response = llm.generate(prompt=prompt, system=SYSTEM_PROMPT)
    parsed = _parse_llm_response(raw_response)

    return ClassificationResult(
        category=TicketCategory(parsed["category"]),
        priority=TicketPriority(parsed["priority"]),
        confidence=float(parsed["confidence"]),
        reasoning=parsed.get("reasoning"),
    )
