"""
Tests for Lung-RADS v2022 categorization engine.
"""
import sys
import os
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lung_rads_nodule_agent.models import Nodule, NoduleType, LungRADSCategory, LungRADSResult
from lung_rads_nodule_agent.engine import (
    assess_screening,
    categorize_nodule,
    categorize_solid_nodule,
    categorize_part_solid_nodule,
    categorize_ground_glass_nodule,
    CATEGORY_INFO,
)
from cli import main as cli_main


# ── Solid Nodule Tests ──────────────────────────────────────────────

class TestSolidNodules:
    def test_solid_below_6mm_is_category_2(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=5)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_solid_exactly_6mm_is_category_3(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=6)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_3

    def test_solid_7mm_is_category_3(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=7)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_3

    def test_solid_exactly_8mm_is_category_4a(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=8)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4A

    def test_solid_12mm_is_category_4a(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=12)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4A

    def test_solid_exactly_15mm_is_category_4b(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=15)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4B

    def test_solid_20mm_is_category_4b(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=20)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4B

    def test_solid_new_below_4mm_is_category_2(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=3, is_new=True)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_solid_new_5mm_is_category_3(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=5, is_new=True)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_3

    def test_solid_new_7mm_is_category_4a(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=7, is_new=True)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4A

    def test_solid_new_10mm_is_category_4b(self):
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=10, is_new=True)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4B

    def test_solid_growth_upgrades_to_4a(self):
        """A 5mm nodule that grew from 2mm (growth=3mm >= 2mm threshold) -> 4A."""
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=5, prior_diameter_mm=2)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4A

    def test_solid_no_significant_growth_stays_same(self):
        """A 5mm nodule that grew from 4mm (growth=1mm < 2mm) stays Category 2."""
        n = Nodule(nodule_id="s1", nodule_type=NoduleType.SOLID, diameter_mm=5, prior_diameter_mm=4)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_2



    def test_growth_just_above_1point5(self):
        n = Nodule(nodule_id="s", nodule_type=NoduleType.SOLID,
                   diameter_mm=5.6, prior_diameter_mm=4.0)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4A

    def test_growth_exactly_1point5_is_not_significant(self):
        n = Nodule(nodule_id="s", nodule_type=NoduleType.SOLID,
                   diameter_mm=5.5, prior_diameter_mm=4.0)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_growing_solid_8mm_is_category_4b(self):
        n = Nodule(nodule_id="s", nodule_type=NoduleType.SOLID,
                   diameter_mm=8, prior_diameter_mm=6)
        assert categorize_solid_nodule(n) == LungRADSCategory.CATEGORY_4B

# ── Part-Solid Nodule Tests ─────────────────────────────────────────

class TestPartSolidNodules:
    def test_part_solid_below_6mm_is_category_2(self):
        n = Nodule(nodule_id="ps1", nodule_type=NoduleType.PART_SOLID, diameter_mm=5)
        assert categorize_part_solid_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_part_solid_8mm_stable_is_category_3(self):
        n = Nodule(nodule_id="ps1", nodule_type=NoduleType.PART_SOLID, diameter_mm=8, solid_component_mm=3)
        assert categorize_part_solid_nodule(n) == LungRADSCategory.CATEGORY_3

    def test_part_solid_with_growing_solid_component_is_category_4b(self):
        n = Nodule(nodule_id="ps1", nodule_type=NoduleType.PART_SOLID, diameter_mm=10, prior_diameter_mm=7, solid_component_mm=5, prior_solid_component_mm=2)
        assert categorize_part_solid_nodule(n) == LungRADSCategory.CATEGORY_4B

    def test_part_solid_new_below_6mm_is_category_3(self):
        n = Nodule(nodule_id="ps1", nodule_type=NoduleType.PART_SOLID, diameter_mm=4, is_new=True)
        assert categorize_part_solid_nodule(n) == LungRADSCategory.CATEGORY_3

    def test_part_solid_new_8mm_with_small_solid_component_is_category_4a(self):
        n = Nodule(nodule_id="ps1", nodule_type=NoduleType.PART_SOLID, diameter_mm=8, solid_component_mm=2, is_new=True)
        assert categorize_part_solid_nodule(n) == LungRADSCategory.CATEGORY_4A



    def test_part_solid_requires_solid_component(self):
        n = Nodule(nodule_id="p", nodule_type=NoduleType.PART_SOLID, diameter_mm=8)
        with pytest.raises(ValueError, match="solid_component_mm"):
            categorize_part_solid_nodule(n)

    @pytest.mark.parametrize("solid,category", [
        (3.0, LungRADSCategory.CATEGORY_3),
        (6.0, LungRADSCategory.CATEGORY_4A),
        (8.0, LungRADSCategory.CATEGORY_4B),
    ])
    def test_part_solid_component_boundaries(self, solid, category):
        n = Nodule(nodule_id="p", nodule_type=NoduleType.PART_SOLID,
                   diameter_mm=12, solid_component_mm=solid)
        assert categorize_part_solid_nodule(n) == category

