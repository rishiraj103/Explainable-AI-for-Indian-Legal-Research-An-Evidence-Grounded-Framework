"""Temporal eligibility rules for historical legal-research evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
import re
from typing import Any


class TemporalStatus(StrEnum):
    ELIGIBLE = "eligible"
    AMBIGUOUS_EXCLUDED = "ambiguous_excluded"
    INELIGIBLE = "ineligible"
    EXCLUDED_MISSING_METADATA = "excluded_missing_metadata"


@dataclass(frozen=True)
class TemporalDecision:
    status: TemporalStatus
    query_year: int | None
    precedent_year: int | None
    reason: str


def _parse_year(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 9999 else None
    if isinstance(value, (date, datetime)):
        return value.year
    if isinstance(value, str):
        stripped = value.strip()
        if len(stripped) >= 4 and stripped[:4].isdigit():
            return int(stripped[:4])
        day_month_year = re.fullmatch(r"\d{1,2}[-/]\d{1,2}[-/](\d{4})", stripped)
        if day_month_year:
            return int(day_month_year.group(1))
    return None


def assess_temporal_eligibility(
    ildc_query_year: int | str | None,
    precedent_decision_date: date | datetime | str | None,
) -> TemporalDecision:
    """Evaluate an eCourts precedent against an ILDC case with only year metadata.

    ILDC's case date is available only at year granularity. To avoid temporal
    leakage, a precedent is eligible only when its decision year is strictly
    earlier. Same-year records are explicitly retained as ambiguous but excluded
    by default. Missing or unparseable temporal metadata is excluded.
    """

    query_year = _parse_year(ildc_query_year)
    precedent_year = _parse_year(precedent_decision_date)

    if query_year is None or precedent_year is None:
        return TemporalDecision(
            status=TemporalStatus.EXCLUDED_MISSING_METADATA,
            query_year=query_year,
            precedent_year=precedent_year,
            reason="ILDC query year or precedent decision date is missing or unparseable.",
        )
    if precedent_year < query_year:
        return TemporalDecision(
            status=TemporalStatus.ELIGIBLE,
            query_year=query_year,
            precedent_year=precedent_year,
            reason="Precedent year is strictly earlier than the ILDC query year.",
        )
    if precedent_year == query_year:
        return TemporalDecision(
            status=TemporalStatus.AMBIGUOUS_EXCLUDED,
            query_year=query_year,
            precedent_year=precedent_year,
            reason="Same-year ordering is unknown because ILDC provides no exact decision date.",
        )
    return TemporalDecision(
        status=TemporalStatus.INELIGIBLE,
        query_year=query_year,
        precedent_year=precedent_year,
        reason="Precedent year is later than the ILDC query year.",
    )
