"""Backward-compatible re-exports for KAIRA identity layer."""

from kaira.identity.kernel import (
    NULLXES_BRAND_CANONICAL_EN,
    NULLXES_BRAND_CANONICAL_RU,
    NULLXES_STT_NORMALIZE_FROM,
)
from kaira.identity.openings import KAIRA_OPENING
from kaira.identity.positioning import (
    NULLXES_POSITIONING_ENTERPRISE_INTRO,
    NULLXES_POSITIONING_HOMEPAGE,
    NULLXES_POSITIONING_ULTRA_SHORT,
)
from kaira.identity.router import (
    KAIRA_INSTRUCTIONS,
    build_instructions,
    build_kaira_instructions,
)

__all__ = [
    "KAIRA_INSTRUCTIONS",
    "KAIRA_OPENING",
    "NULLXES_BRAND_CANONICAL_EN",
    "NULLXES_BRAND_CANONICAL_RU",
    "NULLXES_POSITIONING_ENTERPRISE_INTRO",
    "NULLXES_POSITIONING_HOMEPAGE",
    "NULLXES_POSITIONING_ULTRA_SHORT",
    "NULLXES_STT_NORMALIZE_FROM",
    "build_instructions",
    "build_kaira_instructions",
]
