from enum import Enum


class UserRole(str, Enum):
    OWNER = "OWNER"
    PURCHASE = "PURCHASE"
    GUDANG = "GUDANG"


class PurchaseStatus(str, Enum):
    DRAFT = "DRAFT"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class MovementType(str, Enum):
    PURCHASE_IN = "PURCHASE_IN"
    MANUAL_IN = "MANUAL_IN"
    OUT = "OUT"
    WASTE = "WASTE"
    ADJUSTMENT = "ADJUSTMENT"


class AlertType(str, Enum):
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

