# Lung-RADS Nodule Agent

> **ACR Lung-RADS v2022** lung cancer screening categorization tool.

## Overview

Implements the ACR Lung-RADS v2022 (Lung CT Screening Reporting and Data System) for categorizing pulmonary nodules found on low-dose CT (LDCT) screening. Assigns categories 1, 2, 3, 4A, 4B, 4X, or S based on nodule type, size, growth, and suspicious features, and provides management recommendations.

## Lung-RADS Categories

| Category | Label | Description | Management |
|----------|-------|-------------|------------|
| **1** | Negative | No pulmonary nodules | Annual LDCT |
| **2** | Benign | Solid <6mm, new <4mm, part-solid <6mm total | Annual LDCT |
| **3** | Probably benign | Solid 6-8mm, new 4-6mm, part-solid ≥6mm with solid <6mm | 6-month LDCT |
| **4A** | Suspicious | Solid 8-15mm, new 6-8mm, part-solid with solid 6-8mm | 3-month LDCT |
| **4B** | Very suspicious | Solid ≥15mm, new >8mm, part-solid with solid ≥8mm | Chest CT ± biopsy |
| **4X** | 4A/4B + features | Category 4A or 4B with additional suspicious features | Chest CT ± biopsy |
| **S** | Other finding | Clinically significant non-nodule finding | As appropriate |

## Nodule Types

- **Solid**: Homogeneous soft-tissue attenuation
- **Part-solid (subsolid)**: Mixed ground-glass and solid components
- **Ground-glass**: Hazy increased attenuation without obscuring bronchial/vascular margins

## Growth Definition

- **Significant growth**: ≥2mm increase in diameter from prior scan

## Installation

```bash
pip install -e .
```

## CLI Usage

```bash
# Assess multiple nodules
python cli.py assess -n solid:7 -n part-solid:10:8

# Assess with new nodules and suspicious features
python cli.py assess -n solid:12 --new --suspicious-features

# Categorize a single nodule
python cli.py categorize solid 7
python cli.py categorize part-solid 10 --prior 8

# Show all category info
python cli.py info

# Show specific category info
python cli.py info 4A

# JSON output
python cli.py assess -n solid:7 --json
```

## Python API

```python
from lung_rads_nodule_agent import Nodule, NoduleType, assess_screening

nodules = [
    Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=7),
    Nodule(nodule_id="n2", nodule_type=NoduleType.PART_SOLID, diameter_mm=10, prior_diameter_mm=8),
]

result = assess_screening(nodules)
print(f"Category: {result.category.value} - {result.category_label}")
print(f"Management: {result.management}")
```

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT License. See [LICENSE](LICENSE).
