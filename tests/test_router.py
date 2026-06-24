"""
Unit tests for the rule-based routing service.
"""
import pytest

from app.models.ticket import TeamQueue, TicketCategory, TicketPriority
from app.services.router import route_ticket


@pytest.mark.parametrize(
    "category,expected",
    [
        (TicketCategory.BILLING, TeamQueue.BILLING_TEAM),
        (TicketCategory.PRODUCT, TeamQueue.PRODUCT_TEAM),
        (TicketCategory.ACCOUNT, TeamQueue.ACCOUNT_SUPPORT),
        (TicketCategory.BUG_REPORT, TeamQueue.ENGINEERING),
        (TicketCategory.OTHER, TeamQueue.GENERAL_SUPPORT),
    ],
)
def test_non_critical_routes_by_category(category, expected):
    assert route_ticket(category, TicketPriority.MEDIUM) == expected


@pytest.mark.parametrize("category", list(TicketCategory))
def test_critical_always_escalates(category):
    assert route_ticket(category, TicketPriority.CRITICAL) == TeamQueue.ESCALATIONS


def test_accepts_raw_string_values():
    # Persisted records hold string values, not enum members.
    assert route_ticket("billing", "low") == TeamQueue.BILLING_TEAM
    assert route_ticket("bug_report", "critical") == TeamQueue.ESCALATIONS


def test_every_category_has_a_route():
    for category in TicketCategory:
        # Should not raise KeyError for any category.
        route_ticket(category, TicketPriority.LOW)
