# Trading Agent V1 — Technical Specification

**גרסה:** 1.0-draft לאחר Gap Analysis · **תאריך:** 14.09.2026  
**הקשר:** תושב ישראל, חשבון אישי, נכסים אמריקאיים, Interactive Brokers, Paper בלבד עד אישור מעבר נפרד.

## 1. מטרה וגבולות

המערכת תסרוק 10–20 מניות ו/או ETF נזילים, תחשב החלטות כל 30 דקות כברירת מחדל בטווח 15–60 דקות, ותוכל להחזיק פוזיציה שעה עד מספר ימים. היא רשאית להחליט `HOLD` או `DO_NOTHING`; היעדר עסקה הוא תוצאה תקינה. היא תריץ סיכון וביצוע אוטומטיים בחשבון Paper ללא אישור ידני לכל עסקה.

V1 אינה HFT, אינה ממונפת, אינה מוכרת בחסר, אינה סוחרת באופציות ואינה פועלת בשעות מורחבות. מודל AI לא משנה limits, credentials או policy של ה־Risk Engine. מעבר ל־Live הוא release נפרד שדורש אישור מפורש.

## 2. ארכיטקטורה לוגית

```text
Market Data Adapter
  -> Raw Store + Data Validation + Event Clock
  -> Feature Engine
  -> Baseline Strategy / ML Candidate
  -> Optional AI Event Layer (structured, budgeted, fail-to-HOLD)
  -> Signal Contract
  -> Deterministic Portfolio + Risk Engine (veto)
  -> Durable Order Intent / Outbox (single account writer)
  -> IBKR TWS API Paper
  -> Order Events / Fills / Reconciliation
  -> Journal + Evaluation + Alerts
```

מקור האמת לפוזיציה, פקודות ו־fills הוא IBKR לאחר reconciliation; מצב זיכרון מקומי אינו מקור אמת. כל זמן נשמר ב־UTC, ובנוסף נשמרים `event_time`, `available_time`, `decision_time`, `submit_time`, `ack_time` ו־`fill_time`.

## 3. חוזי נתונים

### Market data

- אותות: bars של 30 דקות שהושלמו; המערכת תוכל להריץ 15 או 60 דקות דרך configuration, אך לא תבצע tuning לפי test.
- ביצוע ו־slippage: 1-minute bars ו/או bid/ask quotes עם receive timestamp. אם אין quote זמין, הגדלת פוזיציה נחסמת או עוברת לתרחיש עלות שמרני.
- שדות bar: `symbol`, `event_time`, `open`, `high`, `low`, `close`, `volume`, `source`, `received_at`, `is_complete`.
- שדות quote: `symbol`, `event_time`, `bid`, `ask`, `bid_size`, `ask_size`, `received_at`, `source`.
- corporate actions: split/dividend ומועד זמינות; מחיר מחקר מתואם אינו מוחל אוטומטית על מחיר execution.
- universe: רשימת נכסים עם `valid_from`/`valid_to`; אין שימוש ב־survivorship-biased universe.
- calendar: America/New_York, RTH, חגים, early closes, halts ו־DST; נתוני אחסון ב־UTC.
- חדשות/filings: `published_at`, `available_at`, source, symbol/entity, event type, materiality, model version. טקסט שהופיע אחרי זמן ההחלטה אסור לשימוש.

IBKR הוא broker/execution source. למחקר היסטורי נשתמש רק במקור בעל רישיון ותיעוד היסטורי מספיק; נתוני Paper או נתונים מושהים אינם הוכחה ל־live slippage.

### Signal contract

כל strategy מחזירה JSON/record מובנה:

```json
{
  "run_id": "...", "symbol": "SPY", "as_of": "UTC",
  "action": "BUY|SELL|HOLD", "target_weight": 0.0,
  "expected_holding_bars": 0, "confidence": 0.0,
  "model_version": "baseline-v1", "features_hash": "...",
  "reason_code": "trend_filter|risk_exit|no_edge"
}
```

Confidence אינה עוקפת סיכון ואינה מומרת ישירות לגודל פוזיציה בלי policy מוגדר.

## 4. Phase 0 — Research to Specification

### תוצרים

1. מפרט זה חתום בגרסה, כולל universe, timeframe, benchmark, cost assumptions, risk defaults ו־gates.
2. `data_manifest` לכל קובץ: מקור, רישיון, timezone, coverage, corporate-action policy, checksum ו־availability semantics.
3. schemas ל־bars, quotes, features, signals, decisions, orders, fills ו־portfolio snapshots.
4. calendar ו־clock policy; בדיקת event/receive/decision separation.
5. design של A–D baseline matrix עם אותה תקופת evaluation, אותו capital model ואותן עלויות.
6. experiment registry: פרמטרים, git revision, data version, seed, output metrics, failed trials והאם ה־test נפתח.
7. acceptance checklist ו־kill conditions לפני כתיבת execution manager.

