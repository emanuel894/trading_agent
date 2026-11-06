"""Template-specific factual adapter for the retained M02 Fed documentation copy.

No transport, inference, comparison engine, source admission or trading. This
processes the 2026-retrieved bytes; it cannot prove the original 2024 edition.
Run: python -m agent.fed_statement_offline --cutoff 2026-10-19T00:00:00Z
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys


# Pins from the accepted foundation, not from caller-supplied metadata.
SOURCE_DIRECTORY = Path(__file__).resolve().parents[2] / "docs/event-evidence/sources"
MANIFEST_SHA256 = "8475f374d6192540bfd8581749487eae736a1f6365c3d326092bd18d100c2798"
SOURCE_URL = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20240918a.htm"
NUMBER = r"(?:\d+-\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
RANGE = re.compile(
    r"\bthe Committee decided to (?:lower|raise|maintain) the target range "
    r"for the federal funds rate (?:by " + NUMBER + r" percentage points? to |to |at )"
    r"(?P<lower>" + NUMBER + r") to (?P<upper>" + NUMBER + r") percent[.;]",
    re.IGNORECASE,
)
MARKERS = {
    "balance_sheet_reduction": "continue reducing its holdings",
    "inflation_elevated": "somewhat elevated",
    "maximum_employment": "maximum employment",
}


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _raw_span(raw, text, a, b):
    return {"text": text[a:b], "raw_utf8_bytes": [len(text[:a].encode("utf-8")),
                                               len(text[:b].encode("utf-8"))],
            "artifact_sha256": _digest(raw)}


def _number(value):
    try:
        whole, fraction = value.split("-", 1) if "-" in value else ("0", value)
        if "/" in fraction:
            numerator, denominator = fraction.split("/")
            if Decimal(denominator) == 0 or Decimal(numerator) >= Decimal(denominator):
                raise ValueError("Unsupported fractional percentage")
            return Decimal(whole) + Decimal(numerator) / Decimal(denominator)
        return Decimal(value)
    except (InvalidOperation, ArithmeticError) as exc:
        raise ValueError("Malformed percentage") from exc


def _parse_policy(raw):
    """Unqualified text parsing only; callers must independently verify source bytes.

    Supports the retained template's plain policy paragraphs. Unexpected markup,
    units or conflicting range references abstain rather than being sanitized.
    Navigation, media contacts, inflation goals and dissent preferences are not
    decision-rate matches. This is not a general Fed HTML/visibility parser.
    """
    text = raw.decode("utf-8")
    starts = list(re.finditer(r'<div id="article">', text))
    ends = list(re.finditer(r'<div id="lastUpdate"', text))
    if len(starts) != 1 or len(ends) != 1 or starts[0].end() >= ends[0].start():
        raise ValueError("Unsupported or missing statement article boundaries")
    start, end = starts[0].end(), ends[0].start()
    paragraphs = list(re.finditer(r"<p>(?P<body>.*?)</p>", text[start:end], re.DOTALL))
    anchors = list(re.finditer(r"the Committee decided to", text[start:end], re.I))
    candidates = [p for p in paragraphs if "the committee decided to" in p["body"].lower()]
    if (len(candidates) != 1 or not anchors or any(
            not candidates[0].start("body") <= a.start() < candidates[0].end("body")
            for a in anchors)):
        raise ValueError("Missing or conflicting policy-range paragraphs")
    paragraph = candidates[0]
    if "<" in paragraph["body"] or "&" in paragraph["body"]:
        raise ValueError("Unsupported policy markup or entities")
    matches = list(RANGE.finditer(paragraph["body"]))
    if len(matches) != 1:
        raise ValueError("Malformed, conflicting or unsupported target-rate units")
    match = matches[0]
    lower, upper = _number(match["lower"]), _number(match["upper"])
    if not Decimal(0) <= lower < upper <= Decimal(100):
        raise ValueError("Invalid target-rate range")
    def span(a, b):
        return _raw_span(raw, text, a, b)

    facts = []
    for label, value in (("lower", lower), ("upper", upper)):
        a, b = match.span(label)
        offset = start + paragraph.start("body")
        facts.append({"measure": label, "value": str(value), "unit": "percent",
                      **span(offset + a, offset + b)})
    markers = {}
    for name, term in MARKERS.items():
        markers[name] = []
        for p in paragraphs:
            if "<" in p["body"] or "&" in p["body"]:
                continue
            for m in re.finditer(r"\b" + re.escape(term) + r"\b", p["body"], re.I):
                offset = start + p.start("body")
                markers[name].append(span(offset + m.start(), offset + m.end()))
    return {"target_range": facts, "policy_markers": markers,
            "rate_change_pp": None, "statement_diff": None}


@dataclass(frozen=True, slots=True)
class RetainedStatement:
    """Immutable copy of the accepted archive and manifest, never a live file view."""
    archive: bytes
    manifest_bytes: bytes

    def __post_init__(self):
        self._verified()

    def _verified(self):
        if not isinstance(self.archive, bytes) or not isinstance(self.manifest_bytes, bytes):
            raise ValueError("Immutable source bytes required")
        if _digest(self.manifest_bytes) != MANIFEST_SHA256:
            raise ValueError("Source verification failed: trusted manifest mismatch")
        rows = [x for x in json.loads(self.manifest_bytes) if x["id"] == "M02"]
        if len(rows) != 1:
            raise ValueError("Source verification failed: ambiguous M02")
        row = rows[0]
        if (row["url"] != SOURCE_URL or row["final_url"] != SOURCE_URL
                or row["http_status"] != 200 or row["raw_path"] != "M02.raw.gz"
                or _digest(self.archive) != row["archive_sha256"]):
            raise ValueError("Source verification failed: archive or source identity mismatch")
        raw = gzip.decompress(self.archive)
        if len(raw) != row["raw_bytes"] or _digest(raw) != row["raw_sha256"]:
            raise ValueError("Source verification failed: raw payload mismatch")
        return raw, row

    @property
    def raw(self):
        return self._verified()[0]

    def snapshot(self, cutoff):
        """Catalog retrieval cutoff only, never causal/predictive availability."""
        if not isinstance(cutoff, datetime) or cutoff.utcoffset() is None:
            raise ValueError("Explicit timezone-aware catalog cutoff required")
        raw, row = self._verified()
        result = {
            "status": "ABSTAIN_NOT_RETRIEVED_BEFORE_CUTOFF", "mode": "catalog_only",
            "predictive_admission": "quarantined", "original_edition_proven": False,
            "cutoff": cutoff.astimezone(timezone.utc).isoformat(), "facts": None,
            "comparison_status": "ABSTAIN_MISSING_INDEPENDENT_PRIOR",
            "source_manifest_sha256": MANIFEST_SHA256,
            "source_manifest_entry": row, "model": None,
        }
        if datetime.fromisoformat(row["retrieved_at"]) >= cutoff:
            return result
        unknown = ("economic_effective", "scheduled_publication", "first_machine_observable", "first_receipt",
                   "source_revision", "ingestion_completed", "verification_completed")
        clocks = {name: {"state": "unknown", "native_value": None, "utc": None}
                  for name in unknown}
        clocks["retrieved"] = {"state": "known", "native_value": row["retrieved_at"],
                               "utc": row["retrieved_at"].replace("+00:00", "Z"),
                               "basis": "retained capture manifest"}
        text = raw.decode("utf-8")
        date = list(re.finditer(r'<p class="article__time">([^<]+)</p>', text))
        release = list(re.finditer(r'<p class="releaseTime">([^<]+)', text))
        if len(date) != 1 or len(release) != 1:
            raise ValueError("Unsupported official release labels")
        clocks["official_publication"] = {
            "state": "source_asserted", "native_date": date[0][1].strip(),
            "native_value": release[0][1].strip(), "precision": "minute", "utc": None,
            "basis": "document label only; no verified historical availability instant",
            "evidence": [_raw_span(raw, text, *label.span(1)) for label in (date[0], release[0])],
        }
        result.update(status="CATALOG_FACTS_ONLY", clocks=clocks, facts=_parse_policy(raw))
        return result


def load_retained(source_directory=None):
    """Read the existing local packet only; missing/mismatched files stop the load."""
    directory = SOURCE_DIRECTORY if source_directory is None else Path(source_directory)
    manifest = (directory / "captures.json").read_bytes()
    archive = (directory / "M02.raw.gz").read_bytes()
    return RetainedStatement(archive, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff", required=True, help="timezone-aware catalog cutoff")
    args = parser.parse_args()
    try:
        packet = load_retained().snapshot(datetime.fromisoformat(args.cutoff))
    except (OSError, ValueError) as exc:
        print(f"ABSTAIN_SOURCE_OR_FORMAT_VERIFICATION: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(packet, sort_keys=True, indent=2, allow_nan=False))
    return 0 if packet["status"] == "CATALOG_FACTS_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
