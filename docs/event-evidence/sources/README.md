# Current source-review packet

Public documentation reviewed October 18, 2026. Each capture records actual UTC
retrieval, requested/final URL, HTTP result, raw byte count and raw/archive SHA-256.
The gzip files retain the received documentation bytes, including error pages.
They are not ingested market/news data, and their retrieval does not establish
historical event availability or source completeness. No authenticated source API,
paid provider, model endpoint or broker was called.

Primary evidence is official agency documentation and provider-owned technical
documentation. `fredapi` is independent community source; `beaapi` is linked from
BEA's developer page. GitHub commit metadata pins inspected clients without
installing/importing them. Web search aided discovery; claims rely on the directly
captured documents below. Failed speculative paths are retained, not treated as
proof that a service or document does not exist.

## Capture inventory

| ID | Source | HTTP | Evidence qualification |
| --- | --- | --- | --- |
| F01 | [FRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html) | 200 | Documentation/source only; not feed qualification |
| F02 | [FRED vintage dates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html) | 200 | Documentation/source only; not feed qualification |
| F03 | [FRED observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) | 200 | Documentation/source only; not feed qualification |
| F04 | [FRED terms](https://fred.stlouisfed.org/legal/) | 200 | Documentation/source only; not feed qualification |
| M01 | [FOMC calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) | 200 | Documentation/source only; not feed qualification |
| M02 | [Fed statement release example](https://www.federalreserve.gov/newsevents/pressreleases/monetary20240918a.htm) | 200 | Documentation/source only; not feed qualification |
| M03 | [Fed speech release example](https://www.federalreserve.gov/newsevents/speech/powell20240823a.htm) | 200 | Documentation/source only; not feed qualification |
| B01 | [BLS API signatures](https://www.bls.gov/developers/api_signature_v2.htm) | 200 | Documentation/source only; not feed qualification |
| B02 | [BLS revisions](https://www.bls.gov/about-bls/revisions.htm) | 200 | Documentation/source only; not feed qualification |
| B03 | [BLS release archives](https://www.bls.gov/bls/news-release/home.htm) | 200 | Documentation/source only; not feed qualification |
| B04 | [BLS errata](https://www.bls.gov/errata/home.htm) | 200 | Documentation/source only; not feed qualification |
| B05 | [BLS CPI release example](https://www.bls.gov/news.release/archives/cpi_09112024.htm) | 200 | Documentation/source only; not feed qualification |
| E01 | [BEA API documentation](https://apps.bea.gov/API/docs/index.htm) | 200 | Documentation/source only; not feed qualification |
| E02 | [BEA GDP vintage and releases](https://www.bea.gov/data/gdp/gross-domestic-product) | 200 | Documentation/source only; not feed qualification |
| E03 | [BEA release archive](https://www.bea.gov/news/archive) | 200 | Documentation/source only; not feed qualification |
| E04 | [BEA official developers and clients](https://www.bea.gov/resources/for-developers) | 200 | Documentation/source only; not feed qualification |
| R01 | [Federal Register API documentation](https://www.federalregister.gov/developers/documentation/api/v1) | 200 | Documentation/source only; not feed qualification |
| R02 | [Federal Register public inspection](https://www.federalregister.gov/reader-aids/using-federalregister-gov/understanding-public-inspection) | 200 | Documentation/source only; not feed qualification |
| R03 | [GovInfo official Federal Register](https://www.govinfo.gov/help/fr) | 200 | Documentation/source only; not feed qualification |
| O01 | [OFAC historical changes FAQ](https://ofac.treasury.gov/faqs/466) | 200 | Documentation/source only; not feed qualification |
| O02 | [OFAC delta archive](https://sanctionslist.ofac.treas.gov/Home/DeltaFileArchive) | 200 | 200 app shell only; historical payloads not established |
| T01 | [USTR Section 301 tariff actions](https://ustr.gov/issue-areas/enforcement/section-301-investigations/tariff-actions) | 200 | Discovery index; no exact publication-time guarantee |
| T02 | [Commerce BIS Federal Register notices](https://www.bis.gov/federal-register-notices) | 404 | Attempted BIS route unavailable |
| T03 | [CBP Cargo Systems Messaging Service](https://www.cbp.gov/trade/automated/cargo-systems-messaging-service) | 403 | CBP page blocked |
| A01 | [USAspending official transaction API contract](https://raw.githubusercontent.com/fedspendingtransparency/usaspending-api/master/usaspending_api/api_contracts/contracts/v2/transactions.md) | 200 | Documentation/source only; not feed qualification |
| A02 | [USAspending official search filter contract](https://raw.githubusercontent.com/fedspendingtransparency/usaspending-api/master/usaspending_api/api_contracts/search_filters.md) | 200 | Documentation/source only; not feed qualification |
| A03 | [Defense contracts announcements](https://www.defense.gov/News/Contracts/) | 403 | Defense announcement page blocked |
| S01 | [SEC EDGAR API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | 200 | Documentation/source only; not feed qualification |
| S02 | [SEC Form 8-K](https://www.sec.gov/files/form8-k.pdf) | 403 | Blocked PDF attempt; no form-specific claim |
| N01 | [Benzinga news documentation](https://docs.benzinga.com/benzinga-apis/newsfeed-v2) | 404 | Attempted path unavailable; N06 supplies current stream documentation |
| N02 | [Benzinga official integration guidance](https://docs.benzinga.com/home) | 200 | Documentation/source only; not feed qualification |
| N03 | [Benzinga official lifecycle guide](https://www.benzinga.com/apis/blog/mastering-the-benzinga-newsfeed-api/) | 200 | Documentation/source only; not feed qualification |
| N04 | [Benzinga documentation index](https://docs.benzinga.com/llms.txt) | 200 | Documentation/source only; not feed qualification |
| T04 | [BIS regulations](https://www.bis.gov/regulations) | 404 | Alternate BIS route unavailable |
| A04 | [USAspending official data guidance](https://www.usaspending.gov/data/about-the-data-download.pdf) | 200 | Documentation/source only; not feed qualification |
| S03 | [SEC Form 8-K alternate official URL](https://www.sec.gov/files/form8k.pdf) | 404 | Alternate PDF path returned 404; no form-specific claim |
| W01 | [fredapi current commit metadata](https://api.github.com/repos/mortada/fredapi/commits/master) | 200 | Documentation/source only; not feed qualification |
| W03 | [BEA official client current commit metadata](https://api.github.com/repos/us-bea/beaapi/commits/main) | 200 | Documentation/source only; not feed qualification |
| W02 | [mortada/fredapi pinned client source](https://raw.githubusercontent.com/mortada/fredapi/d0a0ba3001ebbbceafdcbdd3eb23828f0537cdff/fredapi/fred.py) | 200 | Documentation/source only; not feed qualification |
| W04 | [us-bea/beaapi pinned client source](https://raw.githubusercontent.com/us-bea/beaapi/0d44ba252c5fbb8147656631f907dcfe598454d4/README.md) | 200 | Documentation/source only; not feed qualification |
| N05 | [Benzinga news OpenAPI contract](https://docs.benzinga.com/openapi/news-api.spec.yml) | 404 | Advertised spec path returned 404; no API contract inferred |
| N06 | [Benzinga news stream contract](https://docs.benzinga.com/ws-reference/data-websocket/get-news-stream.md) | 200 | Documentation/source only; not feed qualification |
| R04 | [Federal Register public API OpenAPI schema](https://www.federalregister.gov/api/v1/openapi.json) | 404 | Attempted OpenAPI route returned 404; R01/R02 remain usable |

## Bounded source quotations and design inferences

The machine-readable [claim index](claims.json) binds each quotation to normalized
character offsets in the retained bytes. Each source contributes at most 25
quoted words. Interpretations are our design inferences, not provider guarantees.
For A04, the PDF and hashed `pdftotext -layout` output are both retained; its
decoding version is in the capture record.

| ID | Exact bounded excerpt | Design implication |
| --- | --- | --- |
| F01 | YYYY-MM-DD formatted dates that default to today's date | Vintage defaults and precision are date-based; no intraday receipt follows. |
| F02 | excluding release dates when the data for the series did not change | A vintage-date inventory is not a complete scheduled-event inventory. |
| F04 | Series with a copyright notice are owned by third parties and have special restrictions. | Rights must be assessed per series and purpose; free reachability does not settle retention or AI-use rights. |
| M01 | The minutes of regularly scheduled meetings are released three weeks after the date of the policy decision. | Minutes are distinct later publications, not meeting-date evidence. |
| M02 | For release at 2:00 p.m. EDT | Document asserts a release time; it is not a receipt log. |
| M03 | August 23, 2024 | A speech date alone does not establish when prepared text, delivery, or Q&A became machine-observable. |
| B01 | "periodName": "November" | API sample carries reference periods, values and footnotes; no historical receipt evidence is demonstrated. |
| B02 | additional information that was not available at the time of the initial release | Revisions incorporate later information and cannot replace initial predictive values. |
| B04 | Errata | Corrections must be monitored separately from scheduled revisions; archive coverage still needs qualification. |
| E02 | Previously published estimates contain historical data and have since been revised. | BEA provides routes to prior estimates and vintage history; current GDP values are not original releases. |
| E03 | Data may be superseded. | Archive discovery does not establish completeness or immutable original content. |
| E04 | Python and R packages | BEA links its own client projects; agency provenance differs from independent wrappers. |
| R01 | It is not an official legal edition of the Federal Register | Use discovery XML separately from authoritative legal renditions. |
| R02 | the exact time may vary depending upon server usage and other factors | Official filing and online posting clocks may differ; do not equate them. |
| R03 | official legal equivalent of the paper and microfiche editions | GovInfo official edition is the legal-rendition cross-check, not a receipt-time service. |
| O01 | Designation, removal, and update information is organized chronologically by list and by year. | OFAC provides historical change discovery; exact instants and complete payload replay need qualification. |
| A01 | their amount, type, action date, action type, modification number, and description | Award action dates are transaction semantics, not demonstrated public-release clocks. |
| A02 | Typically, `action_date` represents the date of the latest transaction associated with the award. | Filter dates must not be used to backdate public availability. |
| S01 | These APIs do not require any authentication or API keys to access. | Official submissions transport is accessible without credentials; issuer/wire earlier releases remain separate. |
| N03 | Delta sync by last update time. Useful for polling. | Update polling and removal IDs alone do not establish replay of every original article version. |
| N06 | Replay up to the last 100 cached messages | Bounded stream replay is not a historical full-version archive or complete outage recovery guarantee. |
| W02 | data = df[df['realtime_start'] <= as_of_date] return data | Pinned fredapi as-of helper filters revisions but does not select a unique latest row per observation. |
| W04 | A Python library library to make it easier to retrieve and work with BEA data. | Officially linked BEA client is transport/convenience, not proof of vintage completeness. |
| A04 | on a 90-day delay in the Federal Procurement Data System (FPDS). | Official guidance documents delayed DOD/USACE procurement reporting; action dates cannot establish contemporaneous public announcements. |

## Context and verification

[PR #10 context](pr10-context.json) preserves the specifically read architecture
section at remote head `4dd7703f429df01a6f7e67912294ec26e93b4ad0`. This was read-only;
its branch is never a push target for this work. The current base policies retain
authority over that draft audit.

Recheck hashes and excerpt offsets with [the offline verifier](../verify_artifacts.py).
Integrity verifies the captured text, not its truth, rights, completeness, or
historical availability. Requalify mutable documentation before later acquisition.
