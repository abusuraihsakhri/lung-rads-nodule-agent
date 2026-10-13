"""Guideline, security, CLI and API regression tests."""
import math
import pytest

from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import main as category_cli
from lung_rads_nodule_agent.engine import assess_screening, categorize_nodule
from lung_rads_nodule_agent.models import Nodule, NoduleType, LungRADSCategory


@pytest.mark.parametrize("measurement", [float("nan"), float("inf"), -float("inf")])
def test_invalid_nonfinite_measurements(measurement):
    with pytest.raises(ValueError, match="finite"):
        Nodule("bad", NoduleType.SOLID, measurement)


def test_solid_component_cannot_exceed_total():
    with pytest.raises(ValueError, match="solid_component_mm"):
        Nodule("p", NoduleType.PART_SOLID, 8, solid_component_mm=9)


def test_prior_solid_component_cannot_exceed_prior_total():
    with pytest.raises(ValueError, match="prior_solid_component_mm"):
        Nodule("p", NoduleType.PART_SOLID, 9, prior_diameter_mm=7,
               solid_component_mm=4, prior_solid_component_mm=8)


def test_new_nodule_conflicts_with_prior():
    with pytest.raises(ValueError, match="new nodule"):
        Nodule("n", NoduleType.SOLID, 7, is_new=True, prior_diameter_mm=5)


def test_growth_requires_interval_of_twelve_months_or_less():
    n = Nodule("n", NoduleType.SOLID, 5, prior_diameter_mm=3,
               prior_interval_months=18)
    assert n.has_significant_growth() is False
    assert categorize_nodule(n) == LungRADSCategory.CATEGORY_2


def test_category_4x_from_nodule_specific_features():
    n = Nodule("n", NoduleType.SOLID, 7, has_suspicious_features=True)
    assert assess_screening([n]).category == LungRADSCategory.CATEGORY_4X


def test_s_modifier_on_empty_screening():
    result = assess_screening([], has_other_significant_finding=True)
    assert result.category == LungRADSCategory.CATEGORY_1
    assert result.s_modifier is True


def test_audit_chain_detects_changed_signature_or_metadata():
    trail = AuditTrail(secret_key="test-only-hmac-key")
    trail.log("auditor", "test", "EVENT", {"status": "ok"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "forged"
    assert not trail.verify_integrity()


def test_audit_chain_detects_changed_payload_hash():
    trail = AuditTrail(secret_key="test-only-hmac-key")
    trail.log("auditor", "test", "EVENT", {"status": "ok"})
    trail.logs[0]["payload_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_public_audit_view_is_copy():
    trail = AuditTrail(secret_key="test-only-hmac-key")
    trail.log("auditor", "test", "EVENT", {"status": "ok"})
    trail.get_trail()[0]["actor"] = "forged"
    assert trail.verify_integrity()


def test_sensitive_nested_attribute_is_rejected():
    payload = SystemTaskPayload(task_id="T1", target_identifier="SYNTH-01",
                                primary_metric=4, attributes={"contact": "user@example.com"})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_cli_missing_solid_component_fails_safely(capsys):
    assert category_cli(["assess", "-n", "part-solid:9"]) == 1
    assert "solid_component_mm" in capsys.readouterr().err


def test_cli_valid_solid_component(capsys):
    assert category_cli(["assess", "-n", "part-solid:9::7", "--json"]) == 0
    import json
    assert json.loads(capsys.readouterr().out)["category"] == "4A"


def test_cli_rejects_nonfinite_and_extra_fields(capsys):
    assert category_cli(["categorize", "solid", "nan"]) == 1
    assert category_cli(["assess", "-n", "solid:5:4:3:2:1"]) == 1


def test_api_rejects_sensitive_data_as_client_error():
    from fastapi.testclient import TestClient
    from agents.api import app

    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "TEST-1",
        "target_identifier": "SYNTH-01",
        "primary_metric": 10,
        "attributes": {"free_text": "user@example.com"},
    })
    assert response.status_code == 422


def test_api_health_and_valid_audit():
    from fastapi.testclient import TestClient
    from agents.api import app

    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.post("/api/audit", json={
        "task_id": "TEST-2", "target_identifier": "SYNTH-02",
        "primary_metric": 10,
    })
    assert response.status_code == 200
    assert response.json()["total_alerts"] == 0


def test_csv_boolean_false_is_false_and_true_is_true():
    from lung_rads_nodule_agent.cli import _parse_csv_bool
    assert _parse_csv_bool("False") is False
    assert _parse_csv_bool("0") is False
    assert _parse_csv_bool("True") is True
    assert _parse_csv_bool("yes") is True
    with pytest.raises(ValueError, match="Invalid boolean"):
        _parse_csv_bool("perhaps")


def test_batch_false_stat_does_not_raise_stat_alert(tmp_path):
    import csv
    from lung_rads_nodule_agent.cli import main as audit_cli
    source = tmp_path / "batch.csv"
    dest = tmp_path / "out.csv"
    with source.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["case_id", "metric_primary", "metric_secondary", "is_stat", "status_flag"])
        writer.writeheader()
        writer.writerow({"case_id": "SYNTH-01", "metric_primary": 5, "metric_secondary": 1,
                         "is_stat": "False", "status_flag": "NORMAL"})
    assert audit_cli(["batch", "-i", str(source), "-o", str(dest)]) == 0
    with dest.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["stat_critical_alerts"] == "0"
