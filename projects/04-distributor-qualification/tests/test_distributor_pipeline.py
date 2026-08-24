from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from distributor_pipeline import (  # noqa: E402
    classify_company,
    deduplicate_companies,
    has_person_specific_route,
    read_csv,
    run_pipeline,
)


class DistributorPipelineTests(unittest.TestCase):
    def test_na_values_do_not_count_as_a_reachable_contact(self) -> None:
        contact = {
            "professional_profile": "N/A",
            "work_email": "N/A",
            "professional_phone": "N/A",
        }

        self.assertFalse(has_person_specific_route(contact))

    def test_generic_inbox_does_not_count_as_person_specific(self) -> None:
        contact = {
            "professional_profile": "N/A",
            "work_email": "info@northbridge.example",
            "professional_phone": "N/A",
        }

        self.assertFalse(has_person_specific_route(contact))

    def test_company_deduplication_uses_legal_name_and_root_domain(self) -> None:
        rows = [
            {
                "company_name": "Asteria Clinical Supply Ltd",
                "website": "https://asteria.example",
                "company_profile": "N/A",
                "last_verified": "2026-08-20",
            },
            {
                "company_name": "Asteria Clinical Supply",
                "website": "https://www.asteria.example/catalog",
                "company_profile": "N/A",
                "last_verified": "2026-08-21",
            },
        ]

        unique, duplicates = deduplicate_companies(rows)

        self.assertEqual(1, len(unique))
        self.assertEqual(1, len(duplicates))
        self.assertEqual("Asteria Clinical Supply", unique[0]["company_name"])

    def test_manufacturer_and_confirmed_conflict_are_rejected(self) -> None:
        base = {
            "company_name": "Synthetic Company",
            "website": "https://synthetic.example",
            "source_url": "https://synthetic.example/evidence",
            "distribution_evidence": "Yes",
            "medical_device_evidence": "Yes",
            "professional_channel_evidence": "Yes",
            "direct_fit": "No",
            "manufactures_own_products": "No",
            "conflict_risk": "None",
            "validation_status": "Verified",
        }

        manufacturer = classify_company({**base, "manufactures_own_products": "Yes"})
        conflict = classify_company({**base, "conflict_risk": "Confirmed"})

        self.assertEqual("Rejected", manufacturer.decision)
        self.assertIn("manufacturer", manufacturer.reason.casefold())
        self.assertEqual("Rejected", conflict.decision)
        self.assertIn("conflict", conflict.reason.casefold())

    def test_end_to_end_synthetic_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = run_pipeline(
                PROJECT_ROOT / "data" / "companies.synthetic.csv",
                PROJECT_ROOT / "data" / "contacts.synthetic.csv",
                Path(temp_dir),
            )

            self.assertEqual(10, summary["companies"]["input_rows"])
            self.assertEqual(9, summary["companies"]["unique_rows"])
            self.assertEqual(1, summary["companies"]["duplicates_removed"])
            self.assertEqual(3, summary["companies"]["qualified"])
            self.assertEqual(3, summary["companies"]["review"])
            self.assertEqual(3, summary["companies"]["rejected"])
            self.assertEqual({"Rank 1": 1, "Rank 2A": 2, "Rank 2B": 3}, summary["companies"]["ranks"])

            self.assertEqual(10, summary["contacts"]["input_rows"])
            self.assertEqual(9, summary["contacts"]["unique_rows"])
            self.assertEqual(1, summary["contacts"]["duplicates_removed"])
            self.assertEqual(4, summary["contacts"]["qualified"])
            self.assertEqual(5, summary["contacts"]["review"])
            self.assertEqual(3, summary["contacts"]["orphan_company"])
            self.assertEqual(2, summary["promotion"]["ready_distributors"])
            self.assertTrue(all(summary["checks"].values()))

            qa_path = Path(temp_dir) / "qa_summary.json"
            self.assertTrue(qa_path.is_file())
            self.assertEqual(summary, json.loads(qa_path.read_text(encoding="utf-8")))

            with (Path(temp_dir) / "promotion_ready_distributors.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                promotion_rows = list(csv.DictReader(handle))
            self.assertEqual(
                {"Asteria Clinical Supply", "Northbridge MedTech Distribution GmbH"},
                {row["company_name"] for row in promotion_rows},
            )

    def test_fixture_uses_only_reserved_synthetic_domains(self) -> None:
        for filename in ("companies.synthetic.csv", "contacts.synthetic.csv"):
            for row in read_csv(PROJECT_ROOT / "data" / filename):
                for value in row.values():
                    if "@" in value:
                        self.assertTrue(value.casefold().endswith(".example"))
                    if value.startswith("http"):
                        self.assertIn(".example", value.casefold())


if __name__ == "__main__":
    unittest.main()
