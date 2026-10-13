"""
Lung-RADS Engine: ACR Lung-RADS v2022 categorization for lung cancer screening.

Implements the Lung-RADS assessment categories for low-dose CT (LDCT) lung
cancer screening based on nodule type, size, growth, and suspicious features.

Reference: ACR Lung-RADS v2022
  - Category 1: Negative (no nodules or clearly benign)
  - Category 2: Benign appearance
  - Category 3: Probably benign
  - Category 4A: Suspicious
  - Category 4B: Very suspicious
  - Category 4X: 4A or 4B with additional suspicious features
  - S modifier: Other clinically significant finding
"""
from typing import List, Optional, Dict, Any
from .models import Nodule, NoduleType, LungRADSCategory, LungRADSResult


# Category metadata
CATEGORY_INFO: Dict[LungRADSCategory, Dict[str, str]] = {
    LungRADSCategory.CATEGORY_1: {
        "label": "Negative",
        "description": "No pulmonary nodules or suspicious findings under the modeled criteria.",
        "management": "Continue annual LDCT screening.",
    },
    LungRADSCategory.CATEGORY_2: {
        "label": "Benign appearance",
        "description": "Nodule(s) with very low likelihood of clinically significant malignancy.",
        "management": "Continue annual LDCT screening.",
    },
    LungRADSCategory.CATEGORY_3: {
        "label": "Probably benign",
        "description": "Nodule(s) with low likelihood of clinically significant malignancy.",
        "management": "6-month LDCT follow-up.",
    },
    LungRADSCategory.CATEGORY_4A: {
        "label": "Suspicious",
        "description": "Nodule(s) with moderately suspicious for clinically significant malignancy.",
        "management": "3-month LDCT follow-up. Consider PET/CT for nodules >= 8mm.",
    },
    LungRADSCategory.CATEGORY_4B: {
        "label": "Very suspicious",
        "description": "Nodule(s) with high suspicion for clinically significant malignancy.",
        "management": "Chest CT with or without contrast, PET/CT, and/or tissue sampling.",
    },
    LungRADSCategory.CATEGORY_4X: {
        "label": "Very suspicious with additional features",
        "description": "Category 4A or 4B with additional suspicious features (e.g., lymphadenopathy, pleural effusion).",
        "management": "Chest CT with or without contrast, PET/CT, and/or tissue sampling.",
    },
    LungRADSCategory.CATEGORY_S: {
        "label": "Other clinically significant finding",
        "description": "S is a modifier for additional clinically significant non-lung-cancer findings.",
        "management": "Apply appropriate follow-up in addition to numeric Lung-RADS management.",
    },
}


def categorize_solid_nodule(nodule: Nodule) -> LungRADSCategory:
    """Classify solid nodules using ACR Lung-RADS v2022 size and growth rules."""
    d = nodule.diameter_mm
    if nodule.is_new:
        if d < 4:
            return LungRADSCategory.CATEGORY_2
        if d < 6:
            return LungRADSCategory.CATEGORY_3
        if d < 8:
            return LungRADSCategory.CATEGORY_4A
        return LungRADSCategory.CATEGORY_4B

    # Growing solid nodules <8 mm are 4A; growing solid nodules >=8 mm
    # require 4B assessment. Growth means >1.5 mm in <=12 months.
    if nodule.has_significant_growth():
        return (LungRADSCategory.CATEGORY_4B if d >= 8
                else LungRADSCategory.CATEGORY_4A)
    if d < 6:
        return LungRADSCategory.CATEGORY_2
    if d < 8:
        return LungRADSCategory.CATEGORY_3
    if d < 15:
        return LungRADSCategory.CATEGORY_4A
    return LungRADSCategory.CATEGORY_4B

def categorize_part_solid_nodule(nodule: Nodule) -> LungRADSCategory:
    """Classify part-solid nodules by total size AND measured solid component.

    A missing solid-component measurement must not silently be assumed benign.
    """
    d = nodule.diameter_mm
    if d < 6:
        return (LungRADSCategory.CATEGORY_3 if nodule.is_new
                else LungRADSCategory.CATEGORY_2)

    solid = nodule.solid_component_mm
    if solid is None:
        raise ValueError("Part-solid nodules >=6 mm require solid_component_mm for classification")

    previous = nodule.prior_solid_component_mm
    growing_solid = (previous is not None and nodule.prior_interval_months <= 12
                     and solid - previous > 1.5)
    newly_solid = previous == 0 and solid > 0

    if solid >= 8:
        return LungRADSCategory.CATEGORY_4B
    if (growing_solid or newly_solid or nodule.is_new) and solid >= 4:
        return LungRADSCategory.CATEGORY_4B
    if solid >= 6 or ((growing_solid or newly_solid or nodule.is_new) and solid > 0):
        return LungRADSCategory.CATEGORY_4A
    return LungRADSCategory.CATEGORY_3

