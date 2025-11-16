# Deployment Guide

This guide will help you deploy the PharmaMiku project for demonstration purposes.

## Quick Deployment Options

### Option 1: Vercel (Frontend) + Railway (Backend) - Recommended for Demo

This is the fastest way to get both services deployed.

---

## Frontend Deployment (Vercel)

### Prerequisites
- GitHub account
- Vercel account (free tier works)

### Steps

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Configure:
     - **Framework Preset**: Next.js
     - **Root Directory**: `frontend`
     - **Build Command**: `npm run build` (auto-detected)
     - **Output Directory**: `.next` (auto-detected)

3. **Set Environment Variables**:
   - In Vercel project settings → Environment Variables
   - Add: `NEXT_PUBLIC_BACKEND_URL` = `https://your-backend-url.railway.app` (or your backend URL)
   - Redeploy after adding the variable

4. **Deploy**:
   - Click "Deploy"
   - Wait for build to complete
   - Your frontend will be live at `https://your-project.vercel.app`

---

## Backend Deployment (Railway)

### Prerequisites
- Railway account (free tier available)
- GitHub account

### Steps

1. **Prepare Backend for Deployment**:
   - Ensure `requirements.txt` exists in the `backend/` directory
   - Create a `Procfile` or `railway.json` for Railway

2. **Deploy to Railway**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python

3. **Configure Settings**:
   - **Root Directory**: Set to `backend`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Railway will auto-detect the port from `$PORT` environment variable

4. **Set Environment Variables**:
   - In Railway project settings → Variables
   - Add all required variables from your `.env` file:
     - `OPENAI_API_KEY` (or your LLM API key)
     - `DEBUG_TRACE` (optional, set to `false` for production)
     - Any other API keys or configuration

5. **Deploy**:
   - Railway will automatically build and deploy
   - Get your backend URL from Railway dashboard (e.g., `https://your-app.railway.app`)

6. **Update Frontend**:
   - Go back to Vercel
   - Update `NEXT_PUBLIC_BACKEND_URL` to your Railway backend URL
   - Redeploy frontend

---

## Alternative: Render (Both Services)

### Frontend on Render

1. Go to [render.com](https://render.com)
2. Create new "Static Site"
3. Connect GitHub repo
4. Set:
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/.next`
   - **Environment Variable**: `NEXT_PUBLIC_BACKEND_URL` = your backend URL

### Backend on Render

1. Create new "Web Service"
2. Connect GitHub repo
3. Set:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Add environment variables

---

## Environment Variables Checklist

### Backend (Railway/Render)
- `OPENAI_API_KEY` (or your LLM provider key)
- `DEBUG_TRACE` (optional)
- Any other API keys your backend needs

### Frontend (Vercel/Render)
- `NEXT_PUBLIC_BACKEND_URL` = Your deployed backend URL (e.g., `https://your-backend.railway.app`)

---

## Post-Deployment Checklist

- [ ] Backend is accessible (test `/health` endpoint if you have one)
- [ ] Frontend can connect to backend (check browser console for errors)
- [ ] CORS is configured correctly (backend allows frontend origin)
- [ ] Environment variables are set correctly
- [ ] Test a chat message to ensure end-to-end works

---

## Troubleshooting

### CORS Errors
If you see CORS errors, update `backend/server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],  # Add your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Build Failures
- Check that all dependencies are in `requirements.txt`
- Ensure Python version is compatible (3.11+)
- Check build logs for specific errors

### Frontend Can't Connect to Backend
- Verify `NEXT_PUBLIC_BACKEND_URL` is set correctly
- Ensure backend URL doesn't have trailing slash
- Check that backend is running and accessible

---

## Quick Demo Setup (5 minutes)

1. **Backend (Railway)**:
   - Deploy backend first
   - Copy the Railway URL

2. **Frontend (Vercel)**:
   - Deploy frontend
   - Set `NEXT_PUBLIC_BACKEND_URL` to Railway URL
   - Redeploy

3. **Test**:
   - Open your Vercel URL
   - Send a test message
   - Verify it works!

---

## Cost

- **Vercel**: Free tier (hobby plan) is sufficient for demos
- **Railway**: Free tier includes $5/month credit (enough for demo)
- **Render**: Free tier available (with limitations)

---

## Notes

- For production, consider:
  - Custom domains
  - SSL certificates (usually auto-provided)
  - Database persistence (if needed)
  - Monitoring and logging
  - Rate limiting

---

## Support

If you encounter issues:
1. Check build logs in your deployment platform
2. Verify environment variables are set
3. Test backend endpoints directly (using curl or Postman)
4. Check browser console for frontend errors

