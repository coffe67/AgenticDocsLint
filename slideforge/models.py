from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class Slide:
    index: int
    title: str
    bullets: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    section: Optional[str] = None
    section_confidence: Optional[float] = None

    def text_content(self) -> str:
        parts = [self.title] + self.bullets
        if self.notes:
            parts.append(self.notes)
        return "\n".join(parts)


@dataclass
class Deck:
    meta: Dict[str, Any]
    slides: List[Slide]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": self.meta,
            "slides": [asdict(s) for s in self.slides],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Deck":
        slides = [Slide(**s) for s in data.get("slides", [])]
        meta = data.get("meta", {})
        return Deck(meta=meta, slides=slides)


@dataclass
class KeywordCheckResult:
    section: str
    required_keywords: List[str]
    found: List[str]
    missing: List[str]
    coverage: float


@dataclass
class SlideEvaluation:
    slide_index: int
    section: Optional[str]
    section_confidence: Optional[float]
    keyword_result: Optional[KeywordCheckResult]


@dataclass
class ComplianceDecision:
    status: str  # PASS | NEEDS_UPDATE | FAIL
    score: float
    update_required: bool = False
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    meta: Dict[str, Any]
    per_slide: List[SlideEvaluation]
    overall: ComplianceDecision
    section_summaries: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": self.meta,
            "per_slide": [
                {
                    "slide_index": s.slide_index,
                    "section": s.section,
                    "section_confidence": s.section_confidence,
                    "keyword_result": asdict(s.keyword_result) if s.keyword_result else None,
                }
                for s in self.per_slide
            ],
            "overall": asdict(self.overall),
            "section_summaries": self.section_summaries,
        }
