"""
Tests for input validation and error handling in lung-rads-nodule-agent.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from lung_rads_nodule_agent.models import Nodule, NoduleType, ClinicalCasePayload, UrgencyLevel, AgentAlert
from lung_rads_nodule_agent.engine import ClinicalDomainEngine, categorize_nodule


class TestNoduleValidation:
    """Test Nodel input validation."""

    def test_negative_diameter_raises_error(self):
        with pytest.raises(ValueError, match="diameter_mm must be non-negative"):
            Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=-5)

    def test_excessive_diameter_raises_error(self):
        with pytest.raises(ValueError, match="exceeds reasonable bounds"):
            Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=150)

    def test_negative_prior_diameter_raises_error(self):
        with pytest.raises(ValueError, match="prior_diameter_mm must be non-negative"):
            Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=10, prior_diameter_mm=-3)

    def test_empty_nodule_id_raises_error(self):
        with pytest.raises(ValueError, match="nodule_id must be a non-empty string"):
            Nodule(nodule_id="", nodule_type=NoduleType.SOLID, diameter_mm=5)

    def test_valid_nodule_creation(self):
        n = Nodule(nodule_id="n1", nodule_type=NoduleType.SOLID, diameter_mm=7.5, prior_diameter_mm=5.0)
        assert n.diameter_mm == 7.5
        assert n.prior_diameter_mm == 5.0
        assert n.growth_mm() == 2.5

    def test_zero_diameter_is_valid(self):
        """Edge case: 0mm diameter (no nodule) should be valid."""
        n = Nodule(nodule_id="n0", nodule_type=NoduleType.SOLID, diameter_mm=0)
        assert n.diameter_mm == 0


class TestClinicalDomainEngine:
    """Test ClinicalDomainEngine threshold evaluations."""

    def test_primary_metric_below_thresholds_returns_none(self):
        assert ClinicalDomainEngine.evaluate_primary_index(10.0) is None

    def test_primary_metric_at_warning_threshold(self):
        result = ClinicalDomainEngine.evaluate_primary_index(20.0)
        assert result is not None
        assert "warning" in result["title"].lower() or "Threshold" in result["title"]

    def test_primary_metric_at_critical_threshold(self):
        result = ClinicalDomainEngine.evaluate_primary_index(35.0)
        assert result is not None
        assert "Critical" in result["title"]

    def test_secondary_kinetics_normal_returns_none(self):
        assert ClinicalDomainEngine.evaluate_secondary_kinetics(5.0, False) is None

    def test_secondary_kinetics_stat_flag_triggers_alert(self):
        result = ClinicalDomainEngine.evaluate_secondary_kinetics(5.0, True)
        assert result is not None
        assert "STAT" in result["title"]

    def test_secondary_kinetics_high_value_triggers_alert(self):
        result = ClinicalDomainEngine.evaluate_secondary_kinetics(15.0, False)
        assert result is not None

    def test_biomarker_concordance_normal_returns_none(self):
        assert ClinicalDomainEngine.evaluate_biomarker_concordance("NORMAL", {}) is None

    def test_biomarker_concordance_discordant_flag(self):
        result = ClinicalDomainEngine.evaluate_biomarker_concordance("DISCORDANT", {})
        assert result is not None
        assert "Discordance" in result["title"]

    def test_biomarker_concordance_elevated_marker(self):
        result = ClinicalDomainEngine.evaluate_biomarker_concordance("NORMAL", {"marker_alpha": "ELEVATED"})
        assert result is not None
        assert "Elevated" in result["title"]

    def test_biomarker_concordance_suspicious_flag(self):
        result = ClinicalDomainEngine.evaluate_biomarker_concordance("SUSPICIOUS_FINDING", {})
        assert result is not None


class TestClinicalCasePayload:
    """Test ClinicalCasePayload defaults and validation."""

    def test_default_values(self):
        payload = ClinicalCasePayload()
        assert payload.case_id == "CASE-2026-001"
        assert payload.patient_synthetic_id == "SYNTH-PT-881"
        assert payload.primary_metric == 24.5
        assert payload.is_stat is True

    def test_custom_values(self):
        payload = ClinicalCasePayload(
            case_id="CUSTOM-001",
            primary_metric=10.0,
            is_stat=False
        )
        assert payload.case_id == "CUSTOM-001"
        assert payload.primary_metric == 10.0
        assert payload.is_stat is False

    def test_timestamp_auto_generated(self):
        payload = ClinicalCasePayload()
        assert payload.timestamp is not None
        assert len(payload.timestamp) > 0


class TestAgentAlert:
    """Test AgentAlert model."""

    def test_agent_alert_creation(self):
        alert = AgentAlert(
            alert_id="test-001",
            sub_agent="TestAgent",
            urgency=UrgencyLevel.WARNING,
            title="Test Alert",
            clinical_finding="Test finding",
            actionable_recommendation="Test recommendation"
        )
        assert alert.alert_id == "test-001"
        assert alert.urgency == UrgencyLevel.WARNING

    def test_agent_alert_to_dict(self):
        alert = AgentAlert(
            alert_id="test-001",
            sub_agent="TestAgent",
            urgency=UrgencyLevel.STAT_CRITICAL,
            title="Test Alert",
            clinical_finding="Test finding",
            actionable_recommendation="Test recommendation"
        )
        d = alert.to_dict()
        assert d["alert_id"] == "test-001"
        assert d["urgency"] == "STAT_CRITICAL"
        assert "timestamp" in d
