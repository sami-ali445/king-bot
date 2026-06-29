# 👑 King Bot

**بوت تيليجرام احترافي لخدمات السوشيال ميديا والأرقام الوهمية**

---

## 📋 المميزات

- 📱 **أرقام وهمية** — 3 فئات سعرية ($10 / $7 / $5) عبر 5sim API
- 👥 **رشق وتفاعل** — متابعين، إعجابات، مشاهدات بنظام النقاط
- 🎯 **اكسب نقاط مجاناً** — مهام إعجابات واشتراكات قنوات
- 💰 **شحن الرصيد** — USDT عبر محفظة TRC20
- 🛠 **لوحة تحكم أدمن** — إحصائيات، إذاعة، إدارة مستخدمين

---

## 🚀 التقنيات

| الأداة | الإصدار |
|--------|---------|
| Python | 3.11.9 |
| aiogram | 3.12.0 |
| aiohttp | 3.10.5 |
| requests | 2.32.3 |
| SQLite | Built-in |

---

## ⚙️ التشغيل

### متطلبات البيئة (Environment Variables)

| المتغير | الوصف |
|---------|-------|
| `BOT_TOKEN` | توكن بوت التيليجرام |
| `FIVE_SIM_API_KEY` | مفتاح API لـ 5sim |
| `ADMIN_IDS` | أيدي الأدمنز (مفصولة بفاصلة) |
| `WEBHOOK_SECRET` | سر الـ Webhook |
| `WALLET_ADDRESS` | عنوان محفظة USDT |
| `PYTHON_VERSION` | 3.11.9 |

### أوامر البناء والتشغيل

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python main.py
```

---

## 📁 هيكل المشروع

```
king-bot/
├── main.py              # نقطة الدخول + Web server
├── config.py            # الإعدادات (من الـ env vars)
├── models.py            # قاعدة البيانات + الجداول
├── handlers/
│   ├── user.py          # أوامر المستخدمين
│   └── admin.py         # لوحة تحكم الأدمن
├── keyboards/
│   └── inline.py        # الكيبوردات
├── utils/
│   ├── fivesim.py       # تكامل 5sim API
│   └── database.py      # عمليات قاعدة البيانات
├── render.yaml          # إعدادات Render
├── requirements.txt     # المكتبات
└── data/
    └── bot.db           # قاعدة البيانات
```

---

## 🌐 النشر على Render

1. اربط الـ repo في Render كـ Web Service
2. حدد الـ Environment Variables
3. استخدم `render.yaml` للإعدادات التلقائية
4. البوت يشتغل تلقائياً بعد الـ Deploy

---

## 📞 التواصل

- المطور: @king_developer
- القناة: @king_bot_channel

---

**© 2026 King Bot — All Rights Reserved**
