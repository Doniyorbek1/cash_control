finance_productivity_bot/
│
├── config/                  # Sozlamalar va muhit o'zgaruvchilari
│   ├── __init__.py
│   └── config.py
│
├── database/                # Ma'lumotlar bazasi va ORM modellar
│   ├── __init__.py
│   ├── base.py              # Async SQLAlchemy session
│   └── models.py            # User, Category, Transaction, Reminder, Task modellar
│
├── handlers/                # Bot komandalari va menyular
│   ├── __init__.py
│   ├── start.py             # Start va asosiy menyu
│   ├── finance.py           # Kirim/Chiqim, Hisobotlar logikasi
│   ├── categories.py        # Kategoriya qo'shish va sozlamalar
│   ├── reminders.py         # Aqlli eslatmalar logikasi
│   └── tasks.py             # To-Do list logikasi
│
├── keyboards/               # Tugmalar (Inline va Reply)
│   ├── __init__.py
│   ├── default_kb.py
│   └── inline_kb.py
│
├── middlewares/             # Foydalanuvchini bazaga avto-ro'yxatdan o'tkazish
│   ├── __init__.py
│   └── db_middleware.py
│
├── services/                # Qo'shimcha servislar
│   ├── __init__.py
│   ├── scheduler.py         # APScheduler (eslatmalar uchun)
│   └── reports.py           # Grafik va Excel hisobot yaratish
│
├── utils/                   # Yordamchi funksiyalar va steytlar (States)
│   ├── __init__.py
│   └── states.py
│
├── .env                     # BOT_TOKEN va DATABASE_URL saqlash uchun
├── requirements.txt         # Kutubxonalar ro'yxati
└── main.py                  # Botni ishga tushirish fayli