def categorize_ground_glass_nodule(nodule: Nodule) -> LungRADSCategory:
    """Pure ground-glass nodules <30 mm are 2, >=30 mm at first detection 3.

    Growth without a solid component does not automatically make a GGN 4A.
    """
    if nodule.diameter_mm >= 30:
        return LungRADSCategory.CATEGORY_3
    return LungRADSCategory.CATEGORY_2

def categorize_nodule(nodule: Nodule) -> LungRADSCategory:
    """Categorize a single nodule based on its type."""
    if nodule.nodule_type == NoduleType.SOLID:
        return categorize_solid_nodule(nodule)
    elif nodule.nodule_type == NoduleType.PART_SOLID:
        return categorize_part_solid_nodule(nodule)
    elif nodule.nodule_type == NoduleType.GROUND_GLASS:
        return categorize_ground_glass_nodule(nodule)
    else:
        raise ValueError(f"Unknown nodule type: {nodule.nodule_type}")


# Category severity ordering for finding the highest category
_CATEGORY_RANK: Dict[LungRADSCategory, int] = {
    LungRADSCategory.CATEGORY_1: 0,
    LungRADSCategory.CATEGORY_2: 1,
    LungRADSCategory.CATEGORY_3: 2,
    LungRADSCategory.CATEGORY_4A: 3,
    LungRADSCategory.CATEGORY_4B: 4,
    LungRADSCategory.CATEGORY_4X: 5,
    LungRADSCategory.CATEGORY_S: -1,  # Modifier, not a severity tier.
}


def _max_category(categories: List[LungRADSCategory]) -> LungRADSCategory:
    """Return the highest-severity category from a list."""
    return max(categories, key=lambda c: _CATEGORY_RANK.get(c, 0))


def assess_screening(
    nodules: List[Nodule],
    has_other_significant_finding: bool = False,
    has_suspicious_extranodal_features: bool = False,
) -> LungRADSResult:
    """
    Perform a complete Lung-RADS assessment for a screening LDCT.

    Args:
        nodules: List of Nodule objects found on the scan.
        has_other_significant_finding: True if there are other clinically
            significant findings (triggers Category S).
        has_suspicious_extranodal_features: True if there are additional
            suspicious features like lymphadenopathy or pleural effusion
            (triggers upgrade to Category 4X).

    Returns:
        LungRADSResult with the overall category and management recommendation.
    """
    notes: List[str] = []
    nodule_summaries: List[Dict[str, Any]] = []

    if not nodules and not has_other_significant_finding:
        # No nodules at all
        info = CATEGORY_INFO[LungRADSCategory.CATEGORY_1]
        return LungRADSResult(
            category=LungRADSCategory.CATEGORY_1,
            category_label=info["label"],
            description=info["description"],
            management=info["management"],
            nodule_summaries=[],
            notes=["No pulmonary nodules identified."],
        )

    # Categorize each nodule
    nodule_categories: List[LungRADSCategory] = []
    for nodule in nodules:
        cat = categorize_nodule(nodule)
        nodule_categories.append(cat)

        summary: Dict[str, Any] = {
            "nodule_id": nodule.nodule_id,
            "type": nodule.nodule_type.value,
            "diameter_mm": nodule.diameter_mm,
            "category": cat.value,
            "location": nodule.location,
            **({"solid_component_mm": nodule.solid_component_mm}
               if nodule.solid_component_mm is not None else {}),
        }

        growth = nodule.growth_mm()
        if growth is not None:
            summary["prior_diameter_mm"] = nodule.prior_diameter_mm
            summary["growth_mm"] = round(growth, 1)
            summary["significant_growth"] = nodule.has_significant_growth()

        if nodule.is_new:
            summary["is_new"] = True
        if nodule.prior_solid_component_mm is not None:
            summary["prior_solid_component_mm"] = nodule.prior_solid_component_mm

        nodule_summaries.append(summary)

    # Determine overall category (highest severity)
    overall = _max_category(nodule_categories) if nodule_categories else LungRADSCategory.CATEGORY_1

    # 4X is a distinct category for category 3 or 4 nodules with
    # additional suspicious imaging findings, not only 4A/4B.
    suspicious = has_suspicious_extranodal_features or any(
        n.has_suspicious_features for n in nodules
    )
    if suspicious and overall in (
        LungRADSCategory.CATEGORY_3, LungRADSCategory.CATEGORY_4A,
        LungRADSCategory.CATEGORY_4B
    ):
        overall = LungRADSCategory.CATEGORY_4X
        notes.append("Upgraded to 4X due to additional suspicious imaging features.")

    # S is a modifier and never replaces the numeric assessment category.
    if has_other_significant_finding:
        notes.append("S modifier: other clinically significant finding(s) identified.")

    info = CATEGORY_INFO[overall]
    return LungRADSResult(
        category=overall,
        category_label=info["label"],
        description=info["description"],
        management=info["management"],
        nodule_summaries=nodule_summaries,
        notes=notes,
        s_modifier=has_other_significant_finding,
    )


