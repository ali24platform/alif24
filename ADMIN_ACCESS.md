# ALIF24 Platform — Rahbariyat Kirish Usullari va Huquqlar

## 1. Kirish Yo'llari

Platforma rahbariyati **maxfiy admin panel** orqali kiradi. Oddiy login/parol emas, balki **yashirin URL + maxfiy parol** tizimi ishlatiladi.

### Kirish URL'lari:

| Rol | URL | Lavozim | Rang |
|-----|-----|---------|------|
| **Nurali** | `/nurali` | CEO (Bosh direktor) | 💜 Binafsha |
| **Hazratqul** | `/hazratqul` | CTO (Texnik direktor) | 💙 Ko'k |
| **Pedagog** | `/pedagog` | Metodist | 💚 Yashil |

### Kirish jarayoni:
1. Brauzerda `https://alif24.uz/nurali` (yoki `/hazratqul`, `/pedagog`) sahifasiga o'ting
2. **Maxfiy parol** (passphrase) kiriting
3. Tizim `X-Secret-Token` sessiya tokenini yaratadi va `localStorage` ga saqlaydi
4. Barcha so'rovlar shu token bilan yuboriladi

> **Parol** — `ADMIN_SECRET_KEY` o'zgaruvchisida saqlanadi (`backend/app/core/config.py`)

---

## 2. Huquqlar Matritsasi

### 2.1 Maxfiy Admin Panel (`/api/v1/secret/*`)

| Endpoint | Nurali (CEO) | Hazratqul (CTO) | Pedagog (Metodist) |
|----------|:---:|:---:|:---:|
| `/secret/dashboard` — Statistika | ✅ | ✅ | ✅ |
| `/secret/users` — Foydalanuvchilar ro'yxati | ✅ | ✅ | ✅ |
| `/secret/user/{id}` — Foydalanuvchi tafsilotlari | ✅ | ✅ | ✅ |
| `/secret/search` — Smart qidiruv | ✅ | ✅ | ✅ |
| `/secret/database/tables` — DB jadvallar ro'yxati | ✅ | ✅ | ❌ |
| `/secret/database/table/{name}` — Jadval ma'lumotlari | ✅ | ✅ | ❌ |
| `/secret/activity` — Faoliyat logi | ✅ | ✅ | ✅ |

> **Pedagog** bazaga to'g'ridan-to'g'ri kira olmaydi — faqat dashboard, foydalanuvchilar va qidiruv

### 2.2 RBAC Tizimi (Asosiy Platform)

Maxfiy admin paneldan tashqari, platform `moderator` rolini ishlatadi:

| Imkoniyat | moderator | organization | teacher | parent | student |
|-----------|:---------:|:------------:|:-------:|:------:|:-------:|
| O'qituvchini tasdiqlash/rad etish | ✅ | ❌ | ❌ | ❌ | ❌ |
| Kutilayotgan o'qituvchilarni ko'rish | ✅ | ✅ | ❌ | ❌ | ❌ |
| Platform statistikasi | ✅ | ✅ | ❌ | ❌ | ❌ |
| Barcha foydalanuvchilarni ko'rish | ✅ | ✅ | ❌ | ❌ | ❌ |
| Foydalanuvchi statusini o'zgartirish | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Olimpiada yaratish** | ✅ | ❌ | ❌ | ❌ | ❌ |
| Olimpiada boshqarish (publish/start/finish) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Live Quiz yaratish | ❌ | ✅ | ✅ | ❌ | ❌ |
| Sinf yaratish / boshqarish | ❌ | ❌ | ✅ | ❌ | ❌ |
| Bola hisob yaratish | ❌ | ❌ | ❌ | ✅ | ❌ |
| O'yinlar oynash / coin yig'ish | ❌ | ❌ | ❌ | ❌ | ✅ |
| Olimpiadada qatnashish | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Rollar Tushuntirishi

### `moderator` — Platform rahbariyati
- **Nurali (CEO)**, **Hazratqul (CTO)** lar shu rolda ro'yxatdan o'tadi
- Barcha o'qituvchilarni tasdiqlash/rad etish huquqi
- Olimpiada yaratish va boshqarish
- Platform statistikasini ko'rish
- Foydalanuvchi statusini o'zgartirish (ban/unban)

### `organization` — Ta'lim tashkiloti
- Maktab yoki o'quv markazi sifatida kiradi
- O'qituvchilarni o'z tashkilotiga biriktirish
- Dars jadvali yaratish
- Kutilayotgan o'qituvchilarni ko'rish

### `teacher` — O'qituvchi
- Sinf yaratish va join code olish
- O'quvchilarni sinfga qo'shish
- TestAI orqali test yaratish
- Live Quiz o'tkazish
- Baholash va xabarlar

### `parent` — Ota-ona
- Bola hisobi yaratish (username + PIN)
- Bolaning progressini kuzatish
- Parental control (ekran vaqti, cheklovlar)
- Obuna boshqarish

### `student` — O'quvchi (Bola)
- O'yinlar oynash (MathMonster, LetterMemory, Harf, va h.k.)
- Coin yig'ish (har bir o'yindan +5 coin)
- Kunlik bonus olish (+5 coin)
- Live Quizda qatnashish
- Olimpiadada qatnashish (agar ota-ona obunasi bo'lsa)

---

## 4. Xavfsizlik Eslatmalari

1. **Maxfiy admin panel** oddiy JWT dan alohida ishlaydi — `X-Secret-Token` header orqali
2. Token in-memory saqlanadi (server restart = barcha sessiyalar tugaydi)
3. **Pedagog** roli database'ga kira olmaydi (faqat CEO va CTO)
4. O'qituvchi tasdiqlash faqat `moderator` rolida mumkin
5. Olimpiada yaratish faqat `moderator` uchun
6. `ADMIN_SECRET_KEY` — `.env` yoki `config.py` da saqlanadi

---

## 5. Tavsiya

Production'da quyidagilarni amalga oshirish kerak:
- [ ] Maxfiy parolni `.env` fayliga ko'chirish (hardcode emas)
- [ ] Token muddatini cheklash (hozir cheksiz)
- [ ] IP whitelist qo'shish (faqat ma'lum IP'lardan kirish)
- [ ] Activity log moduli ishga tushirish
- [ ] 2FA (ikki bosqichli autentifikatsiya) qo'shish
