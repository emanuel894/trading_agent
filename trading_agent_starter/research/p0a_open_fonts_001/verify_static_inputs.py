"""Reproduce the design-only font/hash/cmap checks; never shape or render text.

Usage: python verify_static_inputs.py FONT_WORK_DIRECTORY RETAINED_V2_DIRECTORY
Requires the existing audit-reader fontTools4.61.1; no package installation here.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys
import tarfile

import fontTools
from fontTools.ttLib import TTFont


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(work, inventory):
    here = Path(__file__).parent
    lock = json.loads((here / "FONT_ARTIFACTS.json").read_text())
    expected = json.loads((here / "COVERAGE.json").read_text())
    assert fontTools.__version__ == lock["analysis_tool"]["version"]
    for x in lock["downloaded_artifacts"]:
        p = work / "artifacts" / x["name"]
        assert p.stat().st_size == x["bytes"] and digest(p) == x["sha256"]
    for x in lock["license_files"]:
        p = work / "licenses" / x["file"]
        assert p.stat().st_size == x["bytes"] and digest(p) == x["sha256"]
    assert digest(inventory / "nodes.json") == expected["inventory_nodes_sha256"]
    assert digest(inventory / "css.json") == expected["inventory_css_sha256"]
    nodes = json.loads((inventory / "nodes.json").read_text())
    styles = {s["node"]: {k: v for k, v, valid in s["declarations"]}
              for s in json.loads((inventory / "css.json").read_text())["styles"]}
    inherited, points, runs = [], defaultdict(set), defaultdict(int)
    for i, n in enumerate(nodes):
        parent = inherited[n["parent"]] if n["parent"] is not None else {
            "font-family": "Times New Roman", "font-weight": "normal", "font-style": "normal"}
        current = {k: styles.get(i, {}).get(k, v) for k, v in parent.items()}
        inherited.append(current)
        key = tuple(current[k] for k in ("font-family", "font-weight", "font-style"))
        for text in n["data"]:
            if text:
                points[key].update(map(ord, text))
                runs[key] += 1
    assert len(points) == len(expected["results"]) == 9
    fonts = {}
    for x in lock["fonts"]:
        p = work / "bundle" / x["file"]
        assert p.stat().st_size == x["bytes"] and digest(p) == x["sha256"]
        f = TTFont(p)
        assert f["name"].getDebugName(1) == x["family"]
        assert f["name"].getDebugName(2) == x["style"]
        assert f["name"].getDebugName(5) == x["version"]
        assert f["head"].unitsPerEm == x["metrics"]["unitsPerEm"]
        fonts[x["file"]] = f
    for x in expected["results"]:
        key = (x["source_family"], x["weight"], x["style"])
        cps = points[key]
        assert [f"U+{c:04X}" for c in sorted(cps)] == x["inventory_codepoints"]
        assert runs[key] == x["runs"]
        required = cps - {9, 10, 13}
        assert len(required) == x["required_cmap_characters"]
        cmap = fonts[x["font_file"]].getBestCmap()
        assert not [c for c in required if cmap.get(c, ".notdef") == ".notdef"]
        if x["style_status"] == "NATIVE_EMBOLDENING_REQUIRED_NOT_QUALIFIED":
            assert fonts[x["font_file"]]["name"].getDebugName(2) == "Regular"
    assert all(c not in fonts["notosanssymbols.ttf"].getBestCmap() for c in (0x2610, 0x2612))
    with tarfile.open(work / "artifacts" / lock["narrow_publisher_source_archive"], "r:gz") as t:
        names = {Path(m.name).name for m in t.getmembers() if m.isfile()}
        assert {"COPYING", "License.txt", "Makefile"}.issubset(names)
        assert {f"LiberationSansNarrow-{s}.sfd" for s in
                ("Regular", "Bold", "Italic", "BoldItalic")}.issubset(names)
    for f in fonts.values():
        f.close()
    return {"artifact_license_hashes": "PASS", "inventory_character_cmaps": "PASS",
            "groups": 9, "selected_files": 13, "bold_symbol_runs_not_qualified": 2,
            "shaping_or_layout": "NOT_RUN", "g0": "NOT_QUALIFIED"}


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))
