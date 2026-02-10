# 🚀 Deployment Checklist (Going Live)

Follow this checklist to deploy the Alif24 Platform to production on **Vercel**.

## 1. Pre-Deployment Checks
- [ ] **Build Check:** Run `npm run build` in `frontend/` to ensure no build errors.
- [ ] **Test Check:** Verify all critical flows (Login, Dashboard, Quiz) locally.
- [ ] **Environment Variables:** Gather all production keys (Supabase Webhook secrets, Production Azure Keys).

## 2. Database (Supabase)
- [ ] **Migrations:** Run `alembic upgrade head` to apply all schema changes.
- [ ] **Indexes:** Verify `ReadingAnalysis` and `AICache` tables have indexes on `user_id` and `prompt_hash`.
- [ ] **RLS Policies:** If Row Level Security is enabled, ensure policies allow the backend role to access all data.

## 3. Backend Deployment (Vercel)
1.  Go to Vercel Dashboard -> Add New Project -> Import from GitHub.
2.  **Root Directory:** Select `backend`.
3.  **Framework Preset:** FastAPI (or Other).
4.  **Environment Variables:** Add ALL variables from `.env`.
    *   `DATABASE_URL` (Use the Transaction Pool URL from Supabase usually port 6543)
    *   `JWT_SECRET`
    *   `AZURE_OPENAI_*`
    *   `VERCEL=1` (CRITICAL: triggers `NullPool` optimization)
5.  **Build Command:** `pip install -r requirements.txt`
6.  Click **Deploy**.

## 4. Frontend Deployment (Vercel)
1.  Go to Vercel Dashboard -> Add New Project -> Import from GitHub.
2.  **Root Directory:** Select `frontend`.
3.  **Framework Preset:** Vite.
4.  **Environment Variables:**
    *   `VITE_API_URL`: The URL of your deployed Backend (e.g., `https://alif24-backend.vercel.app/api/v1`)
5.  **Build Command:** `npm run build`
6.  Click **Deploy**.

## 5. Post-Deployment Verification
- [ ] **Login:** Try logging in as a Student and Teacher.
- [ ] **Dashboard:** Check if the Student Dashboard loads instantly (verifies unified endpoint).
- [ ] **AI Chat:** Send a message in a story. It might be slow the first time (cache miss), then fast.
- [ ] **Logs:** Check Vercel Function Logs for any `500` errors or `FATAL: too many connections`.

## 6. Maintenance (Cron Jobs)
*   **Cache Clearing:** If `AICache` grows too large, set up a cron job (GitHub Action or Vercel Cron) to delete entries older than 30 days.
    ```sql
    DELETE FROM ai_cache WHERE created_at < NOW() - INTERVAL '30 days';
    ```

**🎉 You are Live!**
