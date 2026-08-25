"""
Data models for Lung-RADS (Lung CT Screening Reporting and Data System).
Standard: ACR Lung-RADS v2022
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class NoduleType(str, Enum):
    SOLID = "solid"
    PART_SOLID = "part-solid"
    GROUND_GLASS = "ground-glass"


class LungRADSCategory(str, Enum):
    CATEGORY_1 = "1"
    CATEGORY_2 = "2"
    CATEGORY_3 = "3"
    CATEGORY_4A = "4A"
    CATEGORY_4B = "4B"
    CATEGORY_4X = "4X"
    CATEGORY_S = "S"


@dataclass
class Nodule:
    """Represents a pulmonary nodule observed on LDCT."""
    nodule_id: str
    nodule_type: NoduleType
    diameter_mm: float
    location: str = ""
    is_new: bool = False
    prior_diameter_mm: Optional[float] = None
    has_suspicious_features: bool = False

    def growth_mm(self) -> Optional[float]:
        """Calculate growth in mm from prior scan. None if no prior."""
        if self.prior_diameter_mm is None:
            return None
        return self.diameter_mm - self.prior_diameter_mm

    def has_significant_growth(self, threshold_mm: float = 2.0) -> bool:
        """Growth >= 2mm is considered significant per Lung-RADS."""
        growth = self.growth_mm()
        if growth is None:
            return False
        return growth >= threshold_mm


@dataclass
class LungRADSResult:
    """Result of a Lung-RADS assessment."""
    category: LungRADSCategory
    category_label: str
    description: str
    management: str
    nodule_summaries: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "category_label": self.category_label,
            "description": self.description,
            "management": self.management,
            "nodule_summaries": self.nodule_summaries,
            "notes": self.notes,
        }
