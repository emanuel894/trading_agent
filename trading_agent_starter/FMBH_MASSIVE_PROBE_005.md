# Owner-local Amendment 005 FMBH reference probe

Amendment 005 SHA-256:
`26eeca3bc843f0de0dab53b61fa2008773e1616d888bb165111fabe8a2c38cc5`.
Canonical bytes: `research/structural_identity_registration_005.json`.
The module checks this hash and protected 003/004 artifacts before requests.

From the updated branch's **trading_agent_starter** directory, with
`MASSIVE_API_KEY` already in the local `.env` or environment, run this Windows
command. Existing project dependencies suffice; no new package is needed.

```powershell
.venv\Scripts\python.exe -m agent.massive_reference_probe --store runs\fmbh_massive_reference_005
```

The loader reads only the explicit current-directory `.env`, disables variable
interpolation, and lets the environment take precedence. It never prints or
persists the key. Authentication uses `Authorization: Bearer ...`; headers are
not archived. Official authentication definition:
https://massive.com/docs/rest/quickstart.

The fixed request contract is `GET https://api.massive.com/v3/reference/tickers`
with `ticker=FMBH`, `market=stocks`, `active=true`, `limit=10`, and exactly these
dates in this order: **2025-02-04, 2025-04-30, 2025-05-01, 2025-05-09**.
There are at most four requests and 13 seconds between request starts. No
retries or redirects are followed; no pagination is followed. A stop may leave
fewer than four dates captured. No CIK/type/exchange/FIGI filter is sent.

## Exact output contract

Successful execution of the process prints one JSON object and writes the same
object to a uniquely named `reference-probe-<uuid>.json` within the selected
store. The append-only `evidence.sqlite` and content-addressed `objects` preserve
each response version and request provenance; reruns never overwrite records.

| Top-level field | Meaning |
| --- | --- |
| `version` | `fmbh-massive-reference-probe-v1` |
| `registration_sha256`, `amendment_004_sha256` | Exact 005 and inherited 004 registration hashes |
| `candidate` | `cik`, `priority`, `priority_digest`, pinned to candidate #1 |
| `created_at` | Actual run creation timestamp |
| `status` | `PASS`, `FAIL`, or `UNRESOLVED` for this bounded capture/consistency check only |
| `stop_reason` | Stable reason code, or null if all four responses passed |
| `dates` | Ordered per-date records, including the stopping record |
| `requests_made` | Actual attempted HTTP requests, at most four |
| `unrequested_dates` | Remaining registered dates not attempted after a stop |
| `eligibility_decision` | Always `UNRESOLVED` |
| `ledger_modified` | Always false |
| `structural_validation_performed` | Always false: the probe never auto-admits a source |
| `store_verification` | Existing evidence-store `status`, `records`, `head_hash` |

Each `dates` item has `date`, `status`, `reason`, `fields`, `missing_fields`.
Once an HTTP evidence record exists it also has `http_status`, `retrieved_at`,
`provider_request_id` (null if absent), `evidence_reference` (`record_id`,
`sha256`), `parameters`, and `access`. `access=HTTP_200` remains independent of
row quality/identity disagreement. An HTTP error retains its numeric status
and a stable access failure code; it does not become economic ineligibility.

For a single object result, `fields` contains only supplied values among `cik`,
`ticker`, `type`, `primary_exchange`, `active`, `share_class_figi`,
`last_updated_utc`. Absent properties stay absent and are listed in
`missing_fields`; supplied nulls are preserved as null, then validated.
Ambiguous response rows stay available in the raw object, not arbitrarily
collapsed to a chosen row. All additional provider fields, including future
revision metadata, remain preserved in the raw response. `last_updated_utc`
never becomes `known_at`, `available_at`, first publication, or effective time.

`PASS` means four well-formed reference responses with exactly one result each,
matching CIK 0000700565, ticker FMBH, type CS, primary exchange XNAS and active
boolean true. Optional FIGI/update-time strings can be absent. Supplied FIGIs
must agree across these four responses. No historical FIGI is invented.
Neither HTTP 200 nor probe PASS establishes lineage completeness, all 60 dates,
exact May cutoff/action state, liquidity eligibility or trading readiness.

## Stop conditions and failures

- `FAIL`: `IDENTIFIER_DISAGREEMENT:<field>`, including inconsistent supplied
  share-class FIGIs. Preserve the observed value; leave the candidate ledger
  UNRESOLVED. A discrepancy is for investigation, not automatic exclusion.
- `UNRESOLVED`: `MISSING_RESULT`, `AMBIGUOUS_MULTIPLE_ROWS`,
  `UNEXPECTED_PAGINATION`, `MISSING_IDENTITY_FIELD:<field>`,
  `MALFORMED_OPTIONAL_FIELD:<field>`, `MALFORMED_REFERENCE_ROW`,
  `PROVIDER_RESPONSE_STRUCTURE`, strict-JSON validation errors, authentication/
  access rejection (401/403), rate limiting (429), other HTTP failure, redirect,
  network/read failure, byte limit or credential-echo detection. Stop immediately.
- Missing optional FIGI/update-time is reported without invention and does not
  by itself fail this access/schema pilot. Present malformed optional values stop.
- Each body is capped at 262,144 bytes. If oversized or containing the API key
  (including a JSON-escaped echo), it is **not persisted**; the record instead
  records `RESPONSE_BYTE_LIMIT` or `SECRET_ECHO_BLOCKED`, with
  `raw_response_preserved=false`. Credential non-retention takes precedence over
  archiving a contaminated provider response. Other permitted bodies, including
  provider errors and malformed JSON, are preserved byte-for-byte.
- Preflight failures print `{status: UNRESOLVED, stop_reason: <code>,
  eligibility_decision: UNRESOLVED}` before requests. A local filesystem or
  configuration exception prints only `status` and
  `stop_reason=LOCAL_IO_OR_CONFIGURATION_FAILURE`; no exception detail/key.
  `MASSIVE_API_KEY_UNAVAILABLE` and `MASSIVE_API_KEY_INVALID` are stable codes.
  Corrupt stores or changed protected registration artifacts fail before access.
- Exit code 0 means probe PASS; all other handled outcomes exit 2. Credentials
  and response bodies are never printed. Fixed observed fields are JSON-encoded.

## Offline structural validator boundary

`agent.acquisition_identity.validate_structural` is the separate 005 entry
point. It requires the exact acquisition purpose, same CIK/internal class ID,
field-specific documented historical-state semantics, hash-verified raw/source-
documentation/reviewer spans and explicit lineage/class completeness review.
Source capture metadata binds `valid_time` and historical semantics; callers
cannot simply relabel a current-only or later-period SEC record historical.

Clock-B fields (`published_at`, `captured_at`, `revised_at`, `known_at`,
`available_at`) may be null for structural reconstruction. They and actual
`retrieved_at` must match preserved source-record metadata. Source resolution
must match the reviewed documentation. A date observation cannot satisfy an
instant requirement without an independent, matching exact-interval record and
grounded interval evidence. Unresolved carry-in, transitions, lineage or class
completeness blocks. Review metadata are assertions to be substantively reviewed,
not a machine-generated guarantee of a provider's historical accuracy.

Nonstructural fields receive no exception; `validate_decision_time` still
requires known/available timestamps no later than the decision. The original
economic-selector and evidence-audit time guards remain byte-for-byte unchanged.
No existing call is globally redirected to the new helper. The probe is a
capture tool only and never invokes structural approval or ledger mutation.
