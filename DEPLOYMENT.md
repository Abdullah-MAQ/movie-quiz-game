# 🎮 Engage Quest Bot - Movie Quiz Game

A full-stack movie quiz application with AI-generated questions powered by Google Gemini API.

## 🚀 Quick Deploy Guide

### Frontend Deployment Options

#### Option 1: Vercel (Recommended)
1. Fork this repository
2. Connect to [Vercel](https://vercel.com)
3. Import your repository
4. Set environment variable: `VITE_API_BASE_URL=https://your-backend-url.railway.app/api`
5. Deploy!

#### Option 2: Netlify
1. Fork this repository
2. Connect to [Netlify](https://netlify.com)
3. Build command: `npm run build`
4. Publish directory: `dist`
5. Set environment variable: `VITE_API_BASE_URL=https://your-backend-url.railway.app/api`

### Backend Deployment Options

#### Option 1: Railway (Recommended)
1. Fork this repository
2. Connect to [Railway](https://railway.app)
3. Create new project from GitHub repo
4. Select the `backend` folder as root
5. Set environment variables:
   - `GOOGLE_API_KEY=your_google_gemini_api_key`
   - `PORT=5000` (Railway sets this automatically)
6. Deploy!

#### Option 2: Render
1. Fork this repository
2. Connect to [Render](https://render.com)
3. Create new Web Service
4. Select your repository
5. Set build command: `pip install -r backend/requirements.txt`
6. Set start command: `cd backend && gunicorn -b 0.0.0.0:$PORT app:app`
7. Set environment variables:
   - `GOOGLE_API_KEY=your_google_gemini_api_key`

## 🔧 Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.8+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Local Development

#### Frontend Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

#### Backend Setup
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your_api_key_here"

# Start server
python app.py
```

## 🌐 Free Hosting Services Used

| Service | Type | Free Tier | Best For |
|---------|------|-----------|----------|
| **Vercel** | Frontend | Unlimited | React/Next.js apps |
| **Netlify** | Frontend | 100GB bandwidth | Static sites |
| **Railway** | Backend | $5 credit/month | Python apps |
| **Render** | Backend | 750 hours/month | Web services |

## 🔑 Environment Variables

### Frontend (.env.local)
```env
VITE_API_BASE_URL=https://your-backend-url.railway.app/api
```

### Backend (.env)
```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
FLASK_ENV=production
PORT=5000
```

## 📁 Project Structure
```
├── src/                    # Frontend React app
├── backend/               # Flask API server
├── public/               # Static assets
├── vercel.json          # Vercel config
├── netlify.toml         # Netlify config
└── render.yaml         # Render config
```

## 🎯 Features
- 🤖 AI-generated movie questions using Google Gemini
- 🎭 Genre-based question filtering
- ⏱️ Real-time quiz timer
- 🏆 Leaderboard system
- 👤 User profiles with statistics
- 📱 Responsive design

## 🔧 Tech Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: Flask, Python
- **AI**: Google Gemini API
- **Data**: Pandas, CSV dataset
- **UI**: Shadcn/ui components

## 📝 Deployment Steps Summary

1. **Get API Key**: Obtain Google Gemini API key
2. **Fork Repository**: Fork this repo to your GitHub
3. **Deploy Backend**: 
   - Railway: Connect repo → Set GOOGLE_API_KEY → Deploy
   - Render: Connect repo → Set build/start commands → Set env vars
4. **Deploy Frontend**:
   - Vercel: Connect repo → Set VITE_API_BASE_URL → Deploy
   - Netlify: Connect repo → Set build settings → Set env vars
5. **Update CORS**: Ensure backend CORS allows your frontend domain

## 🚀 Production Ready
- ✅ Environment variables configured
- ✅ Production build optimized
- ✅ CORS properly configured
- ✅ Gunicorn for production server
- ✅ Error handling implemented

## 📚 API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/quiz/start` - Start new quiz
- `POST /api/quiz/answer` - Submit answer
- `GET /api/leaderboard` - Get leaderboard
- `GET /api/profile/{user_id}` - Get user profile

Happy quizzing! 🎬✨