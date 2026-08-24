"""Deterministic, synthetic distributor qualification and QA pipeline.

This module is a portfolio reconstruction. It contains no private deployment
records, employer rules, external API calls, or outreach functionality.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit


# ``None`` is deliberately not a text placeholder here: it is a valid value for
# the controlled ``conflict_risk`` field. Python ``None`` is still handled by
# ``clean`` and becomes an empty string.
MISSING_VALUES = {"", "n/a", "na", "unknown", "unclear", "-", "null"}
GENERIC_EMAIL_LOCAL_PARTS = {
    "admin",
    "contact",
    "hello",
    "info",
    "office",
    "sales",
    "service",
    "support",
}
LEGAL_SUFFIXES = {
    "ag",
    "bv",
    "co",
    "company",
    "corp",
    "corporation",
    "gmbh",
    "inc",
    "incorporated",
    "limited",
    "llc",
    "ltd",
    "plc",
    "sa",
    "sas",
    "srl",
}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class Decision:
    decision: str
    rank: str
    reason: str


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def is_missing(value: object) -> bool:
    return clean(value).casefold() in MISSING_VALUES


def _ascii_tokens(value: object) -> list[str]:
    normalized = unicodedata.normalize("NFKD", clean(value).casefold())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.replace("&", " and ")
    return re.findall(r"[a-z0-9]+", ascii_text)


def normalize_company_name(value: object) -> str:
    tokens = _ascii_tokens(value)
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def normalize_person_name(value: object) -> str:
    return " ".join(_ascii_tokens(value))


def canonical_url(value: object) -> str:
    if is_missing(value):
        return ""
    raw = clean(value)
    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlsplit(candidate)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        return ""
    host = parsed.hostname.casefold().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", host, path, "", ""))


def root_domain(value: object) -> str:
    url = canonical_url(value)
    if not url:
        return ""
    return urlsplit(url).hostname or ""


def is_valid_url(value: object) -> bool:
    return bool(canonical_url(value))


def is_valid_email(value: object) -> bool:
    return not is_missing(value) and bool(EMAIL_PATTERN.fullmatch(clean(value)))


def normalized_phone(value: object) -> str:
    if is_missing(value):
        return ""
    digits = re.sub(r"\D", "", clean(value))
    return digits if 8 <= len(digits) <= 15 else ""


def is_person_specific_email(value: object) -> bool:
    if not is_valid_email(value):
        return False
    local_part = clean(value).split("@", 1)[0].casefold()
    return local_part not in GENERIC_EMAIL_LOCAL_PARTS


def has_person_specific_route(contact: Mapping[str, str]) -> bool:
    return any(
        (
            is_valid_url(contact.get("professional_profile", "")),
            is_person_specific_email(contact.get("work_email", "")),
            bool(normalized_phone(contact.get("professional_phone", ""))),
        )
    )


def read_csv(path: Path | str) -> list[dict[str, str]]:
    source = Path(path)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {source}")
        return [
            {clean(key): clean(value) for key, value in row.items() if key is not None}
            for row in reader
        ]


def _company_keys(row: Mapping[str, str]) -> set[str]:
    keys: set[str] = set()
    name = normalize_company_name(row.get("company_name", ""))
    domain = root_domain(row.get("website", ""))
    profile = canonical_url(row.get("company_profile", ""))
    if name:
        keys.add(f"name:{name}")
    if domain:
        keys.add(f"domain:{domain}")
    if profile:
        keys.add(f"profile:{profile}")
    return keys


def _contact_keys(row: Mapping[str, str]) -> set[str]:
    keys: set[str] = set()
    company = normalize_company_name(row.get("company_name", ""))
    person = normalize_person_name(row.get("contact_name", ""))
    profile = canonical_url(row.get("professional_profile", ""))
    email = clean(row.get("work_email", "")).casefold()
    phone = normalized_phone(row.get("professional_phone", ""))
    if company and person:
        keys.add(f"company-person:{company}|{person}")
    if profile:
        keys.add(f"profile:{profile}")
    if is_person_specific_email(email):
        keys.add(f"email:{email}")
    if phone:
        keys.add(f"phone:{phone}")
    return keys


def _completeness(row: Mapping[str, str]) -> int:
    return sum(not is_missing(value) for value in row.values())


def _deduplicate(
    rows: Sequence[dict[str, str]],
    key_fn: Callable[[Mapping[str, str]], set[str]],
    label_field: str,
    entity_type: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    parents = list(range(len(rows)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    key_owner: dict[str, int] = {}
    row_keys: list[set[str]] = []
    for index, row in enumerate(rows):
        keys = key_fn(row)
        row_keys.append(keys)
        for key in keys:
            if key in key_owner:
                union(index, key_owner[key])
            else:
                key_owner[key] = index

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(rows)):
        groups[find(index)].append(index)

    kept: list[tuple[int, dict[str, str]]] = []
    duplicates: list[dict[str, str]] = []
    for members in groups.values():
        best = max(
            members,
            key=lambda index: (
                _completeness(rows[index]),
                clean(rows[index].get("last_verified", "")),
                -index,
            ),
        )
        kept.append((best, rows[best]))
        for index in members:
            if index == best:
                continue
            shared_keys = sorted(row_keys[index] & row_keys[best])
            duplicates.append(
                {
                    "entity_type": entity_type,
                    "kept": clean(rows[best].get(label_field, "")),
                    "merged": clean(rows[index].get(label_field, "")),
                    "matched_by": "; ".join(shared_keys) or "transitive identity match",
                }
            )

    return [row for _, row in sorted(kept, key=lambda pair: pair[0])], duplicates


def deduplicate_companies(
    rows: Sequence[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return _deduplicate(rows, _company_keys, "company_name", "Company")


def deduplicate_contacts(
    rows: Sequence[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return _deduplicate(rows, _contact_keys, "contact_name", "Contact")


def classify_company(row: Mapping[str, str]) -> Decision:
    manufacturer = clean(row.get("manufactures_own_products", "")).casefold()
    conflict = clean(row.get("conflict_risk", "")).casefold()
    distribution = clean(row.get("distribution_evidence", "")).casefold()
    medical_device = clean(row.get("medical_device_evidence", "")).casefold()
    channel = clean(row.get("professional_channel_evidence", "")).casefold()

    if manufacturer == "yes":
        return Decision("Rejected", "Rank 3", "Own-brand manufacturer")
    if conflict == "confirmed":
        return Decision("Rejected", "Rank 4", "Confirmed conflict")
    if distribution == "no":
        return Decision("Rejected", "Rank 3", "No third-party distribution evidence")
    if medical_device == "no":
        return Decision("Rejected", "Rank 3", "No medical-device evidence")
    if channel == "no":
        return Decision("Rejected", "Rank 3", "No relevant professional-channel evidence")

    review_reasons: list[str] = []
    for field, label in (
        ("distribution_evidence", "distribution evidence"),
        ("medical_device_evidence", "medical-device evidence"),
        ("professional_channel_evidence", "professional-channel evidence"),
        ("manufactures_own_products", "manufacturer status"),
        ("conflict_risk", "conflict assessment"),
    ):
        if is_missing(row.get(field, "")):
            review_reasons.append(f"missing {label}")
    if conflict == "potential":
        review_reasons.append("potential conflict")
    if clean(row.get("validation_status", "")).casefold() != "verified":
        review_reasons.append("record is not fully verified")
    for field, label in (("website", "website"), ("source_url", "evidence URL")):
        if not is_valid_url(row.get(field, "")):
            review_reasons.append(f"invalid or missing {label}")

    if review_reasons:
        return Decision("Review", "Rank 2B", "; ".join(review_reasons))

    rank = "Rank 1" if clean(row.get("direct_fit", "")).casefold() == "yes" else "Rank 2A"
    return Decision("Qualified", rank, "All deterministic qualification gates passed")


def classify_contact(
    row: Mapping[str, str], qualified_company_keys: set[str]
) -> tuple[Decision, bool]:
    company_key = normalize_company_name(row.get("company_name", ""))
    if company_key not in qualified_company_keys:
        return Decision("Review", "N/A", "Company is not in the qualified distributor set"), True
    if clean(row.get("role_current", "")).casefold() != "yes":
        return Decision("Review", "N/A", "Current role is not verified"), False
    if clean(row.get("validation_status", "")).casefold() != "verified":
        return Decision("Review", "N/A", "Contact is not fully verified"), False
    if not is_valid_url(row.get("source_url", "")):
        return Decision("Review", "N/A", "Contact evidence URL is invalid or missing"), False
    if not has_person_specific_route(row):
        return Decision("Review", "N/A", "No person-specific public contact route"), False
    return Decision("Qualified", "N/A", "Current role and person-specific route verified"), False


def _spreadsheet_safe(value: object) -> object:
    if not isinstance(value, str):
        return value
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]], fieldnames: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _spreadsheet_safe(row.get(field, "")) for field in fieldnames})


def _identity_keys_are_unique(
    rows: Iterable[Mapping[str, str]], key_fn: Callable[[Mapping[str, str]], set[str]]
) -> bool:
    seen: set[str] = set()
    for row in rows:
        keys = key_fn(row)
        if seen & keys:
            return False
        seen.update(keys)
    return True


def _with_decision(row: Mapping[str, str], decision: Decision) -> dict[str, str]:
    return {
        **row,
        "decision": decision.decision,
        "rank": decision.rank,
        "decision_reason": decision.reason,
    }


def run_pipeline(
    companies_path: Path | str,
    contacts_path: Path | str,
    output_dir: Path | str,
) -> dict[str, object]:
    company_rows = read_csv(companies_path)
    contact_rows = read_csv(contacts_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    unique_companies, company_duplicates = deduplicate_companies(company_rows)
    qualified_companies: list[dict[str, str]] = []
    review_companies: list[dict[str, str]] = []
    rejected_companies: list[dict[str, str]] = []
    for row in unique_companies:
        decision = classify_company(row)
        enriched = _with_decision(row, decision)
        if decision.decision == "Qualified":
            qualified_companies.append(enriched)
        elif decision.decision == "Review":
            review_companies.append(enriched)
        else:
            rejected_companies.append(enriched)

    qualified_company_keys = {
        normalize_company_name(row["company_name"]) for row in qualified_companies
    }
    unique_contacts, contact_duplicates = deduplicate_contacts(contact_rows)
    qualified_contacts: list[dict[str, str]] = []
    review_contacts: list[dict[str, str]] = []
    orphan_contacts = 0
    for row in unique_contacts:
        decision, is_orphan = classify_contact(row, qualified_company_keys)
        enriched = _with_decision(row, decision)
        enriched["orphan_company"] = "Yes" if is_orphan else "No"
        if is_orphan:
            orphan_contacts += 1
        if decision.decision == "Qualified":
            qualified_contacts.append(enriched)
        else:
            review_contacts.append(enriched)

    approved_contact_counts: Counter[str] = Counter()
    for row in qualified_contacts:
        if clean(row.get("approval", "")).casefold() == "approved":
            approved_contact_counts[normalize_company_name(row["company_name"])] += 1

    promotion_ready: list[dict[str, object]] = []
    for row in qualified_companies:
        company_key = normalize_company_name(row["company_name"])
        contact_count = approved_contact_counts[company_key]
        if clean(row.get("approval", "")).casefold() == "approved" and contact_count >= 1:
            promotion_ready.append(
                {
                    **row,
                    "approved_contact_count": contact_count,
                    "promotion_status": "Ready for human-controlled promotion",
                }
            )

    company_output_rows = qualified_companies + review_companies + rejected_companies
    contact_output_rows = qualified_contacts + review_contacts
    checks = {
        "company_outputs_reconcile": len(company_output_rows) == len(unique_companies),
        "contact_outputs_reconcile": len(contact_output_rows) == len(unique_contacts),
        "company_identity_keys_unique_after_deduplication": _identity_keys_are_unique(
            company_output_rows, _company_keys
        ),
        "contact_identity_keys_unique_after_deduplication": _identity_keys_are_unique(
            contact_output_rows, _contact_keys
        ),
        "zero_orphan_qualified_contacts": all(
            normalize_company_name(row["company_name"]) in qualified_company_keys
            for row in qualified_contacts
        ),
        "missing_values_not_counted_as_routes": not has_person_specific_route(
            {
                "professional_profile": "N/A",
                "work_email": "N/A",
                "professional_phone": "N/A",
            }
        ),
        "promotion_requires_approved_contact": all(
            clean(row.get("approval", "")).casefold() == "approved"
            and int(row["approved_contact_count"]) >= 1
            for row in promotion_ready
        ),
    }

    rank_counts = Counter(row["rank"] for row in company_output_rows if row["rank"] != "N/A")
    summary: dict[str, object] = {
        "dataset": "Synthetic portfolio demonstration; no private deployment records",
        "companies": {
            "input_rows": len(company_rows),
            "unique_rows": len(unique_companies),
            "duplicates_removed": len(company_duplicates),
            "qualified": len(qualified_companies),
            "review": len(review_companies),
            "rejected": len(rejected_companies),
            "ranks": {
                rank: rank_counts[rank]
                for rank in ("Rank 1", "Rank 2A", "Rank 2B")
                if rank_counts[rank]
            },
        },
        "contacts": {
            "input_rows": len(contact_rows),
            "unique_rows": len(unique_contacts),
            "duplicates_removed": len(contact_duplicates),
            "qualified": len(qualified_contacts),
            "review": len(review_contacts),
            "orphan_company": orphan_contacts,
        },
        "promotion": {"ready_distributors": len(promotion_ready)},
        "checks": checks,
    }

    company_fields = list(company_rows[0]) + ["decision", "rank", "decision_reason"]
    contact_fields = list(contact_rows[0]) + [
        "decision",
        "rank",
        "decision_reason",
        "orphan_company",
    ]
    promotion_fields = company_fields + ["approved_contact_count", "promotion_status"]
    duplicate_fields = ["entity_type", "kept", "merged", "matched_by"]
    _write_csv(output / "qualified_distributors.csv", qualified_companies, company_fields)
    _write_csv(output / "review_distributors.csv", review_companies, company_fields)
    _write_csv(output / "rejected_distributors.csv", rejected_companies, company_fields)
    _write_csv(output / "qualified_contacts.csv", qualified_contacts, contact_fields)
    _write_csv(output / "review_contacts.csv", review_contacts, contact_fields)
    _write_csv(output / "promotion_ready_distributors.csv", promotion_ready, promotion_fields)
    _write_csv(
        output / "duplicate_decisions.csv",
        company_duplicates + contact_duplicates,
        duplicate_fields,
    )
    (output / "qa_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Qualify and deduplicate synthetic distributor/contact records."
    )
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--contacts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = run_pipeline(args.companies, args.contacts, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(summary["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
