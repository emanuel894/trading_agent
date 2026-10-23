"""Design evidence only: evaluate frozen V2 JSON, never parse/render a filing.

No application imports, source-file access, layout, extraction, network or inference.
Run: python evaluate_inventory.py INVENTORY_DIRECTORY OUTPUT_DIRECTORY
The output records proof obligations, NOT authentic text classifications.
"""
import gzip
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(root, output):
    binding = json.loads((Path(__file__).parent / "bindings.json").read_text())
    for name, expected in binding["inventory_sha256"].items():
        if sha(root / name) != expected:
            raise ValueError("INVENTORY_HASH_MISMATCH: " + name)
    nodes = json.loads((root / "nodes.json").read_text())
    css = json.loads((root / "css.json").read_text())
    styles = {}
    for s in css["styles"]:
        declarations = s["declarations"]
        if not all(valid for _, _, valid in declarations):
            raise ValueError("INVALID_INVENTORIED_DECLARATION")
        d = {k: v for k, v, _ in declarations}
        if len(d) != len(declarations):
            raise ValueError("DUPLICATE_INVENTORIED_PROPERTY")
        styles[s["node"]] = d
    substantive = [False] * len(nodes)
    for i in range(len(nodes) - 1, -1, -1):
        n = nodes[i]
        substantive[i] = any(t.strip() for t in n["data"]) or any(
            substantive[j] for j in n["children"])
    table_owner = [None] * len(nodes)
    for i, n in enumerate(nodes):
        table_owner[i] = i if n["tag"] == "table" else (
            table_owner[n["parent"]] if n["parent"] is not None else None)
    tables = [i for i, n in enumerate(nodes) if n["tag"] == "table"]
    table_facts = {}
    for i in tables:
        rows = nodes[i]["children"]
        sums = []
        for j in rows:
            if nodes[j]["tag"] != "tr":
                raise ValueError("UNEXPECTED_TABLE_CHILD")
            total = 0
            for k in nodes[j]["children"]:
                if nodes[k]["tag"] != "td":
                    raise ValueError("UNEXPECTED_ROW_CHILD")
                attrs = dict(nodes[k]["attrs"])
                if "rowspan" in attrs:
                    raise ValueError("UNEXPECTED_ROWSPAN")
                span = int(attrs.get("colspan", "1"))
                if span <= 0:
                    raise ValueError("INVALID_COLSPAN")
                total += span
            sums.append(total)
        a = nodes[i]["parent"]
        nested = False
        while a is not None:
            nested |= nodes[a]["tag"] == "table"
            a = nodes[a]["parent"]
        table_facts[i] = {"row_count": len(rows), "column_sums": sorted(set(sums)),
                          "nested_table": nested, "style": styles.get(i, {})}

    records = []
    gap_counts = {}

    def add(gap, i, local, reason, **facts):
        n = nodes[i]
        records.append({"gap": gap, "node": i, "tag": n["tag"],
                        "span": [n["start"], n["end"]], "parent": n["parent"],
                        "local": local, "reason": reason,
                        "has_nonwhitespace_descendant": substantive[i], **facts})

    flex = [i for i, s in styles.items() if s.get("display") in ("flex", "inline-flex")]
    for i in flex:
        n, s = nodes[i], styles[i]
        direction = s.get("flex-direction", "row")
        # Only local sizing facts close. Neither result admits the document.
        if not substantive[i]:
            local, reason = "LOCAL_CLOSED", "F_EMPTY_NO_TEXT"
        elif direction == "column":
            local, reason = "LOCAL_CLOSED", "F_AUTO_MAIN_SIZE_MINIMUM_ONLY"
        else:
            local, reason = "NEEDS_CERTIFICATE", "F_UNBOUNDED_INLINE_INK_AND_MIN_CONTENT"
        add("F", i, local, reason, direction=direction,
            defaults={"grow": "0", "shrink": "1", "basis": "auto", "wrap": "nowrap",
                      "order": "0", "min_width": "auto unless explicit"},
            element_items=[{"node": j, "span": [nodes[j]["start"], nodes[j]["end"]],
                            "style": styles.get(j, {})} for j in n["children"]],
            anonymous_nonwhitespace_text_segments=[k for k, item in enumerate(n["content"])
                                                   if item[0] == "text" and item[1].strip()])

    table_nodes = [i for i, n in enumerate(nodes) if n["tag"] in ("table", "tr", "td")]
    collapsed = []
    for i in table_nodes:
        n, s = nodes[i], styles.get(i, {})
        if s.get("visibility") == "collapse":
            collapsed.append(i)
            overrides = []
            todo = list(n["children"])
            while todo:
                j = todo.pop()
                if "visibility" in styles.get(j, {}):
                    overrides.append(j)
                todo.extend(nodes[j]["children"])
            if substantive[i] or overrides:
                raise ValueError("COLLAPSE_LOCAL_PROOF_FAILED")
            local, reason = "LOCAL_CLOSED", "T_EMPTY_COLLAPSE_HIDDEN_LEDGER_REQUIRED"
        else:
            overrides = []
            local, reason = "NEEDS_CERTIFICATE", "T_GRID_IS_NOT_TEXT_INK_CONTAINMENT"
        add("T", i, local, reason, table=table_owner[i],
            style=s, visibility_overrides=overrides)

    positions = [i for i, s in styles.items() if "position" in s]
    forbidden = {"top", "right", "bottom", "left", "inset", "transform", "float",
                 "overflow", "clip", "clip-path", "opacity", "order"}
    for i, s in styles.items():
        if forbidden.intersection(s):
            raise ValueError("UNEXPECTED_DISPLACEMENT_OR_CLIPPING")
    for i in positions:
        s = styles[i]
        if s["position"] != "relative":
            raise ValueError("UNEXPECTED_POSITION")
        add("P", i, "LOCAL_CLOSED", "P_ZERO_TRANSLATION_NOT_A_GLOBAL_PAINT_PROOF",
            z_index=s["z-index"], parent=nodes[i]["parent"])

    interaction_keys = {"width", "min-width", "white-space", "background-color"}
    interaction = [i for i, s in styles.items() if interaction_keys.intersection(s)]
    for i in interaction:
        s = styles[i]
        # Inline min-width has no sizing effect; flex items are blockified.
        parent_display = styles.get(nodes[i]["parent"], {}).get("display")
        ignored_min = s.get("min-width") == "fit-content" and nodes[i]["tag"] == "span" \
            and parent_display not in ("flex", "inline-flex")
        add("W", i, "NEEDS_CERTIFICATE", "W_NO_GEOMETRIC_CONTAINMENT_CERTIFICATE",
            declarations={k: s[k] for k in sorted(interaction_keys.intersection(s))},
            ordinary_inline_min_width_inapplicable=ignored_min,
            direct_flex_item=parent_display in ("flex", "inline-flex"),
            table=table_owner[i])

    hanging = [i for i, s in styles.items() if s.get("text-indent", "").startswith("-")]
    if hanging != [4996]:
        raise ValueError("UNEXPECTED_HANGING_CONTEXT")
    W = Decimal(1280) - Decimal(16)
    pad = W * Decimal("0.03333")
    indent = W * Decimal("-0.03448")
    origin = Decimal(8) + pad + indent
    add("H", 4996, "NEEDS_CERTIFICATE", "H_REFERENCE_POINT_SAFE_INK_BEARING_UNKNOWN",
        containing_width_px=str(W), padding_px=str(pad), indent_px=str(indent),
        first_line_reference_x_px=str(origin), glyph_left_bearing_bound=None)

    for gap in "FTPWH":
        subset = [r for r in records if r["gap"] == gap]
        gap_counts[gap] = {"instances": len(subset),
                           "local_results": dict(Counter(r["local"] for r in subset))}
    # Design-oracle arithmetic only. Rectangles and metrics are supplied premises,
    # never inferred from authentic markup or used to classify authentic text.
    oracle_checks = {
        "F_positive_supplied_metrics": Decimal(3) + Decimal(97) == Decimal(100),
        "F_negative_marker_overhang": Decimal(6) > Decimal(3),
        "T_positive_ink_within_row": 0 <= 1 < 11 <= 12,
        "T_negative_ink_crosses_next_row": 14 > 12,
        "P_positive_disjoint_owner_y": 10 < 20,
        "P_negative_owner_ink_overlap": 23 > 20,
        "W_positive_advance_fits": 30 <= 40,
        "W_negative_advance_does_not_fit": 30 > 20,
        "H_positive_supplied_bearing": origin - Decimal(2) > 0,
        "H_negative_supplied_bearing": origin - Decimal(8) < 0,
    }
    if not all(oracle_checks.values()):
        raise ValueError("ORACLE_ARITHMETIC_FAILED")
    output.mkdir(parents=True, exist_ok=True)
    packed = b"".join((json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n").encode()
                      for r in records)
    detailed = output / "instances.jsonl.gz"
    detailed.write_bytes(gzip.compress(packed, mtime=0))
    summary = {"evaluation_id": "p0a-final-composition-1.0.0", "design_only": True,
        "baseline": binding["baseline"], "inventory_sha256": binding["inventory_sha256"],
        "counts": {"nodes": len(nodes), "styles": len(styles), "gap_results": gap_counts,
                   "records": len(records), "unique_evaluated_nodes": len({r['node'] for r in records}),
                   "table_roles": dict(Counter(nodes[i]["tag"] for i in table_nodes)),
                   "collapsed_rows": len(collapsed),
                   "row_backgrounds": dict(Counter(s["background-color"] for s in styles.values()
                                                    if "background-color" in s)),
                   "width_declarations": sum("width" in s for s in styles.values()),
                   "nowrap_cells": sum(s.get("white-space") == "nowrap" for s in styles.values()),
                   "inline_ineffective_fit_content": sum(s.get("min-width") == "fit-content"
                                                        for s in styles.values())},
        "tables": table_facts, "hanging_indent": records[-1],
        "oracle_arithmetic": oracle_checks,
        "oracles_executed": "10 scalar assertions on supplied synthetic premises only; no CSS/DOM processor",
        "details": {"file": detailed.name, "sha256": sha(detailed),
                    "uncompressed_sha256": hashlib.sha256(packed).hexdigest()},
        "authentic_text_classification": "NOT_PERFORMED",
        "authentic_extraction_replays": 0, "source_parses": 0, "renders": 0,
        "research_inference_calls": 0, "external_spend_usd": 0,
        "decision": "B_ARCHITECTURAL_BLOCKER_NO_GO",
        "processing_latency_memory": "NOT_MEASURED; JSON evaluation is not extraction or inference"}
    (output / "evaluation.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"counts": summary["counts"], "details": summary["details"],
                      "oracle_assertions": len(oracle_checks), "decision": summary["decision"]}))


if __name__ == "__main__":
    evaluate(Path(sys.argv[1]), Path(sys.argv[2]))
