# 🚀 DEPLOYMENT CHECKLIST - First App Launch

## Pre-Deployment (Local Setup)

### ✅ 1. Update Requirements
- [x] Added `gunicorn` to requirements.txt
- **Why**: Production server that Railway uses to run Django. Without it, your app won't start on Railway.

### ✅ 2. Create Procfile
- [x] Created `Procfile` with:
  ```
  web: gunicorn ecom.wsgi --log-file -
  release: python manage.py migrate
  ```
- **Why**: Tells Railway exactly how to start your app and when to run database migrations

### ✅ 3. Verify Static Files Collection
- [ ] Run locally: `python manage.py collectstatic --noinput`
- **Why**: Gathers all CSS, JS, images into a single folder that Railway can serve efficiently

### ✅ 4. Test Migrations Locally
- [ ] Run: `python manage.py migrate --run-syncdb`
- **Why**: Ensures your database schema works before deploying. If this fails locally, it'll fail on Railway too.

### ✅ 5. Verify Settings.py for Production
- [x] `DEBUG = False` (controlled by env vars)
- [x] `SECURE_SSL_REDIRECT = not DEBUG` (auto-enables in production)
- [x] `SESSION_COOKIE_SECURE = not DEBUG` (auto-enables in production)
- [x] `CSRF_COOKIE_SECURE = not DEBUG` (auto-enables in production)
- [ ] Review `ALLOWED_HOSTS` configuration
- **Why**: These prevent security vulnerabilities in production (SSL/HTTPS, CSRF attacks, session hijacking)

---

## Railway Setup

### ✅ 6. Create Railway Project with PostgreSQL
- [ ] Go to [railway.app](https://railway.app)
- [ ] Create new project → "Provision PostgreSQL"
- [ ] This auto-creates `DATABASE_URL` env variable
- **Why**: PostgreSQL is production-grade, SQLite is for local dev only. Railway auto-injects the connection URL.

### ✅ 7. Connect Your GitHub Repository
- [ ] Push your code to GitHub (`backend/ecom` folder)
- [ ] In Railway → Connect GitHub repo
- [ ] Select branch to deploy (usually `main`)
- **Why**: Enables automatic deployments when you push code changes

### ✅ 8. Set Environment Variables on Railway
In Railway dashboard → Variables tab, add:
- [ ] `SECRET_KEY` = Generate a strong random key (use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- [ ] `DEBUG` = `False`
- [ ] `DJANGO_DEBUG` = `False`
- [ ] `ALLOWED_HOSTS` = `yourdomain.up.railway.app` (Railway will provide the exact domain)
- [ ] `SECURE_SSL_REDIRECT` = `True`
- [ ] `ADMIN_EMAIL` = Your email
- [ ] `DEFAULT_FROM_EMAIL` = noreply@yourdomain.com (or update later)
- *Optional email vars if you plan to send emails*

- **Why**: 
  - `SECRET_KEY` prevents session/token hacking (NEVER use the dev key in production)
  - `DEBUG=False` disables error pages that expose code (security)
  - `ALLOWED_HOSTS` prevents Host Header attacks
  - SSL redirect forces HTTPS (encrypts user data)

---

## Pre-Launch Testing

### ✅ 9. Test Production Build Locally
- [ ] Set env vars locally to simulate production:
  ```bash
  $env:DEBUG = "False"
  $env:DJANGO_DEBUG = "False"
  $env:ALLOWED_HOSTS = "127.0.0.1"
  python manage.py collectstatic --noinput
  gunicorn ecom.wsgi
  ```
- [ ] Visit `http://127.0.0.1:8000` and verify it works
- **Why**: Catches most production issues before they go live

### ✅ 10. Create Superuser on Railway
- [ ] After first deploy, run: `railway run python manage.py createsuperuser`
- **Why**: You need a superuser account to access `/admin`

---

## Deployment

### ✅ 11. Trigger Initial Deploy
- [ ] Push your code to GitHub (or Railway will auto-deploy if connected)
- [ ] Watch Railway logs for any errors
- [ ] Check that `release: python manage.py migrate` completes successfully
- **Why**: Initial deploy runs migrations to set up the database schema

### ✅ 12. Verify Production Site
- [ ] Visit your Railway domain (Railway will show you the URL)
- [ ] Test core functionality:
  - [ ] Homepage loads
  - [ ] Can browse products
  - [ ] Admin login works at `/admin`
  - [ ] Orders dashboard loads
  - [ ] Can submit a form (contact, order, etc.)
- **Why**: Make sure nothing broke during deployment

---

## Post-Launch Monitoring

### ✅ 13. Monitor Logs
- [ ] Check Railway logs regularly for errors
- [ ] Set up email alerts if Railway offers them
- **Why**: Catch bugs early before customers encounter them

### ✅ 14. Set Up SSL Certificate (Usually Auto)
- [ ] Railway provides free SSL via Let's Encrypt (automatic)
- [ ] Verify your site has a 🔒 lock icon in browser
- **Why**: Encrypts user data in transit (required for safety)

### ✅ 15. Backup Your Database
- [ ] Enable PostgreSQL backups in Railway (if available in your tier)
- [ ] Consider weekly exports
- **Why**: You don't want to lose customer orders and product data

---

## Important Notes

### ⚠️ Debug Errors
If something fails:
1. Check Railway logs first: `railway run python manage.py migrate --plan` (preview migrations)
2. Check `ALLOWED_HOSTS` - most 404 errors are caused by this
3. Check `SECRET_KEY` is set
4. Check `DATABASE_URL` is populated (Railway should set this auto)

### 📝 First Deploy Timeline
- Build: 2-5 minutes (collecting static files, etc.)
- Migrations: 30 seconds - 2 minutes
- Total: Usually ready in ~5 minutes

### 🔄 Future Deployments
Just push to GitHub → Railway auto-deploys → migrations run automatically → Done!

---

## Your Current Status

✅ requirements.txt - Updated with gunicorn
✅ Procfile - Created
✅ settings.py - Already configured for Railway
⏳ Next: Set up Railway PostgreSQL + deploy

**Ready to go to the next step?** Let me know when you've set up Railway!
