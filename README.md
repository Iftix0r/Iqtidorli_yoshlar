# ⚡ Iqtidorli Yoshlar — Milliy Iqtidorlar Platformasi

**Iqtidorli Yoshlar** — bu mamlakatimizdagi yosh iste'dodlarni aniqlash, ularni tizimli ravishda monitoring qilish va qo'llab-quvvatlash uchun yaratilgan zamonaviy ekotizim. Platforma iqtidorli yoshlar, mentorlar va investorlarni bitta maydonda birlashtiradi.

---

## 🌟 Asosiy Imkoniyatlar

### 🧑‍🎓 Iqtidorlar uchun:
*   **Shaxsiy Profil:** O'z ko'nikmalari, yutuqlari va loyihalarini namoyish etish portfoliosi.
*   **Leaderboard (Reyting):** Ballar tizimi asosida respublika miqyosidagi reytingda qatnashish.
*   **Onlayn Ta'lim:** Maxsus kurslarda qatnashish va rasmiy sertifikatlarga ega bo'lish.
*   **Tanlovlar:** Grantlar, stipendiyalar va qimmatbaho sovg'alar uchun tanlovlarda ishtirok etish.

### 👨‍🏫 Mentor va Investorlar uchun:
*   **Iqtidorlarni qidirish:** Hududlar va ko'nikmalar bo'yicha eng sara yoshlarni topish.
*   **Vakansiyalar:** Eng yaxshi nomzodlarga ish taklif qilish yoki loyihalariga investitsiya kiritish.

---

## 🛡️ Xavfsizlik (Security Architecture)
Loyiha "Defense in Depth" (Chuqur Mudofaa) strategiyasi asosida himoyalangan:
*   **2FA (Telegram):** Har bir kirish urinishi Telegram orqali 2-bosqichli tekshiruvdan o'tadi.
*   **DDoS Himoya:** IP-manzillar bo'yicha aqlli cheklovlar va avtomatik bloklash tizimi.
*   **Encryption at Rest:** Shaxsiy ma'lumotlar AES-128 algoritmi orqali shifrlangan holatda saqlanadi.
*   **Audit Trail:** Foydalanuvchilarning har bir harakati (IP, qurilma bilan) monitoring qilinadi.
*   **HSTS & CSP:** Brauzer darajasidagi barcha zamonaviy xavfsizlik protokollari (Content Security Policy) yoqilgan.

---

## ⚙️ Tizim Boshqaruvi (System Panel)
Adminlar uchun quyidagi vositalar integratsiya qilingan:
*   **Real-time Monitoring:** Server yuklamasi, xotira va xizmatlar holati (Nginx, Postgres, Redis).
*   **Git Integration:** Versiyalarni boshqarish va serverda terminalsiz yangilash.
*   **Backup System:** Ma'lumotlar bazasidan avtomatik va qo'lda zaxira nusxa (SQL Dump) olish.
*   **Error Tracking:** Tizimdagi barcha xatoliklar (500 errors) visual loglarda ko'rsatiladi.

---

## 🚀 Texnologik Stek
*   **Backend:** Python 3.11, Django 5.x
*   **Frontend:** Vanilla JS, CSS3, Lucide Icons, Chart.js
*   **Database:** PostgreSQL / SQLite
*   **Server:** Ubuntu/Linux (Eskiz.uz/cPanel)
*   **Cache:** LocMem / Redis

---

## 🛠️ O'rnatish tartibi
1. Repozitoriyani klonlash: `git clone https://github.com/Iftix0r/Iqtidorli_yoshlar.git`
2. Virtual muhitni yoqish: `python -m venv venv && source venv/bin/activate`
3. Kutubxonalarni o'rnatish: `pip install -r requirements.txt`
4. Migratsiyalarni amalga oshirish: `python manage.py migrate`
5. `.env` faylini sozlash (SECRET_KEY, DB_SETTINGS).
6. Serverni ishga tushirish: `python manage.py runserver`

---
© 2026 Iqtidorli Yoshlar loyihasi. O'zbekistonning kelajagi bo'lgan iqtidorlar uchun yaratilgan.
