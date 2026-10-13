"""
Data models for Lung-RADS (Lung CT Screening Reporting and Data System).
Standard: ACR Lung-RADS v2022
"""
import datetime
import math
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


class UrgencyLevel(str, Enum):
    """Urgency levels for clinical alerts."""
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    STAT_CRITICAL = "STAT_CRITICAL"


class ClinicalIntegrityStatus(str, Enum):
    """Overall clinical integrity status."""
    CONCORDANT_NORMAL = "CONCORDANT_NORMAL"
    DISCORDANCE_DETECTED = "DISCORDANCE_DETECTED"
    CRITICAL_ACTION_REQUIRED = "CRITICAL_ACTION_REQUIRED"


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
    solid_component_mm: Optional[float] = None
    prior_solid_component_mm: Optional[float] = None
    prior_interval_months: float = 12.0  # Assumed when a prior measurement is supplied.

    def __post_init__(self):
        """Validate measured dimensions and prevent unverifiable classification."""
        if not isinstance(self.nodule_id, str) or not self.nodule_id.strip():
            raise ValueError("nodule_id must be a non-empty string")
        if not isinstance(self.nodule_type, NoduleType):
            raise ValueError("nodule_type must be a NoduleType")
        for name in ("diameter_mm", "prior_diameter_mm", "solid_component_mm",
                     "prior_solid_component_mm", "prior_interval_months"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                      or not math.isfinite(value)):
                raise ValueError(f"{name} must be a finite number")
        if self.diameter_mm < 0:
            raise ValueError(f"diameter_mm must be non-negative, got {self.diameter_mm}")
        if self.diameter_mm > 100:
            raise ValueError(f"diameter_mm exceeds reasonable bounds (>100mm): {self.diameter_mm}")
        if self.prior_diameter_mm is not None and self.prior_diameter_mm < 0:
            raise ValueError(f"prior_diameter_mm must be non-negative, got {self.prior_diameter_mm}")
        if self.prior_interval_months <= 0:
            raise ValueError("prior_interval_months must be positive")
        if self.is_new and self.prior_diameter_mm is not None:
            raise ValueError("A new nodule cannot have a prior diameter")
        if self.solid_component_mm is not None:
            if self.nodule_type != NoduleType.PART_SOLID:
                raise ValueError("solid_component_mm is only valid for part-solid nodules")
            if not 0 <= self.solid_component_mm <= self.diameter_mm:
                raise ValueError("solid_component_mm must be between 0 and total diameter_mm")
        if self.prior_solid_component_mm is not None:
            if self.nodule_type != NoduleType.PART_SOLID or self.solid_component_mm is None:
                raise ValueError("prior_solid_component_mm requires a part-solid nodule with solid_component_mm")
            if self.prior_diameter_mm is None:
                raise ValueError("prior_solid_component_mm requires prior_diameter_mm")
            if not 0 <= self.prior_solid_component_mm <= self.prior_diameter_mm:
                raise ValueError("prior_solid_component_mm must be between 0 and prior_diameter_mm")

    def growth_mm(self) -> Optional[float]:
        """Calculate growth in mm from prior scan. None if no prior."""
        if self.prior_diameter_mm is None:
            return None
        return self.diameter_mm - self.prior_diameter_mm

    def has_significant_growth(self, threshold_mm: float = 1.5) -> bool:
        """Lung-RADS v2022: strictly >1.5 mm mean-diameter growth within 12 months."""
        growth = self.growth_mm()
        return growth is not None and self.prior_interval_months <= 12 and growth > threshold_mm


@dataclass
class LungRADSResult:
    """Result of a Lung-RADS assessment."""
    category: LungRADSCategory
    category_label: str
    description: str
    management: str
    nodule_summaries: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    s_modifier: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "category_label": self.category_label,
            "description": self.description,
            "management": self.management,
            "nodule_summaries": self.nodule_summaries,
            "notes": self.notes,
            "s_modifier": self.s_modifier,
        }


@dataclass
class ClinicalCasePayload:
    """Payload for a clinical case evaluation."""
    case_id: str = "CASE-2026-001"
    patient_synthetic_id: str = "SYNTH-PT-881"
    primary_metric: float = 24.5
    secondary_metric: float = 14.0
    status_flag: str = "DISCORDANT"
    is_stat: bool = True
    clinical_notes: str = ""
    biomarkers: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


@dataclass
class AgentAlert:
    """Alert generated by a clinical sub-agent."""
    alert_id: str
    sub_agent: str
    urgency: UrgencyLevel
    title: str
    clinical_finding: str
    actionable_recommendation: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "sub_agent": self.sub_agent,
            "urgency": self.urgency.value,
            "title": self.title,
            "clinical_finding": self.clinical_finding,
            "actionable_recommendation": self.actionable_recommendation,
            "timestamp": self.timestamp,
        }
