from enum import Enum


class KairaMode(str, Enum):
    PUBLIC = "public"
    DEMO = "demo"
    OPERATOR = "operator"
    MAGISTER = "magister"
    CRITICAL = "critical"
