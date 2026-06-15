"""Golden eval cases for the Research Radar pipeline. Each case is a draft plus
the behavior we expect from scan(), grounded in the real studies under /data.
Pure data — no logic — so the pytest suite can parametrize over it."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Case:
    id: str
    draft: str
    expect_studies: tuple[str, ...] = ()   # at least one must surface, relevance >= threshold
    forbid_studies: tuple[str, ...] = ()   # none of these may surface (precision)
    expect_stale: bool | None = None       # None = don't assert
    expect_stance: str | None = None
    expect_gap: bool | None = None         # None = don't assert (e.g. a gap is acceptable but not required)
    expect_too_short: bool = False
    judge: str | None = None               # qualitative dimension: faithfulness | quote_support | gap_quality
    tags: tuple[str, ...] = field(default_factory=tuple)


CASES: list[Case] = [
    Case(
        id="terminology_mismatch",
        draft=(
            "We're seeing too many shoppers bail out at the cart. I want to redesign "
            "the cart-abandonment flow to reduce checkout drop-off and recover lost orders."
        ),
        expect_studies=("s02", "s12"),   # 'payment friction' / 'checkout confidence' — different words, same problem
        judge="faithfulness",
        tags=("retrieval", "rerank"),
    ),
    Case(
        id="staleness_contradiction",
        draft=(
            "Dormant users have gone quiet, so my plan is to win them back by sending "
            "more reminder emails and increasing notification frequency until they re-engage."
        ),
        expect_studies=("s03",),         # Notification Volume (2024) — stale AND contradicts the assumption
        expect_stale=True,
        expect_stance="contradicts",
        judge="quote_support",
        tags=("staleness", "contradiction"),
    ),
    Case(
        id="honest_gap",
        draft=(
            "We want to add multi-language localization so the product is fully usable "
            "in Spanish, German, and Japanese, including translated UI and date formats."
        ),
        expect_gap=True,
        judge="gap_quality",
        tags=("gap",),
    ),
    Case(
        id="precision_distractor",
        draft=(
            "I want to build a mobile offline mode so users can keep working without a "
            "connection and sync their changes once they're back online."
        ),
        forbid_studies=("s06",),         # mobile *performance* shares the platform but is a different problem
        tags=("precision",),
    ),
    Case(
        id="too_short_guard",
        draft="checkout",
        expect_too_short=True,
        expect_gap=True,
        tags=("guard",),
    ),
]
