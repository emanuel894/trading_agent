"""Offline cover evidence only. No eligibility promotion or market calculations.

An XBRL context's reporting dates are NOT listing bounds. Combined filings must
retain the context entity so that a subsidiary cannot inherit its parent's stock.
"""
from collections import defaultdict
from html.parser import HTMLParser
import re

from .audit_store import AuditFailure
from .dated_source_review import CoverTags


class ContextEntities(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entities, self.context, self.identifier = {}, None, None

    def handle_starttag(self, tag, attrs):
        local = tag.split(":")[-1]
        if local == "context":
            if self.context is not None:
                raise AuditFailure("NESTED_IDENTITY_CONTEXT")
            self.context = dict(attrs).get("id")
        elif local == "identifier" and self.context:
            self.identifier = ""

    def handle_data(self, data):
        if self.identifier is not None:
            self.identifier += data

    def handle_endtag(self, tag):
        local = tag.split(":")[-1]
        if local == "identifier" and self.identifier is not None:
            value = self.identifier.strip()
            cik = str(int(value)).zfill(10) if re.fullmatch(r"\d{1,10}", value) else None
            if self.context in self.entities and self.entities[self.context] != cik:
                raise AuditFailure("CONFLICTING_CONTEXT_ENTITY")
            self.entities[self.context] = cik
            self.identifier = None
        elif local == "context":
            self.context = None


def identity_anchors(raw, cik):
    if len(raw) > 40_000_000:
        raise AuditFailure("IDENTITY_SOURCE_BYTE_CAP")
    text = raw.decode("utf-8")
    parser, cover = ContextEntities(), CoverTags()
    parser.feed(text)
    cover.feed(text)
    groups = defaultdict(lambda: defaultdict(list))
    for row in cover.rows:
        groups[row["context_ref"]][row["tag"]].append(row["text"])
    result = []
    for context, fields in groups.items():
        if "Security12bTitle" not in fields:
            continue
        entity = parser.entities.get(context)
        result.append({"context_ref": context, "entity_cik": entity,
                       "target_entity_match": entity == cik, "fields": dict(fields)})
    return {"target_cik": cik, "cover_groups": result,
            "unresolved_contexts": [g["context_ref"] for g in result if not g["entity_cik"]],
            "listing_interval_proven": False, "decision_receipt_proven": False}
