# Alpaca Paper — Foundation 0.2

המטרה בשלב זה היא לבדוק את תשתית הסוכן מול Alpaca Paper בלבד, בלי כסף אמיתי ובלי נתיב Live.

## מה נוסף

- `agent/broker.py` — חוזה BrokerAdapter כללי לקריאה בלבד.
- `agent/alpaca_paper.py` — Adapter ל-Alpaca Paper עם `paper=True` כפוי.
- `python -m agent alpaca-probe` — בדיקת account/clock/positions/open orders/quotes ללא שליחת פקודות.
- `.env.example` — תבנית secrets מקומית.
- `.gitignore` — חסימת `.env`, קובצי local config ו-runtime state.
- `tests/test_alpaca_paper.py` — בדיקות שמוודאות ש-Live/Trading flags נחסמים וש-probe נשאר read-only.

## התקנה

ב-Windows מתוך `trading_agent_starter`:

```bat
setup_windows.bat
```

הסקריפט יוצר `.venv`, מתקין `requirements.txt`, יוצר `.env` מקומי מהתבנית ומריץ את הבדיקות.

## הגדרת Alpaca Paper

ערכו רק את הקובץ המקומי `.env`:

```env
BROKER=alpaca
ALPACA_PAPER=true
ALPACA_API_KEY=YOUR_PAPER_KEY
ALPACA_API_SECRET=YOUR_PAPER_SECRET
ALPACA_DATA_FEED=iex
TRADING_ENABLED=false
ALLOW_PAPER_ORDERS=false
ALPACA_LIVE_TRADE=false
```

אין להעלות `.env` ל-GitHub ואין לשלוח API keys בצ'אט.

## בדיקת החיבור

```bat
.venv\Scripts\python.exe -m agent alpaca-probe --symbols SPY,QQQ
```

תוצאה תקינה כוללת:

```text
READ_ONLY_CHECK_PASSED
```

הפקודה קוראת מצב חשבון, clock, מספר פוזיציות, מספר פקודות פתוחות ו-latest quotes ל-SPY/QQQ. היא אינה יוצרת, מבטלת או משנה פקודות.

## גבול השלב

Foundation 0.2 עדיין לא מבצע Paper orders. השלב הבא לאחר connection probe מוצלח הוא:

1. market-data contract ל-30-minute bars / 1-minute execution context;
2. journal/schema רב-נכסי;
3. baseline Quant קפוא;
4. Paper Order Manager מאחורי Risk Engine;
5. רק אחר כך ניסוי A/B: Quant-only מול Quant+AI;
6. לאחר בסיס מדיד, בניית שכבת multi-agent עם תפקידים נפרדים.

אין מעבר ל-Live ואין הרשאת order ל-LLM בשלב זה.
