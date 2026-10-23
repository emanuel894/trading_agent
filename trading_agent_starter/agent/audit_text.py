"""Untrusted-document parsing and conservative, source-grounded disclosure links."""
from __future__ import annotations

from html.parser import HTMLParser
import re
import time

from .audit_store import AuditFailure, VERSION, canonical, digest, utc_now

PARSER_VERSION = "mda-visible-text-v1"
LINK_VERSION = "paragraph-overlap-v1"
SUSPICIOUS = re.compile(
    r"ignore\s+(?:all\s+)?(?:previous|prior|system)\s+instructions|"
    r"(?:system|assistant)\s*:\s*(?:you are|ignore)|"
    r"(?:reveal|send|print)\s+(?:the\s+)?(?:api.?key|secret|password)|"
    r"<\|(?:im_start|system|assistant)\|>|(?:execute|run)\s+(?:this\s+)?(?:shell|tool)\s+command",
    re.I)


class VisibleText(HTMLParser):
    BLOCKS = {"p", "div", "tr", "table", "h1", "h2", "h3", "h4", "br", "li"}
    SKIP = {"style", "script", "head", "ix:hidden"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip, self.suspicious = [], [], False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"iframe", "object", "embed", "form", "script"}:
            self.suspicious = True
        hidden = ("hidden" in attrs or "display:none" in attrs.get("style", "").replace(" ", "").lower())
        if self.skip or tag in self.SKIP or hidden:
            if tag not in {"br", "img", "meta", "link", "input", "hr"}:
                self.skip.append(tag)
            return
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
            return
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalize(value):
    return " ".join(value.split()).casefold()


def parse_document(store, document, *, mda=False):
    started, tick = utc_now(), time.monotonic()
    raw = store.raw(document)
    if len(raw) > 15_000_000:
        raise AuditFailure("PARSER_BYTE_LIMIT")
    try:
        html = raw.decode("utf-8-sig")
    except UnicodeError:
        # No silent replacement or guessed encoding in source-span evidence.
        raise AuditFailure("UNSUPPORTED_DOCUMENT_ENCODING") from None
    if re.search(r"<!ENTITY", html, re.I):
        raise AuditFailure("EXTERNAL_ENTITY_REJECTED")
    parser = VisibleText()
    parser.feed(html)
    parser.close()
    if parser.suspicious or SUSPICIOUS.search(html):
        raise AuditFailure("SUSPICIOUS_DOCUMENT_CONTENT")
    if parser.skip:
        raise AuditFailure("UNBALANCED_HIDDEN_CONTENT")
    text = "\n".join(" ".join(line.split()) for line in "".join(parser.parts).splitlines()
                     if line.strip())
    if not text or len(text) > 2_000_000:
        raise AuditFailure("EMPTY_OR_OVERSIZE_TEXT")
    span = [0, len(text)]
    if mda:
        starts = list(re.finditer(r"(?im)^item\s+2\s*[.\-–:]?\s*management[’'s]*\s*", text))
        candidates = []
        for start in starts:
            end = re.search(r"(?im)^item\s+[34]\s*[.\-–:]?\s*(?:quantitative|controls)", text[start.end():])
            if end:
                right = start.end() + end.start()
                if right - start.start() >= 500:
                    candidates.append([start.start(), right])
        if len(candidates) != 1:
            raise AuditFailure("MDA_SECTION_MISSING_OR_AMBIGUOUS")
        span = candidates[0]
    fiscal = {}
    for name in ("DocumentFiscalPeriodFocus", "DocumentFiscalYearFocus"):
        values = re.findall(r'<ix:nonnumeric\b(?=[^>]*\bname\s*=\s*[\"\']dei:' + name
                            + r'[\"\'])[^>]*>\s*([^<]+?)\s*</ix:nonnumeric>', html, re.I)
        if len(set(values)) == 1:
            fiscal[name] = values[0].strip()
    view = store.append("text_view", document["id"], {
        "parser_version": PARSER_VERSION, "input_document": document["id"],
        "started_at": started, "finished_at": utc_now(), "elapsed_seconds": time.monotonic() - tick,
        "span_coordinate_system": "Unicode character offsets in this immutable UTF-8 text view",
        "mda_span": span if mda else None, "fiscal": fiscal, "untrusted": True,
        "model": None, "prompt": None, "schema_version": VERSION}, text.encode("utf-8"))
    paragraphs = []
    for match in re.finditer(r"[^\n]+", text[span[0]:span[1]]):
        if len(match.group().split()) < 8:
            continue
        start, end = span[0] + match.start(), span[0] + match.end()
        paragraphs.append({"id": digest(canonical([view["blob_sha"], start, end])),
                           "view_id": view["id"], "span": [start, end], "text": text[start:end]})
    if not paragraphs or len(paragraphs) > 4000:
        raise AuditFailure("PARAGRAPH_COUNT_OUT_OF_BOUNDS")
    if any(len(p["text"]) > 20000 for p in paragraphs):
        raise AuditFailure("PARAGRAPH_SIZE_OUT_OF_BOUNDS")
    return {"document": document, "view": view, "text": text, "paragraphs": paragraphs,
            "fiscal": fiscal}