# ── Ground-Glass Nodule Tests ───────────────────────────────────────

class TestGroundGlassNodules:
    def test_gg_below_6mm_is_category_2(self):
        n = Nodule(nodule_id="g1", nodule_type=NoduleType.GROUND_GLASS, diameter_mm=4)
        assert categorize_ground_glass_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_gg_10mm_is_category_2(self):
        n = Nodule(nodule_id="g1", nodule_type=NoduleType.GROUND_GLASS, diameter_mm=10)
        assert categorize_ground_glass_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_gg_with_growth_below_30mm_is_category_2(self):
        n = Nodule(nodule_id="g1", nodule_type=NoduleType.GROUND_GLASS, diameter_mm=12, prior_diameter_mm=9)
        assert categorize_ground_glass_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_gg_new_5mm_is_category_2(self):
        n = Nodule(nodule_id="g1", nodule_type=NoduleType.GROUND_GLASS, diameter_mm=5, is_new=True)
        assert categorize_ground_glass_nodule(n) == LungRADSCategory.CATEGORY_2

    def test_gg_new_8mm_is_category_2(self):
        n = Nodule(nodule_id="g1", nodule_type=NoduleType.GROUND_GLASS, diameter_mm=8, is_new=True)
        assert categorize_ground_glass_nodule(n) == LungRADSCategory.CATEGORY_2



    def test_gg_30mm_at_baseline_is_category_3(self):
        n = Nodule(nodule_id="g", nodule_type=NoduleType.GROUND_GLASS, diameter_mm=30)
        assert categorize_ground_glass_nodule(n) == LungRADSCategory.CATEGORY_3

# ── Full Screening Assessment Tests ─────────────────────────────────

