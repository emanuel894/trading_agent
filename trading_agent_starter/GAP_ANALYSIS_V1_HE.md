# Gap Analysis — Trading Agent V1 מול ה־Starter הקיים

עודכן: 14 בספטמבר 2026. הבדיקה מתייחסת ל־Trading Agent Starter 0.1 שנבנה קודם ול־Project Brief הנוכחי.

## מסקנה

ה־Starter מתאים כ־**Foundation**: הוא מספק בדיקות מקומיות, סימולטור קטן, בדיקות סיכון, יומן SQLite ובדיקת חיבור לקריאה בלבד ל־IBKR. הוא אינו עדיין Trading Agent V1 ואינו Paper Trader אוטונומי. אין צורך לזרוק אותו או לבנות מחדש את רכיבי היסוד; צריך להרחיב סביבם במודולי data, backtest, journal ו־execution.

## מה נשאר כמו שהוא

| רכיב קיים | התאמה לבריף | החלטה |
|---|---|---|
| Python והפרדה בין risk, ledger ו־broker adapter | תואם לארכיטקטורה | לשמר |
| `risk.py` כפונקציה דטרמיניסטית | בסיס נכון ל־veto חיצוני | לשמר ולהרחיב לכיסוי תיק, פקודות ממתינות, נזילות ולוח מסחר |
| `ledger.py` עם SQLite, מזהה intent ו־halt שנשמר אחרי restart | בסיס טוב ל־idempotency ול־kill latch | לשמר; לחבר ל־outbox ול־order lifecycle |
| `ibkr_readonly.py` | מאמת חשבון Paper מדויק ללא שליחת פקודות | לשמר כשלב חיבור ראשון; לא להפוך אותו למנוע execution |
| חסימת Live ports ו־account allowlist | הגנה חשובה בתחילת הפרויקט | לשמר ולבדוק ב־integration tests |
| בדיקות stale/future data, חשיפה, duplicate intent, restart ו־fills מדומים | תואם לדרישות safety | לשמר ולהוסיף בדיקות broker fault ו־time controls |
| אין LLM ואין נתיב order ישיר | תואם לעקרון הארכיטקטוני | לשמר; AI יתווסף מאוחר יותר מאחורי חוזה מובנה |
| ה־Windows setup והדגמה offline | טוב להתחלה מבוקרת | לשמר; להוסיף בדיקת SDK וחיבור Paper מפורשת |

## מה צריך לשנות או להוסיף

| פער | מצב ב־Starter | שינוי נדרש |
|---|---|---|
| Horizon | הדגמה על נרות יומיים | לעבור למחקר על 30-minute signals עם 1-minute/quote execution data; לשמור daily כבדיקת smoke בלבד |
| Universe | נכס יחיד, דוגמת SPY | 10–20 נכסים נזילים, universe קבוע ו־point-in-time, מגבלת מספר פוזיציות |
| Baseline | כלל moving average פשוט, קנייה בלבד | baseline רב־נכסי מוגדר מראש עם signal, sizing, turnover ו־holding period של שעות/ימים |
| Backtest | replay ליניארי מינימלי | event-driven engine עם זמני event/receive/decision/order, fills, partial fills, latency, fees, spread ו־slippage |
| Metrics | return בסיסי ו־drawdown | כל מדדי הבריף: annualized return, Sharpe, Sortino, MDD, win rate, profit factor, turnover, holding time, trades, slippage, fees, risk-adjusted, יחס ל־SPY, AI/API cost ו־net return |
| Baseline matrix | אין השוואת A–D | לבנות A Passive, B Quant ללא AI, C אותו Quant עם AI, D Event/news רק אם יוגדר אות שניתן לבדוק point-in-time |
| Data quality | CSV יומי או נתוני broker לפי צורך | data manifest, corporate actions, delisted/universe policy, quotes, trading calendar, timezone ו־availability timestamp |
| Database | ledger ו־JSON reports בלבד | SQLite בתחילת המחקר עם schema מלא; PostgreSQL רק כשיש שירות 24/7 וריבוי תהליכים |
| Paper execution | אין `placeOrder` בכוונה | Order Manager נפרד, single writer, durable outbox, broker order state, fills, reconciliation ו־retry/query לפני retry |
| Risk | בדיקת order בודד | portfolio risk, pending exposure, reserved cash/shares, ADV/spread/volatility, max positions, loss limits ו־market-hours |
| AI | אין AI | רק אחרי baseline: structured event extraction / classifier / veto feature, עם escalation לפי עלות ו־fallback HOLD |
| 24/7 | אין service supervisor, alerts או heartbeat | worker, health checks, reconnect, weekly re-auth runbook, alerting, backups ו־operator reset |
| Validation | בדיקות יחידה בלבד | walk-forward, final holdout, synthetic fault injection ו־Paper integration tests. אין להשתמש ב־test לשיפור הפרמטרים |

## פערים שאינם באגים

היעדר מנוע פקודות והיעדר מודל AI הם גבולות מכוונים של Foundation 0.1. כך נשמרת הפרדה בין אימות חיבור בטוח לבין הרשאת ביצוע. גם ההדגמה הסינתטית אינה תוצאה פיננסית, ולכן אין להמיר את המספרים שלה למדד הצלחה.

## סדר ההרחבה שאושר

1. חיבור Paper לקריאה בלבד ואימות הרשאות.
2. Phase 0: נעילת specification, data contract, universe, baseline ו־acceptance gates.
3. Phase 1: multi-asset event-driven backtest ללא AI.
4. Paper order manager עם risk gate ו־reconciliation.
5. AI רק בניסוי A/B מבודד, עם מדידת עלות ותועלת.

ה־Starter נשאר בסיס הקוד; השלב הבא אינו rewrite אלא הוספת מודולים סביבו.
