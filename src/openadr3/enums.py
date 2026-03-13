"""OpenADR 3 enumerations."""

from enum import Enum


class ObjectType(str, Enum):
    """OpenADR 3 object types."""

    PROGRAM = "PROGRAM"
    EVENT = "EVENT"
    VEN = "VEN"
    RESOURCE = "RESOURCE"
    REPORT = "REPORT"
    SUBSCRIPTION = "SUBSCRIPTION"


class Operation(str, Enum):
    """OpenADR 3 CRUD operations."""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class PayloadType(str, Enum):
    """Common OpenADR 3 payload types. Extensible via string values."""

    PRICE = "PRICE"
    USAGE = "USAGE"
    DEMAND = "DEMAND"
    SETPOINT = "SETPOINT"
    EXPORT_PRICE = "EXPORT_PRICE"
    GHG = "GHG"
    SIMPLE = "SIMPLE"
    LOAD_DISPATCH = "LOAD_DISPATCH"
    LOAD_CONTROL = "LOAD_CONTROL"
