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
  - Category S: Other clinically significant finding
"""
from typing import List, Optional, Dict, Any
from .models import Nodule, NoduleType, LungRADSCategory, LungRADSResult


# Category metadata
CATEGORY_INFO: Dict[LungRADSCategory, Dict[str, str]] = {
    LungRADSCategory.CATEGORY_1: {
        "label": "Negative",
        "description": "No pulmonary nodules. No further action needed.",
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
        "description": "Clinically significant findings unrelated to nodules (e.g., aortic aneurysm, consolidation).",
        "management": "Follow-up as appropriate for the specific finding.",
    },
}


def categorize_solid_nodule(nodule: Nodule) -> LungRADSCategory:
    """
    Categorize a solid nodule based on Lung-RADS v2022.

    For baseline screening:
      - <6mm: Category 2
      - 6 to <8mm: Category 3
      - 8 to <15mm: Category 4A
      - >=15mm: Category 4B

    For new nodules on follow-up:
      - <4mm: Category 2
      - 4 to <6mm: Category 3
      - 6 to <8mm: Category 4A
      - >=8mm: Category 4B

    Growth >=2mm upgrades to at least Category 4A.
    """
    d = nodule.diameter_mm

    if nodule.is_new:
        # New nodule thresholds (on follow-up)
        if d < 4:
            cat = LungRADSCategory.CATEGORY_2
        elif d < 6:
            cat = LungRADSCategory.CATEGORY_3
        elif d < 8:
            cat = LungRADSCategory.CATEGORY_4A
        else:
            cat = LungRADSCategory.CATEGORY_4B
    else:
        # Baseline / existing nodule thresholds
        if d < 6:
            cat = LungRADSCategory.CATEGORY_2
        elif d < 8:
            cat = LungRADSCategory.CATEGORY_3
        elif d < 15:
            cat = LungRADSCategory.CATEGORY_4A
        else:
            cat = LungRADSCategory.CATEGORY_4B

    # Growth >= 2mm upgrades
    if nodule.has_significant_growth(2.0):
        if cat in (LungRADSCategory.CATEGORY_1, LungRADSCategory.CATEGORY_2,
                    LungRADSCategory.CATEGORY_3):
            cat = LungRADSCategory.CATEGORY_4A
        # Already 4A or higher stays as-is or higher

    return cat


def categorize_part_solid_nodule(nodule: Nodule) -> LungRADSCategory:
    """
    Categorize a part-solid (subsolid) nodule based on Lung-RADS v2022.

    Part-solid nodules are assessed by total diameter and solid component size.
    Since we track total diameter and can infer solid component from growth or
    explicit data, we use total diameter with solid component thresholds.

    Baseline:
      - Total <6mm: Category 2
      - Total >=6mm with solid component <6mm: Category 3
      - Total >=6mm with solid component 6-8mm: Category 4A
      - Total >=6mm with solid component >=8mm: Category 4B

    New part-solid nodules:
      - <6mm total: Category 2
      - >=6mm total: Category 3 (unless solid component warrants higher)
    """
    d = nodule.diameter_mm  # total diameter
    # For part-solid, we use a convention: if prior_diameter is set and the nodule
    # has grown, the growth approximates the solid component increase.
    # We store solid component size in notes or use diameter as proxy.
    # For simplicity, we treat the total diameter for initial categorization
    # and use growth to determine if solid component is enlarging.

    if nodule.is_new:
        if d < 6:
            return LungRADSCategory.CATEGORY_2
        else:
            # New part-solid >= 6mm: Category 3 unless significant growth
            if nodule.has_significant_growth(2.0):
                return LungRADSCategory.CATEGORY_4A
            return LungRADSCategory.CATEGORY_3
    else:
        # Baseline part-solid
        if d < 6:
            return LungRADSCategory.CATEGORY_2

        # >= 6mm total: determine by solid component behavior
        # Significant growth suggests enlarging solid component
        if nodule.has_significant_growth(2.0):
            return LungRADSCategory.CATEGORY_4A

        # Stable part-solid >= 6mm: Category 3
        return LungRADSCategory.CATEGORY_3


def categorize_ground_glass_nodule(nodule: Nodule) -> LungRADSCategory:
    """
    Categorize a ground-glass nodule based on Lung-RADS v2022.

    Baseline:
      - <6mm: Category 2
      - 6 to <30mm without growth: Category 2 or 3
      - >=30mm: Category 3

    New ground-glass:
      - <4mm: Category 2
      - 4 to <6mm: Category 2
      - >=6mm: Category 3

    Growth >=2mm: Category 4A
    """
    d = nodule.diameter_mm

    if nodule.has_significant_growth(2.0):
        return LungRADSCategory.CATEGORY_4A

    if nodule.is_new:
        if d < 6:
            return LungRADSCategory.CATEGORY_2
        else:
            return LungRADSCategory.CATEGORY_3
    else:
        # Baseline
        if d < 6:
            return LungRADSCategory.CATEGORY_2
        elif d < 30:
            return LungRADSCategory.CATEGORY_3
        else:
            return LungRADSCategory.CATEGORY_3


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
    LungRADSCategory.CATEGORY_S: 6,
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
        }

        growth = nodule.growth_mm()
        if growth is not None:
            summary["prior_diameter_mm"] = nodule.prior_diameter_mm
            summary["growth_mm"] = round(growth, 1)
            summary["significant_growth"] = nodule.has_significant_growth()

        if nodule.is_new:
            summary["is_new"] = True

        nodule_summaries.append(summary)

    # Determine overall category (highest severity)
    overall = _max_category(nodule_categories) if nodule_categories else LungRADSCategory.CATEGORY_1

    # Upgrade to 4X if suspicious extranodal features and currently 4A or 4B
    if has_suspicious_extranodal_features and overall in (
        LungRADSCategory.CATEGORY_4A, LungRADSCategory.CATEGORY_4B
    ):
        overall = LungRADSCategory.CATEGORY_4X
        notes.append("Upgraded to 4X due to additional suspicious features (e.g., lymphadenopathy, pleural effusion).")

    # Add Category S if other significant findings exist
    if has_other_significant_finding:
        notes.append("Other clinically significant finding(s) identified (Category S).")

    info = CATEGORY_INFO[overall]
    return LungRADSResult(
        category=overall,
        category_label=info["label"],
        description=info["description"],
        management=info["management"],
        nodule_summaries=nodule_summaries,
        notes=notes,
    )
