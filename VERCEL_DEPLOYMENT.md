# Deploying ReachMe on Vercel

This repository is pre-configured for zero-friction deployment to Vercel via Python Serverless Functions.

---

## 1. Quick Deploy Steps

1. Go to [vercel.com](https://vercel.com/) and click **"Add New..."** &rarr; **"Project"**.
2. Select your GitHub repository: `ReachMe` (or `pranavramesh06/ReachMe`).
3. Under **Framework Preset**, leave it as **"Other"** (Vercel automatically detects `vercel.json` and `@vercel/python`).
4. Under **Root Directory**, keep it as `./`.

---

## 2. Configure Environment Variables

Before clicking **Deploy**, open the **Environment Variables** accordion and add the following keys:

| Key | Example Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://neondb_owner:...@...-pooler.region.neon.tech/neondb?sslmode=require` | Your Neon PostgreSQL connection string (**use the pooled connection string** with `-pooler` for optimal serverless performance). |
| `SECRET_KEY` | `reachme-production-secret-key-xyz987` | A secure random string for Flask session management. |
| `FLASK_ENV` | `production` | Sets Flask to production mode. |

---

## 3. Deployment Verification

Once deployed:
- Visit your Vercel URL (e.g., `https://reachme-xyz.vercel.app`).
- Try the **Clinical Triage** engine, **Doctor Appointment Booking**, or **Medicine Catalog**.
- Log in with the pre-seeded demo accounts:
  - **Patient**: `patient@reachme.com` / `patient123`
  - **Doctor**: `doctor@reachme.com` / `doctor123`
  - **Admin**: `admin@reachme.com` / `admin123`
