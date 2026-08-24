"""Static checks for public-portfolio links, privacy, and file hygiene."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".md",
    ".py",
    ".java",
    ".for",
    ".ino",
    ".yml",
    ".yaml",
    ".svg",
    "",
}
EXCLUDED_SUFFIXES = {
    ".cae",
    ".class",
    ".docx",
    ".inp",
    ".jnl",
    ".mph",
    ".odb",
    ".pdf",
    ".vi",
    ".zip",
}
FORBIDDEN_TEXT = {
    "+98 991 234 3050",
    "+989912343050",
    "e:\\master",
    "c:\\users\\yasam",
    "recognised by the ceo",
    "credited by the ceo",
    "saved approximately one month",
    "modelutil.create",
    "v32-marcombe.mph",
    "v32_marcombe.java",
    "docs.google.com/spreadsheets/d/",
    "weekly-live-distributor-discovery",
    "files-mentioned-by-the-user-distributor",
}

REQUIRED_PUBLIC_FILES = {
    Path("assets/distributor-qualification/workflow.svg"),
    Path("projects/01-hydrogel-multiphysics/code/HydrogelModelDefinition.java"),
    Path("projects/01-hydrogel-multiphysics/MODEL_AUDIT.md"),
    Path("projects/04-distributor-qualification/data/companies.synthetic.csv"),
    Path("projects/04-distributor-qualification/data/contacts.synthetic.csv"),
    Path("projects/04-distributor-qualification/src/distributor_pipeline.py"),
    Path("projects/04-distributor-qualification/tests/test_distributor_pipeline.py"),
}

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_LINK = re.compile(r"(?:src|href)=['\"]([^'\"]+)['\"]", re.IGNORECASE)


def iter_files() -> list[Path]:
    return [path for path in ROOT.rglob("*") if path.is_file() and ".git" not in path.parts]


def check_excluded_files(files: list[Path]) -> list[str]:
    return [
        f"excluded artefact committed: {path.relative_to(ROOT)}"
        for path in files
        if path.suffix.lower() in EXCLUDED_SUFFIXES
    ]


def check_required_files() -> list[str]:
    return [
        f"required public artefact missing: {path}"
        for path in sorted(REQUIRED_PUBLIC_FILES)
        if not (ROOT / path).is_file()
    ]


def check_private_text(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        if path == Path(__file__) or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").casefold()
        for forbidden in FORBIDDEN_TEXT:
            if forbidden.casefold() in text:
                errors.append(
                    f"private or stale text in {path.relative_to(ROOT)}: {forbidden!r}"
                )
    return errors


def check_synthetic_distributor_data() -> list[str]:
    errors: list[str] = []
    data_dir = ROOT / "projects/04-distributor-qualification/data"
    for path in sorted(data_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for line_number, row in enumerate(csv.DictReader(handle), start=2):
                for field, raw_value in row.items():
                    value = (raw_value or "").strip().casefold()
                    if value.startswith(("http://", "https://")):
                        host = (urlsplit(value).hostname or "").rstrip(".")
                        if not host.endswith(".example"):
                            errors.append(
                                f"non-synthetic URL in {path.relative_to(ROOT)}:"
                                f"{line_number} field {field}"
                            )
                    if "@" in value and not value.rsplit("@", 1)[-1].endswith(
                        ".example"
                    ):
                        errors.append(
                            f"non-synthetic email in {path.relative_to(ROOT)}:"
                            f"{line_number} field {field}"
                        )
    return errors


def _local_target(raw_target: str) -> str | None:
    target = unquote(raw_target.strip().split()[0].strip("<>"))
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    return target.split("#", 1)[0].split("?", 1)[0]


def check_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        if path.suffix.lower() not in {".md", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        targets = MARKDOWN_LINK.findall(text) + HTML_LINK.findall(text)
        for raw_target in targets:
            target = _local_target(raw_target)
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(
                    f"link escapes repository in {path.relative_to(ROOT)}: {raw_target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"broken local link in {path.relative_to(ROOT)}: {raw_target}"
                )
    return errors


def main() -> int:
    files = iter_files()
    errors = []
    errors.extend(check_required_files())
    errors.extend(check_excluded_files(files))
    errors.extend(check_private_text(files))
    errors.extend(check_synthetic_distributor_data())
    errors.extend(check_links(files))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Portfolio checks passed for {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