### Phase 0 לא כולל

אין אופטימיזציית hyperparameters על test, אין fine-tuning, אין order submission, אין שימוש במנוי AI בתשלום ואין טענה לרווחיות.

### יציאה מ־Phase 0

כל ההחלטות הקבועות לעיל מופיעות בקובץ versioned; dataset נבדק; smoke test מזהה timestamp לא־מונוטוני, missing bars, future availability ו־duplicate rows; וניתן להריץ baseline על אותו קובץ באופן חוזר עם checksum זהה.

## 5. Phase 1 — Baseline ללא AI

### Baselines להשוואה

- **A — Passive:** buy-and-hold SPY, עם אותו חלון, אותה convention של cash/fees ודיווח exposure.
- **B — Quant:** האסטרטגיה הראשונה המוגדרת להלן, ללא LLM או ML.
- **C — Quant + AI:** יתווסף רק אחרי ש־B קפוא; אותה מערכת בדיוק עם שדה AI מאושר.
- **D — Event/news:** ייבנה רק אם נמצא feed point-in-time ותוגדר השערה נפרדת מראש.

### Baseline B — 30-minute trend/volatility allocation

1. Universe ראשוני: 10–20 ETF/מניות אמריקאיים נזילים, שנקבעו מראש עם כללי inclusion/exclusion ותאריך קיום. הרשימה היא scope ניסויי, לא המלצת השקעה.
2. כל 30 דקות, אחרי סגירת bar, חשב לכל נכס EMA קצר 20 bars, EMA ארוך 60 bars, ATR של 14 bars, תשואה של 20 bars, spread ו־dollar-volume filter.
3. BUY candidate אם EMA20 > EMA60, המחיר מעל EMA100, הנזילות וה־spread עוברים סף, ואין halt/earnings blackout שהוגדר. אחרת HOLD/EXIT לפי policy.
4. אין short. יעד משקל מחושב inverse-volatility ומנורמל בתוך gross cap; position cap ו־max positions נאכפים מחדש ב־Risk Engine.
5. אין rebalance אם השינוי קטן מ־minimum trade notional. יש cooldown לאחר fill ומקסימום holding window מוגדר. ברירת המחדל המחקרית היא 1–3 ימי מסחר; לא משנים אותה לפי final test.
6. החלטה מתקבלת רק על bar שהושלם. order simulation מתחיל לאחר latency קבועה בתרחישי sensitivity, ומשתמש ב־next available 1-minute quote/bar. אין שימוש ב־high/low עתידי כדי לאשר fill.
7. Extended hours כבוי. דיבידנדים, splits, fees, FX ו־cash treatment מדווחים במפורש.

### Backtest protocol

```text
Historical data -> validation/quality gates -> Train (אם יש ML)
-> Validation/tuning -> Freeze model/config -> untouched Test
-> Roll-forward walk-forward window -> final report
```

ב־Phase 1 ללא ML, אין train split; עדיין יש validation period לבחירת convention ו־untouched holdout להערכת סופית. Features משתמשים רק בשורות שזמינות עד `as_of`; labels אינם נכנסים ל־feature store. בכל שינוי data, cost או parameter נוצר run חדש. חלונות labels חופפים יקבלו purge/embargo כשיידרש.

### Metrics

הדוח יציג return, annualized return, volatility, Sharpe, Sortino, max drawdown, win rate, profit factor, turnover, number of trades, average holding time, gross/net exposure, slippage bps, commissions/fees, rejected/cancelled orders, latency, performance מול SPY ומול B, AI/API cost ו־net return after all costs. יוצגו גם מספרי עסקאות, אחוז הזמן ב־HOLD, תוצאות לפי נכס, חודש ו־regime, וכן confidence intervals באמצעות block bootstrap או שיטה תלויה־זמן.

אישור Phase 1 דורש reproducibility, תוצאות חיוביות אחרי cost scenarios מחמירים, יציבות בין חלונות ונכסים והיעדר תלות בתאריך יחיד. Positive return לבדו אינו gate.

## 6. Risk Engine ראשוני

הפרמטרים הם engineering defaults ל־Paper וניתנים לשינוי רק בקובץ versioned עם review; מודל או LLM אינם יכולים לכתוב אותם בזמן ריצה:

