"""Canonical enums — must match docs/DECISION-REGISTER-AND-CHANGELOG.md.

Do not invent alternate values. Change only with contract migration.
"""

from enum import StrEnum


class TransactionType(StrEnum):
    BUY = "buy"
    RENT = "rent"
    SELL = "sell"
    GENERAL_ENQUIRY = "general_enquiry"
    UNKNOWN = "unknown"


class PropertyType(StrEnum):
    APARTMENT = "apartment"
    HOUSE = "house"
    DUPLEX = "duplex"
    OFFICE = "office"
    SHOP = "shop"
    LAND = "land"
    OTHER = "other"
    UNKNOWN = "unknown"


class Timeline(StrEnum):
    IMMEDIATE = "immediate"
    WITHIN_1_MONTH = "within_1_month"
    WITHIN_3_MONTHS = "within_3_months"
    RESEARCHING = "researching"
    UNKNOWN = "unknown"


class PipelineStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    VIEWING_SCHEDULED = "viewing_scheduled"
    NEGOTIATION = "negotiation"
    NURTURING = "nurturing"
    WON = "won"
    LOST = "lost"


class ProcessingStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class QualificationStatus(StrEnum):
    INCOMPLETE = "incomplete"
    QUALIFIED = "qualified"
    NEEDS_REVIEW = "needs_review"
    DISQUALIFIED = "disqualified"


class PriorityBand(StrEnum):
    HOT = "hot"
    WARM = "warm"
    STANDARD = "standard"
    UNSCORED = "unscored"


class SenderType(StrEnum):
    CUSTOMER = "customer"
    ASSISTANT = "assistant"
    SALES_AGENT = "sales_agent"
    SYSTEM = "system"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    LEASED = "leased"
    DELIVERED_TO_N8N = "delivered_to_n8n"
    RETRY_WAIT = "retry_wait"
    DEAD_LETTER = "dead_letter"


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    PROVIDER_ACCEPTED = "provider_accepted"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNKNOWN = "unknown"


class BudgetRelation(StrEnum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    RANGE = "range"
    UNKNOWN = "unknown"
