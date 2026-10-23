# Canonical visibility contract V1.1 open-font overlay — proposed only

Proposal ID `p0a-canonical-visibility-1.1.0-open-fonts-proposed`.
**UNAPPLIED / INACTIVE.** V1.0.0 remains the accepted baseline; PR52 is preserved.
No rendering/gate/processing authority arises from this document.

This proposal is for private synthetic qualification. Font files remain unmodified.
Narrow's publisher source archive is retained, but source-to-binary build equivalence
is unverified; no font-binary/container redistribution is cleared. Such distribution
requires an independent corresponding-source/rights check for the exact binaries.

Replace only V1 §2's logical-font-only assumption and the corresponding §5 font
qualification with the following explicit **processing assumptions** once reviewed:

1. Bind every source family/weight/style to exact unmodified font bytes and face
   indices in FONT_ARTIFACTS.json, plus the future reviewed native/config manifest.
   Initial Times New Roman maps to Liberation Serif2.1.5; Arial Narrow to Liberation
   Sans Narrow package1.07.6/internal1.07.5; Calibri to Carlito1.104; Segoe UI Symbol
   to Noto Sans Symbols2 Regular2.008. Static regular/bold/italic/bold-italic faces
   are exact physical faces where supplied. Noto Sans Symbols v2.003 is excluded
   because its cmap lacks the retained ballot characters.
2. Isolate Fontconfig to the selected13 files only. Use a separately hash-pinned
   private configuration/cache with no system includes, directories or fallback.
   Match complete family names and admitted normal/bold, normal/italic requests;
   verify selected filename SHA256, face index, variation coordinates and glyph
   availability. Generic sans-serif suffixes confer no extra fallback authority.
   Unexpected file/face/style, missing glyph or native fallback => whole-document
   AMBIGUOUS. Original family/style declarations remain recorded unchanged.
3. Symbols2 Regular covers both U+2610/U+2612. Normal symbol requests use that
   physical face without synthesis. Bold requests require an **explicitly reviewed
   native-emboldening policy**, with its exact maintained implementation/parameters
   pinned and independently qualified; never silently render regular and call it
   bold. No artificial italic, generated replacement glyph, modified font binary,
   alternate font or custom synthesis code. Until this native bold path is accepted,
   those requests abstain and the authentic document remains unqualified.
4. Freeze native font/style selection, Pango/HarfBuzz/FreeType/Fontconfig builds,
   hinting/shaping/rounding/locale/cache and all environment inputs before a gate.
   Font binary hashes alone do not pin native rendered metrics. Native output must
   expose sufficient exact source-cluster/ink/paint evidence under the existing
   mapper; a glyph cluster maps to original byte-span unions, not rewritten text.
5. These mappings and any native synthesis are canonical research-processing
   assumptions, never claims of original Microsoft-font equality or historical
   investor display. No compatibility slogan or advance-width comparison establishes
   identical rendering, visibility or completeness. Independently review material
   exclusions; uncertainty anywhere blocks the whole selected document.

Everything else remains unchanged: VISIBLE/HIDDEN/AMBIGUOUS, active-content
rejection even inside hidden trees, opaque white canvas/contrast rules, viewport,
source order/original UTF-8 spans, whitespace-only normalization, typed passive
iXBRL isolation, independent full MD&A reference, no silent loss or denominator
shrink, source/clock uncertainty, sample counts and scientific single-repair gate.
This overlay does not close PR49's geometry obligations by declaration, solve
pagination equivalence, approve a native adapter, or waive any failed oracle.

Required acceptance sequence: owner + independent scientific/security review of
this versioned assumption change; a new explicit update proposal to the inactive
synthetic-only security exception referencing exact accepted hashes; full G0
artifact/license/isolation/oracle acceptance; then **separate explicit gate
authorization**. Any scientific target/criterion/materiality change requires its
own versioned scientific amendment first. Do not apply this overlay, edit PR52,
modify original registrations or execute the gate in this task.
