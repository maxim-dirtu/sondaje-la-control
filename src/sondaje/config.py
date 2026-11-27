"""Tunable methodology parameters (METHODOLOGY.md, "Tunable parameters" and M-1).

One frozen object, :class:`MethodologyConfig`, holds every parameter that the
methodology marks as tunable, with the documented defaults. Analysis code takes a
config argument instead of hard-coding numbers, so that the sensitivity analysis
(T-025) can vary them.
"""

from dataclasses import dataclass, field

from sondaje.schema import SHARE_BASES

DEFAULT_SHARE_BASE_PRIORITY: tuple[str, ...] = (
    "expressed_option",
    "all_respondents",
    "likely_voters",
    "other_subset",
)
"""M-1.1 (OI-1): the share base used when a poll publishes several, first match wins."""

DEFAULT_TRUST_WEIGHTS: dict[str, float] = {
    "relative_accuracy": 0.35,
    "systematic_bias": 0.30,
    "transparency": 0.15,
    "behaviour": 0.10,
    "track_record": 0.10,
}
"""M-5.1 default component weights (M-5.1a…M-5.1e)."""


@dataclass(frozen=True)
class MethodologyConfig:
    """Every tunable parameter of METHODOLOGY.md, with its default.

    Shares and thresholds are fractions in [0, 1]; ``c1`` is in percentage points.
    """

    window_days: int = 28
    """M-1.3: accuracy window, in days between ``fieldwork_end`` and election day."""
    tau: float = 7.0
    """M-1.3: recency-weight time constant, in days."""
    small_party_threshold: float = 0.01
    """M-1.2: result share below which a contestant is merged into "others"."""
    share_base_priority: tuple[str, ...] = DEFAULT_SHARE_BASE_PRIORITY
    """M-1.1 (OI-1): order in which share bases are chosen."""
    lt_fraction: float = 0.5
    """M-1.1 (OI-2): a value published as "<x" enters the normalization as ``x * lt_fraction``."""
    campaign_days: int = 120
    """M-3.2: campaign window, in days before election day."""
    deff: float = 1.5
    """M-4.1: design effect."""
    c1: float = 2.0
    """M-3.3: early-campaign house effect threshold, in percentage points."""
    c2: float = 0.33
    """M-3.3: closing ratio for the convergence flag."""
    herding_flag: float = 0.5
    """M-3.4: variance ratio below which herding is flagged."""
    n0: int = 3
    """M-5.2: shrinkage prior strength (number of elections)."""
    trust_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_TRUST_WEIGHTS))
    """M-5.1: component weights of the trust score."""

    def __post_init__(self) -> None:
        if self.window_days < 0:
            raise ValueError("window_days must be >= 0")
        if self.campaign_days < 0:
            raise ValueError("campaign_days must be >= 0")
        if self.tau <= 0:
            raise ValueError("tau must be > 0")
        if not 0 <= self.small_party_threshold < 1:
            raise ValueError("small_party_threshold must be in [0, 1)")
        if not 0 <= self.lt_fraction <= 1:
            raise ValueError("lt_fraction must be in [0, 1]")
        unknown = [base for base in self.share_base_priority if base not in SHARE_BASES]
        if unknown:
            raise ValueError(f"unknown share base(s) in share_base_priority: {unknown}")
        if len(set(self.share_base_priority)) != len(self.share_base_priority):
            raise ValueError("share_base_priority has duplicates")
        if not self.share_base_priority:
            raise ValueError("share_base_priority is empty")