class ClinicalDomainEngine:
    """Clinical domain evaluation engine for multi-agent case auditing.

    Evaluates primary metrics, secondary kinetics, and biomarker concordance
    against ACR Lung-RADS v2022 & Fleischner Society 2017 thresholds.
    """

    # Thresholds for primary metric evaluation
    PRIMARY_WARNING_THRESHOLD = 20.0
    PRIMARY_CRITICAL_THRESHOLD = 35.0

    # Thresholds for secondary kinetics evaluation
    SECONDARY_WARNING_THRESHOLD = 12.0
    SECONDARY_CRITICAL_THRESHOLD = 18.0

    # Status flags that trigger discordance alerts
    DISCORDANT_FLAGS = {"DISCORDANT", "SUSPICIOUS", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"}

    @staticmethod
    def evaluate_primary_index(primary_metric: float) -> Optional[Dict[str, str]]:
        """Evaluate primary metric against clinical thresholds.

        Returns alert dict if threshold exceeded, None otherwise.
        """
        if primary_metric >= ClinicalDomainEngine.PRIMARY_CRITICAL_THRESHOLD:
            return {
                "title": "Primary Metric Critical Threshold Exceeded",
                "finding": f"Primary metric ({primary_metric:.1f}) exceeds critical threshold ({ClinicalDomainEngine.PRIMARY_CRITICAL_THRESHOLD:.1f}).",
                "recommendation": "Immediate clinical review and escalation required.",
            }
        elif primary_metric >= ClinicalDomainEngine.PRIMARY_WARNING_THRESHOLD:
            return {
                "title": "Primary Metric Threshold Discrepancy",
                "finding": f"Primary metric ({primary_metric:.1f}) exceeds standard clinical baseline ({ClinicalDomainEngine.PRIMARY_WARNING_THRESHOLD:.1f}).",
                "recommendation": "Perform secondary cross-check and review calibration profile.",
            }
        return None

    @staticmethod
    def evaluate_secondary_kinetics(secondary_metric: float, is_stat: bool) -> Optional[Dict[str, str]]:
        """Evaluate secondary kinetics against clinical thresholds.

        Returns alert dict if threshold exceeded, None otherwise.
        """
        if is_stat or secondary_metric >= ClinicalDomainEngine.SECONDARY_CRITICAL_THRESHOLD:
            return {
                "title": "STAT Critical Kinetics Alert",
                "finding": f"Secondary parameter index ({secondary_metric:.1f}) triggered automated supervisory escalation with STAT={is_stat}.",
                "recommendation": "Initiate mandatory closed-loop clinical notification protocol.",
            }
        elif secondary_metric >= ClinicalDomainEngine.SECONDARY_WARNING_THRESHOLD:
            return {
                "title": "Secondary Kinetics Threshold Exceeded",
                "finding": f"Secondary parameter index ({secondary_metric:.1f}) exceeds warning threshold ({ClinicalDomainEngine.SECONDARY_WARNING_THRESHOLD:.1f}).",
                "recommendation": "Increase monitoring frequency and verify with secondary assay.",
            }
        return None

    @staticmethod
    def evaluate_biomarker_concordance(status_flag: str, biomarkers: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Evaluate biomarker concordance and status flags.

        Returns alert dict if discordance detected, None otherwise.
        """
        status_upper = str(status_flag).upper()
        if any(flag in status_upper for flag in ClinicalDomainEngine.DISCORDANT_FLAGS):
            return {
                "title": "Biomarker / Feature Discordance Flag",
                "finding": f"Phenotypic discordance noted in observation status ({status_flag}).",
                "recommendation": "Reconcile correlative findings with secondary confirmatory testing.",
            }

        # Check biomarkers for elevated markers
        elevated_markers = [
            k for k, v in biomarkers.items()
            if isinstance(v, str) and v.upper() in ("ELEVATED", "HIGH", "POSITIVE", "CRITICAL")
        ]
        if elevated_markers:
            return {
                "title": "Elevated Biomarker Detection",
                "finding": f"Elevated biomarkers detected: {', '.join(elevated_markers)}.",
                "recommendation": "Correlate with clinical findings and consider repeat testing.",
            }
        return None
