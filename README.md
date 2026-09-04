# Centralia Tours — Backend API

Sayohat agentligi sayti uchun **FastAPI** backend. Frontend (React/Next.js va h.k.) shu API bilan ishlaydi.

## Texnologiyalar
- **FastAPI** — REST API
- **PostgreSQL + SQLAlchemy 2.0** — ma'lumotlar bazasi
- **Alembic** — migratsiyalar
- **JWT (python-jose)** — autentifikatsiya (access + refresh token)
- **Pydantic v2** — validatsiya
- **Payme / Click** — O'zbekiston to'lov tizimlari integratsiyasi

## Ko'p tillilik (uz / ru / en)
Har bir matn maydoni (title, description...) bazada JSON ko'rinishida saqlanadi:
```json
{"uz": "Samarqand", "ru": "Самарканд", "en": "Samarkand"}
```
API so'rovga `?lang=uz` (yoki `ru`, `en`) qo'shilsa — javobda faqat shu tildagi matn qaytadi.
Agar `lang` berilmasa — barcha tillar bilan to'liq obyekt qaytadi (admin panel uchun qulay).

Masalan:
```
GET /api/v1/tours?lang=ru
GET /api/v1/tours/samarkand-2-day-trip?lang=en
```

## Ma'lumotlar bazasi: Supabase (PostgreSQL)
Loyiha [Supabase](https://supabase.com) taqdim etadigan bepul PostgreSQL bazasidan foydalanadi.
Ikkita alohida URL kerak bo'ladi (Supabase "Connect" oynasidan olinadi):

- **`DATABASE_URL`** — transaction pooler (port `6543`, `?pgbouncer=true`). Bu server ish vaqtida
  (uvicorn) ishlatiladi — ko'p parallel so'rovlarni samarali boshqaradi.
- **`DIRECT_URL`** — session pooler yoki to'g'ridan-to'g'ri ulanish (port `5432`). Bu FAQAT
  Alembic migratsiyalari uchun ishlatiladi, chunki `CREATE TABLE` kabi DDL buyruqlari
  transaction-mode pgbouncer orqali ishonchli ishlamasligi mumkin.

`.env` faylida ikkalasini ham to'ldiring — kod avtomatik ravishda to'g'ri URL'ni tanlaydi.

## Deploy qilish (internetga chiqarish)

Frontend jamoasi backendga masofadan ulanishi uchun uni bepul hosting'ga joylashtirish tavsiya etiladi: **Render.com**.

1. Loyihani GitHub'ga yuklang (yangi repository yarating, kodlarni push qiling)
2. https://render.com da ro'yxatdan o'ting (GitHub bilan kirsa bo'ladi)
3. "New +" → "Web Service" → GitHub repongizni tanlang
4. Sozlamalar:
   - **Build Command:** `pip install -r requirements.txt && alembic upgrade head`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3
5. "Environment Variables" bo'limida `.env` faylingizdagi barcha qiymatlarni birma-bir qo'shing (`SECRET_KEY`, `DATABASE_URL`, `DIRECT_URL`, `STRIPE_SECRET_KEY` va h.k.)
6. "Create Web Service" tugmasini bosing — bir necha daqiqadan keyin sizga `https://centralia-backend.onrender.com` kabi ommaviy manzil beriladi
7. `BACKEND_CORS_ORIGINS` environment variable'ga frontend domenini qo'shishni unutmang
8. Shu yangi manzilni frontend jamoasiga bering — ular endi `https://centralia-backend.onrender.com/api/v1` orqali ulanadi

> **Eslatma:** Render bepul tarifida server 15 daqiqa foydalanilmasa "uxlab qoladi" va keyingi so'rovda ~30 soniya sekin ochiladi. Bu development bosqichida muammo emas, lekin production uchun pullik tarifga o'tish tavsiya etiladi.

## O'rnatish (lokal)

```bash
# 1. Virtual muhit
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. .env faylini sozlash
cp .env.example .env
# .env ichida DATABASE_URL va DIRECT_URL (Supabase'dan olingan) hamda SECRET_KEY,
# PAYME_*, CLICK_* qiymatlarni to'ldiring

# 4. Supabase loyihasi allaqachon PostgreSQL bazasini o'zi bilan beradi - alohida yaratish shart emas

# 5. Migratsiyalarni yaratish va qo'llash (DIRECT_URL orqali ishlaydi)
alembic revision --autogenerate -m "init"
alembic upgrade head

# 6. (ixtiyoriy) Demo ma'lumotlar
python -m app.seed

# 7. Serverni ishga tushirish (DATABASE_URL - pgbouncer pooler orqali)
uvicorn app.main:app --reload
```

Server ishga tushgach:
- API: http://localhost:8000/api/v1
- Swagger docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Asosiy endpointlar

| Metod | Yo'l | Tavsif |
|---|---|---|
| POST | `/api/v1/auth/register` | Ro'yxatdan o'tish |
| POST | `/api/v1/auth/login` | Kirish (access + refresh token) |
| POST | `/api/v1/auth/refresh` | Tokenni yangilash |
| GET | `/api/v1/auth/me` | Joriy foydalanuvchi |
| GET | `/api/v1/countries` | Davlatlar ro'yxati |
| GET | `/api/v1/destinations` | Yo'nalishlar |
| GET | `/api/v1/tours` | Turlar ro'yxati (filtr: country, destination, category, min_price, max_price, search) |
| GET | `/api/v1/tours/{slug}` | Tur tafsilotlari |
| POST | `/api/v1/tours` | Tur qo'shish (admin) |
| POST | `/api/v1/bookings` | Buyurtma yaratish (mehmon yoki login qilingan) |
| GET | `/api/v1/bookings/my` | Mening buyurtmalarim |
| GET | `/api/v1/bookings` | Barcha buyurtmalar (admin) |
| POST | `/api/v1/payments/init` | To'lov linkini olish (Payme/Click/Stripe) |
| POST | `/api/v1/payments/payme/webhook` | Payme JSON-RPC webhook |
| POST | `/api/v1/payments/click/prepare` | Click Prepare webhook |
| POST | `/api/v1/payments/click/complete` | Click Complete webhook |
| POST | `/api/v1/payments/stripe/webhook` | Stripe webhook |
| GET | `/api/v1/reviews` | Sharhlar |
| GET | `/api/v1/blogs` | Blog maqolalari |

## Loyiha strukturasi

```
app/
  core/        - config, database, security (JWT), i18n util
  models/      - SQLAlchemy modellari
  schemas/     - Pydantic sxemalar (request/response)
  crud/        - bazaga murojaat qiluvchi funksiyalar
  services/    - Payme va Click integratsiya logikasi
  api/v1/      - endpointlar (routerlar)
  main.py      - FastAPI ilova kirish nuqtasi
alembic/       - DB migratsiyalar
```

## To'lov integratsiyasi haqide eslatma
`app/services/payme.py`, `app/services/click.py` va `app/services/stripe_service.py` —
ishlaydigan integratsiya skeletlari (merchant kabinetdan olinadigan kalitlarni `.env`ga
qo'yish kifoya).

- **Payme / Click** — O'zbekiston ichidagi kartalar (Uzcard/Humo), summa **UZS**da bo'ladi.
- **Stripe** — xalqaro Visa/Mastercard/Amex kartalar uchun (chet ellik sayyohlar), summa
  odatda **USD**da bo'lishi kerak (Stripe UZS'ni qo'llab-quvvatlamaydi). Kalitlarni
  https://dashboard.stripe.com/apikeys dan oling. Webhook sozlash uchun Stripe CLI orqali
  lokalda test qilish mumkin: `stripe listen --forward-to localhost:8000/api/v1/payments/stripe/webhook`

Productionga chiqarishdan oldin **Payme sandbox**, **Click test muhiti** va **Stripe test mode**da
to'liq test qiling — ayniqsa xatolik kodlari va summa validatsiyasini.

## Yangi migratsiya kerak
`SiteStats` jadvalidan `satisfaction_percent`, `completed_trips`, `happy_travelers` ustunlari
OLIB TASHLANDI (endi jonli hisoblanadi, saqlanmaydi) — faqat `years_experience` qoladi.
Quyidagini ishga tushiring:
```bash
alembic revision --autogenerate -m "site stats: auto-calculate trips, travelers, satisfaction"
alembic upgrade head
```

## Keyingi qadamlar (tavsiya)
- Admin panelga fayl yuklash uchun S3/local storage endpointi qo'shish
- Email/SMS orqali booking tasdiqlash xabarnomasi (masalan Celery + Redis bilan fon vazifa)
- Rate limiting (masalan `slowapi`) — public endpointlar uchun
- Testlar: `pytest` + `httpx.AsyncClient`
"# silkora" 