def verify_comparable(current, prior):
    a, b = current["fiscal"], prior["fiscal"]
    try:
        valid = (a["DocumentFiscalPeriodFocus"] in {"Q1", "Q2", "Q3"}
                 and a["DocumentFiscalPeriodFocus"] == b["DocumentFiscalPeriodFocus"]
                 and int(a["DocumentFiscalYearFocus"]) == int(b["DocumentFiscalYearFocus"]) + 1)
    except (KeyError, ValueError):
        valid = False
    if not valid:
        raise AuditFailure("FISCAL_COMPARISON_UNVERIFIED")


def disclosure_map(current, prior, disclosures):
    """Text overlap is linkage evidence, never an assertion of semantic novelty."""
    prior_text = normalize(prior["text"])
    started = time.monotonic()
    pool = [(doc, p, normalize(p["text"])) for doc in disclosures for p in doc["paragraphs"]]
    if len(pool) > 20000:
        raise AuditFailure("DISCLOSURE_COMPARISON_CAP")
    links = []
    for paragraph in current["paragraphs"]:
        if time.monotonic() - started > 10:
            raise AuditFailure("DISCLOSURE_LINKAGE_TIME_BUDGET")
        normalized = normalize(paragraph["text"])
        entry = {k: paragraph[k] for k in ("id", "view_id", "span")}
        entry.update(relation="UNRESOLVED", prior_match=None,
                     new_relative_to_prior_10q=normalized not in prior_text,
                     new_to_public=None, materially_equivalent=None)
        if normalized in prior_text:
            entry["relation"] = "UNCHANGED_FROM_PRIOR_10Q"
            entry["prior_match"] = {"view_id": prior["view"]["id"], "method": "normalized_substring"}
        else:
            # Numeric/negation tokens must remain identical even for a review candidate.
            tokens = set(re.findall(r"[\w%.+-]+", normalized))
            numbers = re.findall(r"[-+]?\d[\d,.]*%?", normalized)
            negations = tokens & {"not", "no", "never", "without", "decreased", "increased"}
            best = None
            for doc, other, candidate in pool:
                if normalized == candidate:
                    best = (1.0, doc, other)
                    break
                other_tokens = set(re.findall(r"[\w%.+-]+", candidate))
                if (numbers != re.findall(r"[-+]?\d[\d,.]*%?", candidate)
                        or negations != other_tokens & {"not", "no", "never", "without", "decreased", "increased"}):
                    continue
                score = len(tokens & other_tokens) / max(1, len(tokens | other_tokens))
                if score >= 0.85 and (best is None or score > best[0]):
                    best = score, doc, other
            if best:
                score, doc, other = best
                entry["relation"] = "EXACT_PRIOR_TEXT" if score == 1 and normalized == normalize(other["text"]) else "POSSIBLE_EQUIVALENT_REVIEW"
                entry["prior_match"] = {"document_id": doc["document"]["id"],
                                        "view_id": other["view_id"], "span": other["span"],
                                        "accepted_at": doc["document"]["metadata"].get("accepted_at"),
                                        "method": "token_jaccard", "score": score}
                # Even exact wording can refer to a different period or entity.
        links.append(entry)
    return {"version": LINK_VERSION, "links": links,
            "changed_paragraphs": sum(p["new_relative_to_prior_10q"] for p in links),
            "exact_prior_text": sum(p["relation"] == "EXACT_PRIOR_TEXT" for p in links),
            "semantic_equivalence": "UNREVIEWED", "public_novelty": "UNKNOWN",
            "coverage_scope": "captured SEC filings/exhibits and explicitly imported company disclosures"}
