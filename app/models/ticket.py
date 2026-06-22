"""
Core data models for tickets.
"""
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TicketCategory(str, Enum):
    BILLING = "billing"
    PRODUCT = "product"
    ACCOUNT = "account"
    BUG_REPORT = "bug_report"
    OTHER = "other"


class TicketPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TeamQueue(str, Enum):
    BILLING_TEAM = "billing_team"
    PRODUCT_TEAM = "product_team"
    ACCOUNT_SUPPORT = "account_support"
    ENGINEERING = "engineering"
    GENERAL_SUPPORT = "general_support"
    ESCALATIONS = "escalations"


class TicketCreate(BaseModel):
    """Schema for an incoming, not-yet-classified ticket submission."""
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=5000)
    customer_email: Optional[str] = None


class ClassificationResult(BaseModel):
    """Output of the classification service."""
    category: TicketCategory
    priority: TicketPriority
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None  # brief model-provided rationale, useful for eval/debugging


class Ticket(BaseModel):
    """Full ticket record, including classification and routing."""
    id: Optional[int] = None
    subject: str
    body: str
    customer_email: Optional[str] = None
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    confidence: Optional[float] = None
    routed_team: Optional[TeamQueue] = None
    status: str = "new"  # new | classified | routed | resolved
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True)