| מגבלה | ערך פתיחה ניסויי |
|---|---:|
| leverage / shorts / options | disabled |
| maximum open positions | 5 |
| single-name/ETF weight | 10% NAV |
| gross exposure | 60% NAV |
| order notional | הנמוך מבין 5% NAV ו־1% מ־20-day ADV |
| max spread | 30 bps, configurable לפי universe |
| stale quote | 60 seconds for order validation |
| daily loss response | freeze risk-increasing orders סביב 1% NAV |
| strategy drawdown response | freeze סביב 5% עד review |
| maximum portfolio volatility | לא מופעל לפני שיש estimator יציב |
| cooldown | configurable; לא משמש להעלאת סיכון |

Risk checks: account mode, session, data freshness, clock drift, symbol permission, halt, price tick, spread, liquidity, cash, pending orders, reserved shares, gross/symbol/sector exposure, daily loss, drawdown, duplicate intent and reconciliation state. `unknown` הוא reject. Freeze אינו flatten אוטומטי; emergency flatten הוא policy נפרד.

## 7. Database and logging schema

SQLite הוא store התחלתי בתהליך יחיד; PostgreSQL ייכנס רק לשירות 24/7. כל טבלה מקבלת `created_at_utc` ו־`run_id`:

| טבלה | שדות עיקריים |
|---|---|
| `runs` | run_id, git_sha, config_hash, data_version, model_version, mode, started/ended |
| `bars` / `quotes` | symbol, event_time, received_at, source, OHLCV / bid-ask, completeness |
| `features` | symbol, as_of, feature_version, values_hash, values_json |
| `signals` | action, target_weight, confidence, reason_code, model output |
| `ai_outputs` | provider/tier, prompt_hash, structured output, latency, token/cost, fallback |
| `risk_decisions` | decision_id, checks, approved/rejected, reason, limits_version |
| `orders` | intent_id, broker_order_id, permId, account_mode, side, qty, limit, state |
| `fills` | execId, order_id, fill_time, qty, price, commission, currency |
| `positions` / `portfolio_snapshots` | symbol, qty, avg cost, mark, cash, NAV, exposure |
| `alerts` / `heartbeats` | severity, component, event, acknowledged, latency, connection |

אין לשמור סיסמאות, MFA, API secrets או prompt שמכיל credentials. Reasoning נשמר כסיכום מובנה ולא כטקסט סודי מיותר.

## 8. Paper execution ו־24/7

Order Manager יהיה single writer לחשבון. לפני submit הוא עושה atomic outbox reserve; timeout הוא מצב לא ידוע שמחייב query/reconciliation לפני retry. הוא מטפל ב־partial fill, cancel/replace, rejects, duplicate events ו־disconnect. לאחר restart: account, positions, open orders ו־recent executions נסגרים ל־snapshot לפני החלטה חדשה. מצב halt נשמר עמיד.

ה־service יפעל בהמשך על IB Gateway או TWS בשרת ייעודי, עם heartbeat, reconnect, backup, alerts ו־weekly re-auth runbook. אין לפתוח את socket מחוץ ל־localhost. Paper אינו הוכחה ל־queue position או ל־live impact.

## 9. AI layer ו־A/B test

AI אינו דרוש ל־Phase 1. לאחר baseline קפוא, ה־AI יקבל רק features/events שהיו זמינים בזמן ההחלטה ויחזיר schema מוגבל: `BUY/SELL/HOLD`, confidence, horizon, reason_code ו־invalidating_conditions. ברירת מחדל לכל timeout, parse failure, hallucination או cost-budget breach היא `HOLD`.

Escalation: model זול ל־classification/summarization; tier ביניים רק אם event materiality גבוהה; tier חזק לחריגים נדירים. כל request נמדד latency/token/cost. AI אינו רשאי לשנות risk limits או לשלוח order.

AI מוסיף alpha רק אם C משפר את B באותו universe, באותם timestamps, עם אותו execution model, לאחר fees/slippage/data/API costs, במספר walk-forward windows וב־untouched holdout, עם ירידה שאינה חריגה ב־drawdown/turnover. משווים גם `B` ללא AI וגם `B + shuffled/disabled AI`; אם אין incremental value, מסירים AI.

## 10. Acceptance gates

אין מעבר ל־Paper execution לפני Phase 0 חתום. אין autonomous Paper לפני backtest deterministic שעובר data-quality ו־risk tests. אין Live לפני תקופת Paper ארוכה, zero unexplained reconciliation mismatches, zero duplicate order intents, fault injection, review אנושי ו־approval מפורש. אין gate שמבוסס רק על Sharpe, return או מספר ימי פעילות.

## 11. התאמה ל־Starter

`risk.py`, `ledger.py`, `ibkr_readonly.py`, הבדיקות וה־offline demo נשמרים. `replay.py` יישאר smoke baseline, וב־Phase 1 יתווסף event-driven multi-asset backtester לצדו. קובץ זה מגדיר את ההרחבה; הוא אינו טוען שהרכיבים החסרים כבר נבנו.