class TestAssessScreening:
    def test_no_nodules_is_category_1(self):
        result = assess_screening([])
        assert result.category == LungRADSCategory.CATEGORY_1
        assert result.category_label == "Negative"

    def test_single_small_solid_is_category_2(self):
        nodules = [Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=4)]
        result = assess_screening(nodules)
        assert result.category == LungRADSCategory.CATEGORY_2

    def test_multiple_nodules_takes_highest_category(self):
        nodules = [
            Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=4),  # Cat 2
            Nodule(nodule_id="n2", nodule_type=NoduleType.SOLID, diameter_mm=10),  # Cat 4A
        ]
        result = assess_screening(nodules)
        assert result.category == LungRADSCategory.CATEGORY_4A

    def test_suspicious_features_upgrades_4a_to_4x(self):
        nodules = [Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=10)]
        result = assess_screening(nodules, has_suspicious_extranodal_features=True)
        assert result.category == LungRADSCategory.CATEGORY_4X

    def test_suspicious_features_upgrades_4b_to_4x(self):
        nodules = [Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=20)]
        result = assess_screening(nodules, has_suspicious_extranodal_features=True)
        assert result.category == LungRADSCategory.CATEGORY_4X

    def test_suspicious_features_upgrades_cat3_to_4x(self):
        """Suspicious features only upgrade 4A/4B to 4X, not lower categories."""
        nodules = [Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=7)]
        result = assess_screening(nodules, has_suspicious_extranodal_features=True)
        assert result.category == LungRADSCategory.CATEGORY_4X

    def test_other_finding_adds_note(self):
        result = assess_screening([], has_other_significant_finding=True)
        assert any("significant" in n.lower() for n in result.notes)


    def test_s_modifier_preserves_numeric_category(self):
        n = Nodule(nodule_id="n", nodule_type=NoduleType.SOLID, diameter_mm=7)
        result = assess_screening([n], has_other_significant_finding=True)
        assert result.category == LungRADSCategory.CATEGORY_3
        assert result.s_modifier is True
        assert result.to_dict()["s_modifier"] is True

    def test_result_has_management(self):
        nodules = [Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=7)]
        result = assess_screening(nodules)
        assert "6-month" in result.management

    def test_result_has_nodule_summaries(self):
        nodules = [
            Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=7),
            Nodule(nodule_id="n2", nodule_type=NoduleType.PART_SOLID, diameter_mm=10, prior_diameter_mm=8, solid_component_mm=4, prior_solid_component_mm=2),
        ]
        result = assess_screening(nodules)
        assert len(result.nodule_summaries) == 2
        assert result.nodule_summaries[0]["diameter_mm"] == 7
        assert result.nodule_summaries[1]["growth_mm"] == 2.0

    def test_to_dict(self):
        nodules = [Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=7)]
        result = assess_screening(nodules)
        d = result.to_dict()
        assert "category" in d
        assert "management" in d
        assert "nodule_summaries" in d


# ── Nodule Model Tests ──────────────────────────────────────────────

class TestNoduleModel:
    def test_growth_calculation(self):
        n = Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=10, prior_diameter_mm=7)
        assert n.growth_mm() == 3.0

    def test_growth_none_when_no_prior(self):
        n = Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=10)
        assert n.growth_mm() is None

    def test_significant_growth_true(self):
        n = Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=10, prior_diameter_mm=7)
        assert n.has_significant_growth() is True

    def test_significant_growth_false(self):
        n = Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=10, prior_diameter_mm=9)
        assert n.has_significant_growth() is False

    def test_significant_growth_exact_threshold(self):
        n = Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=10, prior_diameter_mm=8)
        assert n.has_significant_growth() is True  # exactly 2mm


# ── CLI Tests ───────────────────────────────────────────────────────

class TestCLI:
    def test_assess_single_nodule(self):
        ret = cli_main(["assess", "-n", "solid:7"])
        assert ret == 0

    def test_assess_multiple_nodules(self):
        ret = cli_main(["assess", "-n", "solid:4", "-n", "part-solid:10:8:4:2"])
        assert ret == 0

    def test_assess_json_output(self, capsys):
        ret = cli_main(["assess", "-n", "solid:7", "--json"])
        assert ret == 0
        import json
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "category" in data

    def test_categorize_command(self, capsys):
        ret = cli_main(["categorize", "solid", "7"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "Lung-RADS" in out

    def test_info_command(self, capsys):
        ret = cli_main(["info"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "Negative" in out

    def test_info_specific_category(self, capsys):
        ret = cli_main(["info", "4A"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "Suspicious" in out


# ── Category Info Tests ─────────────────────────────────────────────

class TestCategoryInfo:
    def test_all_categories_have_info(self):
        for cat in LungRADSCategory:
            assert cat in CATEGORY_INFO
            info = CATEGORY_INFO[cat]
            assert "label" in info
            assert "description" in info
            assert "management" in info

    def test_category_1_management(self):
        assert "annual" in CATEGORY_INFO[LungRADSCategory.CATEGORY_1]["management"].lower()

    def test_category_3_management(self):
        assert "6-month" in CATEGORY_INFO[LungRADSCategory.CATEGORY_3]["management"]

    def test_category_4a_management(self):
        assert "3-month" in CATEGORY_INFO[LungRADSCategory.CATEGORY_4A]["management"]
