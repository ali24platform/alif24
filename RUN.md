# 🚀 ALIF24 Platform - Ishga Tushirish

## Tez Boshlash

### 1. Backend Server
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Server
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/frontend"
npm run dev -- --port 5173
```

---

## 📍 URL'lar

| Xizmat | URL |
|--------|-----|
| 🌐 Frontend | http://localhost:5173 |
| 🔧 Backend API | http://localhost:8000 |
| 📚 API Docs | http://localhost:8000/docs |

---

## ⚙️ Ilk Marta O'rnatish

### Backend Dependencies
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend"
pip install -r requirements.txt
```

### Frontend Dependencies
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/frontend"
npm install
```

### Database Migration
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend"
python3 -m alembic upgrade head
```

---

## 🔄 Bitta Komanda Bilan Ishga Tushirish

### Variant 1: Alohida terminal oynalarida
Terminal 1 (Backend):
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend" && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 (Frontend):
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/frontend" && npm run dev
```

---

## 🛠 Foydali Buyruqlar

### Backend loglarni ko'rish
```bash
tail -f "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend/backend.log"
```

### Database tozalash va qayta yaratish
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend"
python3 cleanup_partial_migration.py
python3 -m alembic upgrade head
```

### Yangi migration yaratish
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend"
python3 -m alembic revision --autogenerate -m "migration_nomi"
```

---

## 🔐 Environment Variables

Backend `.env` fayli (`/backend/.env`):
```env
DATABASE_URL=sqlite:///./alif24.db
JWT_SECRET=your-secret-key
CORS_ORIGINS=*
TELEGRAM_BOT_TOKEN=your-bot-token
OPENAI_API_KEY=your-openai-key
```

---

## ❗ Muammolar Yechimi

### Port band bo'lsa
```bash
# 8000 portni tozalash
lsof -ti:8000 | xargs kill -9

# 5173 portni tozalash  
lsof -ti:5173 | xargs kill -9
```

### ModuleNotFoundError
```bash
cd "/Users/hazratqul/Documents/alif24-platform_ready1 (1)/backend"
pip install emails jinja2
```
