import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routers.chat import extract_equipment_id, format_asset_display_name, format_enterprise_response


class GraphRAGTests(unittest.TestCase):
    def test_extract_equipment_id_supports_hyphenated_tags(self):
        self.assertEqual(extract_equipment_id("Please review Pump P-101 for anomalies"), "P101")

    def test_extract_equipment_id_supports_plain_tags(self):
        self.assertEqual(extract_equipment_id("What is wrong with P101?"), "P101")

    def test_format_asset_display_name_avoids_duplicate_tag(self):
        class DummyAsset:
            def __init__(self, name):
                self.name = name

        asset = DummyAsset("Pump P101")
        self.assertEqual(format_asset_display_name(asset, "P101"), "Pump P101")

    def test_format_enterprise_response_uses_concise_rca_sections(self):
        enterprise = {
            "intent_routing": {"intent": "root_cause_analysis", "label": "Root Cause Analysis", "agent": "RCA Agent", "retrieval_priority": []},
            "primary_answer": "Pump P101 shows repeated overheating during startup.",
            "executive_summary": "Pump P101 shows repeated overheating during startup.",
            "asset_information": {"asset_name": "Pump P101", "asset_type": "Pump", "department": "Utilities", "current_health": "72%", "operational_status": "Warning"},
            "root_cause_analysis": {
                "most_probable_root_cause": "Bearing lubrication loss.",
                "confidence_score": 88,
                "supporting_evidence": ["Repeated high vibration", "Thermal rise on startup"],
            },
            "historical_incidents": {"timeline": [{"date": "2024-01-01", "title": "Trip", "severity": "High", "root_cause": "Lubrication loss"}], "frequency": "2 events", "trend": "Recurring"},
            "maintenance_history": {"recent_maintenance": "Re-greased bearings", "pending_maintenance": "PM due", "technician": "D. Kim"},
            "inspection_findings": {"latest_inspection": "Inspection 01", "observations": "Hot bearing", "risk_level": "High"},
            "manual_recommendation": {"relevant_maintenance_procedure": "Follow lubrication SOP", "document": "Manual", "page_number": 3, "section": "Bearing maintenance"},
            "expert_recommendation": {"best_practices": ["Inspect lubrication system"]},
            "predictive_risk": {"failure_probability": "78%", "risk_level": "High", "estimated_remaining_useful_life": "30 days", "recommended_next_inspection": "2026-06-30"},
            "recommended_actions": {"immediate_actions": ["Inspect bearings"], "preventive_actions": ["Add vibration monitoring"], "long_term_improvements": ["Upgrade lubrication controls"]},
            "evidence": [{"document_name": "maintenance_logs.csv", "page_number": 1, "section": "Incident", "incident_id": "INC-1", "maintenance_id": "ML-1001", "inspection_id": "", "confidence": 90, "excerpt": "Repeated overheating"}],
            "response_template": "root_cause",
            "response_sections": ["Executive Summary", "Root Cause", "Business Impact", "Corrective Action", "Preventive Action", "Evidence"],
        }
        response = format_enterprise_response(enterprise)
        self.assertIn("Executive Summary", response)
        self.assertIn("Root Cause", response)
        self.assertIn("Business Impact", response)
        self.assertIn("Corrective Action", response)
        self.assertIn("Preventive Action", response)
        self.assertIn("Evidence", response)
        self.assertIn("Source Citations", response)
        self.assertIn("maintenance_logs.csv", response)
        self.assertNotIn("Startup Procedure", response)
        self.assertNotIn("Shutdown Procedure", response)
        self.assertNotIn("SOP Details", response)

    def test_format_enterprise_response_manual_lookup(self):
        enterprise = {
            "intent_routing": {"intent": "manual_lookup", "label": "Manual Lookup", "agent": "Manual Lookup Agent", "retrieval_priority": []},
            "primary_answer": "Found manual reference for Pump P101: Bearing maintenance.",
            "executive_summary": "Found manual reference for Pump P101: Bearing maintenance.",
            "manual_lookup_response": {
                "summary": "This manual section covers bearing maintenance procedures.",
                "key_instructions": ["Inspect bearing housing", "Check lubrication levels"],
                "document": "BearingManual.pdf",
                "page_number": 12,
                "section": "Bearing Maintenance",
                "confidence": 85,
            },
            "evidence": [{"document_name": "BearingManual.pdf", "page_number": 12, "section": "Bearing Maintenance", "confidence": 85, "excerpt": "Lubrication and inspection procedure."}],
        }
        response = format_enterprise_response(enterprise)
        self.assertIn("Manual Lookup", response)
        self.assertIn("This manual section covers bearing maintenance procedures.", response)
        self.assertIn("Inspect bearing housing", response)
        self.assertIn("BearingManual.pdf", response)


if __name__ == "__main__":
    unittest.main()
