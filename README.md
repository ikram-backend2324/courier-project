# 🚚 RouteAI - AI-Powered Courier Route Planner

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Your OpenRouter API Key
Edit `courier_project/settings.py` and replace:
```python
OPENROUTER_API_KEY = 'your-openrouter-api-key-here'
```
with your actual OpenRouter API key from https://openrouter.ai

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Admin User
```bash
python manage.py createsuperuser
```
Or use the default: **admin / admin123** (if you ran the setup script)

### 5. Run the Server
```bash
python manage.py runserver
```

### 6. Access the App
- **Client Side:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin (admin / admin123)

---

## Features

### Client Side
- 🌍 **3 Languages:** English / Russian / Uzbek (switch in top navbar)
- 🗺️ **Interactive Map:** OpenStreetMap + Leaflet.js (free, no API key)
- 📍 **Smart Location:** GPS → Manual Map Click → Admin Default (fallback chain)
- 🤖 **AI Route Optimization:** Uses OpenRouter (mistral-7b-instruct, very cheap)
- 📦 **Route Management:** Create, view, and track delivery routes

### Admin Panel (Jazzmin)
- Manage Couriers (set default starting locations)
- View all Routes and Delivery Points
- Monitor AI responses and route status

### AI Model
- Model: `mistralai/mistral-7b-instruct` (~$0.0001 per route plan)
- Responds in the selected language (EN/RU/UZ)
- Provides optimized order + reasoning + time savings estimate

---

## Courier Location Priority
1. **Browser GPS** (most accurate) - user allows location permission
2. **Map Click** - courier pins their location manually
3. **Admin Default** - pre-set warehouse/depot location

---

## Tech Stack
- Django 4.2 + SQLite
- Django Jazzmin (admin theme)
- Leaflet.js + OpenStreetMap (free maps)
- OpenRouter API (AI)
- Vanilla JS + CSS (no framework dependencies)
