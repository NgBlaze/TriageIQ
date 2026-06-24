"""
Rule-based routing from a ticket's classification to a target team queue.

Routing is deliberately deterministic (no LLM call): given a category and
priority, the destination queue is fully predictable, auditable, and free to
compute. This keeps routing fast and testable, and means a misroute is a rule
bug we can fix — not model nondeterminism.

Rules (in order of precedence):
  1. Any CRITICAL ticket goes to ESCALATIONS regardless of category — critical
     issues (outage, security, data loss) need immediate senior attention and
     shouldn't wait in a category-specific queue.
  2. Otherwise route by category to that category's owning team.
"""
from app.models.ticket import TeamQueue, TicketCategory, TicketPriority

# Category → owning team queue (used when priority is not critical).
_CATEGORY_ROUTING: dict[TicketCategory, TeamQueue] = {
    TicketCategory.BILLING: TeamQueue.BILLING_TEAM,
    TicketCategory.PRODUCT: TeamQueue.PRODUCT_TEAM,
    TicketCategory.ACCOUNT: TeamQueue.ACCOUNT_SUPPORT,
    TicketCategory.BUG_REPORT: TeamQueue.ENGINEERING,
    TicketCategory.OTHER: TeamQueue.GENERAL_SUPPORT,
}


def route_ticket(category: TicketCategory, priority: TicketPriority) -> TeamQueue:
    """Return the team queue a ticket should be routed to.

    Coerces string inputs to the enum so callers holding either enum members
    or their raw string values (e.g. from persisted records) route the same.
    """
    category = TicketCategory(category)
    priority = TicketPriority(priority)

    if priority == TicketPriority.CRITICAL:
        return TeamQueue.ESCALATIONS

    return _CATEGORY_ROUTING[category]
