# מדריך ממש פשוט — איך להפעיל את Trading Agent עם Alpaca Paper

המדריך הזה מיועד למי שלא עובד ביום־יום עם Git, Python או שורת פקודה.

המטרה כרגע: רק לוודא שהמחשב שלך מצליח להתחבר ל־Alpaca Paper ולקרוא חשבון ונתוני שוק. אין מסחר אמיתי ואין שליחת פקודות.

---

## לפני שמתחילים

צריך שיהיו לך:

1. מחשב Windows.
2. חשבון Alpaca Paper פתוח.
3. Paper API Key ו־Secret Key של Alpaca.
4. אינטרנט.

אל תשלחי את ה־API Key או ה־Secret לאף אחד ואל תעלי צילום מסך שמציג אותם.

---

# חלק א — הורדת הגרסה הנכונה מ־GitHub

אנחנו עובדים כרגע על branch בשם:

`feat/alpaca-paper-foundation`

## הדרך הקלה בלי Git

1. היכנסי לריפו:
   `emanuel894/trading_agent`
2. בחלק העליון של רשימת הקבצים לחצי על הכפתור שבו כתוב `main`.
3. בחרי מהרשימה:
   `feat/alpaca-paper-foundation`
4. לחצי על הכפתור הירוק `Code`.
5. לחצי `Download ZIP`.
6. שמרי את קובץ ה־ZIP בתיקיית Downloads.
7. לחצי על הקובץ עם הכפתור הימני ובחרי `Extract All...`.
8. מומלץ להעביר את התיקייה שחולצה אל:
   `C:\TradingAgent`

בסוף את אמורה לראות בערך:

`C:\TradingAgent\trading_agent_starter`

---

# חלק ב — התקנת Python

1. היכנסי ל־python.org.
2. הורידי Python 3.13 ל־Windows 64-bit.
3. פתחי את קובץ ההתקנה.
4. חשוב מאוד: סמני את האפשרות `Add Python to PATH` אם היא מופיעה.
5. השלימי את ההתקנה.

כדי לבדוק שהכול תקין:

1. לחצי על Start.
2. כתבי `cmd`.
3. פתחי `Command Prompt`.
4. כתבי:

```bat
py -3.13 --version
```

אם מופיע מספר גרסה של Python 3.13 — הכול תקין.

---

# חלק ג — הרצת ההתקנה של הפרויקט

1. פתחי File Explorer.
2. היכנסי ל:
   `C:\TradingAgent\trading_agent_starter`
3. מצאי את הקובץ:
   `setup_windows.bat`
4. לחצי עליו פעמיים.
5. ייפתח חלון שחור.
6. תני לו לסיים.

הקובץ יבצע לבד:

- יצירת סביבת Python מקומית `.venv`
- התקנת Alpaca SDK
- התקנת python-dotenv
- יצירת קובץ `.env` מקומי
- הרצת כל הבדיקות

בסוף אמורה להופיע הודעה שמתחילה ב־`Setup complete`.

אם החלון נסגר או מופיעה שגיאה — צלמי רק את טקסט השגיאה. אין לצלם API keys.

---

# חלק ד — הכנסת מפתחות Alpaca Paper

בתיקייה:

`C:\TradingAgent\trading_agent_starter`

אמור להיות עכשיו קובץ בשם:

`.env`

אם אינך רואה אותו:

1. ב־File Explorer לחצי `View`.
2. הפעילי `Show hidden files` אם צריך.

## פתיחת הקובץ

1. לחצי על `.env` עם הכפתור הימני.
2. בחרי `Open with`.
3. בחרי Notepad.

את אמורה לראות:

```env
BROKER=alpaca
ALPACA_PAPER=true
ALPACA_API_KEY=PASTE_PAPER_KEY_HERE
ALPACA_API_SECRET=PASTE_PAPER_SECRET_HERE
ALPACA_DATA_FEED=iex

TRADING_ENABLED=false
ALLOW_PAPER_ORDERS=false
ALPACA_LIVE_TRADE=false
```

החליפי רק את שתי השורות:

```env
ALPACA_API_KEY=...
ALPACA_API_SECRET=...
```

במפתחות שקיבלת מ־Alpaca Paper.

אל תשני כרגע את שלוש השורות הבאות:

```env
TRADING_ENABLED=false
ALLOW_PAPER_ORDERS=false
ALPACA_LIVE_TRADE=false
```

שמרי את הקובץ וסגרי את Notepad.

---

# חלק ה — בדיקת החיבור

1. היכנסי שוב לתיקייה:
   `C:\TradingAgent\trading_agent_starter`
2. לחצי בשורת הכתובת של File Explorer.
3. כתבי:
   `cmd`
4. לחצי Enter.

ייפתח Command Prompt כבר בתוך התיקייה הנכונה.

העתיקי והדביקי את הפקודה הבאה:

```bat
.venv\Scripts\python.exe -m agent alpaca-probe --symbols SPY,QQQ
```

ולחצי Enter.

## הצלחה

אם הכול עובד, אמורה להופיע תוצאה שכוללת:

```text
READ_ONLY_CHECK_PASSED
```

וגם מידע כמו:

- broker: alpaca
- mode: paper-read-only
- market_is_open
- positions_count
- open_orders_count
- quotes עבור SPY ו־QQQ

המערכת לא שולחת שום פקודת קנייה או מכירה בשלב הזה.

---

# מה לשלוח חזרה לצ'אט

אם הצליח, שלחי רק:

```text
READ_ONLY_CHECK_PASSED
```

אפשר גם לצרף את שאר הפלט, אבל לפני כן בדקי שאין בו מפתח API או Secret.

אם יש שגיאה, שלחי את טקסט השגיאה בלבד.

---

# מה קורה אחרי שהבדיקה עוברת

לאחר חיבור מוצלח, סדר העבודה יהיה:

1. Market Data ל־30 דקות.
2. Journal רב־נכסי.
3. Quant baseline.
4. Paper Order Manager מאחורי Risk Engine.
5. בדיקת Quant-only מול Quant+AI.
6. בניית 6 Agents עם תפקידים נפרדים.
7. Orchestrator שמנהל את ששת ה־Agents.
8. רק בהמשך — Paper Trading אוטונומי מלא.

לא עוברים לכסף אמיתי בשלב הזה.
