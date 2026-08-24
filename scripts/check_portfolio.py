"""Static checks for public-portfolio links, privacy, and file hygiene."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".for", ".ino", ".yml", ".yaml", ".svg", ""}
EXCLUDED_SUFFIXES = {
    ".cae",
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
    errors.extend(check_excluded_files(files))
    errors.extend(check_private_text(files))
    errors.extend(check_links(files))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Portfolio checks passed for {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

