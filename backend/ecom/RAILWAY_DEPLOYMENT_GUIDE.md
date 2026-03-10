# 🚀 Solchart Railway Deployment Guide

## Project Status
✅ **Ready for Production** - All features complete, security measures in place, tested and working

---

## 📋 Pre-Deployment Checklist

### 1. Local Testing (BEFORE pushing to Railway)
- [ ] Run `python manage.py runserver` locally and test all key features:
  - [ ] Product browsing and search
  - [ ] User registration and login
  - [ ] Quote request submission (test full confirmation flow)
  - [ ] Adding products to cart and checkout
  - [ ] Admin dashboard access
- [ ] Run migrations locally: `python manage.py migrate`
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Test email sending (quote confirmations, order confirmations)

### 2. Git Preparation
```bash
# Make sure all changes are committed
git status

# Create a new branch for deployment if preferred
git checkout -b production

# Or just commit to main
git add .
git commit -m "Final deployment preparation for Solchart"
git push origin main  # or your branch
```

### 3. Environment Variables to Set in Railway
Copy these from `.env.example` and set actual values in Railway dashboard:

**Critical (MUST SET):**
```
DJANGO_DEBUG=False                          # IMPORTANT: Must be False in production
SECRET_KEY=<generate-a-secure-key>          # Generate via `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://...               # Railway will provide this
```

**Email Configuration (CRITICAL for quote/order confirmations):**
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com        # Gmail account for sending emails
EMAIL_HOST_PASSWORD=your-app-password       # Gmail App Password (NOT regular password!)
DEFAULT_FROM_EMAIL=noreply@solchart.example
ADMIN_EMAIL=admin@example.com
BUSINESS_CONTACT_EMAIL=contact@solchart.com
```

**Business Settings:**
```
BROTHER_PHONE_NUMBER=+260977XXXXXX          # Phone for manual payment collection
BROTHER_NAME=Solchart Zambia (Founder)
```

**Optional (If using AWS S3 for media):**
```
USE_S3=True
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_STORAGE_BUCKET_NAME=<bucket-name>
```

---

## 🚢 Railway Deployment Steps

### Step 1: Connect Repository to Railway
1. Go to [railway.app](https://railway.app)
2. Create new project → Import from GitHub
3. Select your Solchart repository
4. Railway will auto-detect Django project

### Step 2: Configure Railway Services

#### Database Service
- Railway should auto-provision PostgreSQL
- Set `DATABASE_URL` environment variable (Railway does this automatically)

#### Web Service
1. Click "Settings" → Deployment
2. Set Start Command:
   ```bash
   python manage.py migrate && python manage.py collectstatic --noinput && gunicorn ecom.wsgi
   ```
3. Set Runtime:
   - Python version: 3.12 or latest
   - Memory: 512MB (should be fine for MVP)

3. Variables: Add all env variables from checklist above

#### Domain Setup
1. Go to Deployments → Custom Domain
2. Add your domain (e.g., solchart.com, www.solchart.com)
3. Update DNS records with provided CNAME

### Step 3: Run Migrations
After first deployment, connect to Railway terminal:
```bash
railway run python manage.py migrate
```

---

## ⚙️ Production Settings Already Configured

✅ **HTTPS Enforcement:**
```python
SECURE_SSL_REDIRECT = not DEBUG        # Enabled automatically in production
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000         # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

✅ **Security Features Already Implemented:**
- Quote request confirmation page (prevents accidental submissions)
- Customer & admin email confirmations
- PDF export for quotes
- CSRF protection
- SQL injection prevention
- XSS protection

---

## 📧 Email Setup (IMPORTANT!)

### Using Gmail (Recommended for MVP)
1. Enable 2-Factor Authentication on your Gmail account
2. Generate "App Password" (NOT your regular Gmail password):
   - Go to: myaccount.google.com → Security → App passwords
   - Select Mail + Windows Computer
   - Copy the 16-character password
3. Use this password in `EMAIL_HOST_PASSWORD`

### Alternative: SendGrid (More Reliable)
1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Create API key
3. Set:
   ```
   EMAIL_BACKEND=sendgrid_backend.SendgridBackend
   SENDGRID_API_KEY=SG.xxxxx
   ```

---

## 🔍 Post-Deployment Testing Checklist

After deployment to Railway:

1. **Check Website is Live**
   - [ ] Visit your domain (should be HTTPS)
   - [ ] Test home page loads
   - [ ] Check products page

2. **Test Key Features**
   - [ ] Create new user account
   - [ ] Submit quote request (should get confirmation email)
   - [ ] Check admin can see quote (Django admin)
   - [ ] Add product to cart
   - [ ] Complete checkout flow
   - [ ] Check order confirmation email received

3. **Monitor Logs**
   - Railway → Logs → Check for errors
   - Look for 404s, 500s, email errors
   - Database connection should show success

4. **Database**
   - [ ] Data persists after reload
   - [ ] Users can log back in
   - [ ] Quotes/orders are saved

---

## 🐛 Common Issues & Fixes

### Issue: 500 Error on Website
**Cause:** Missing environment variables
**Fix:** Check Railway logs → Add missing env vars → Redeploy

### Issue: Email Not Sending
**Cause:** Incorrect email credentials or Gmail app password not used
**Fix:** 
1. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in Railway
2. If using Gmail, ensure App Password is set (not regular password)
3. Check Railway logs for SMTP errors

### Issue: Static Files Not Loading (CSS/Images broken)
**Cause:** Collectstatic didn't run
**Fix:** 
1. Check Procfile/Start Command runs `collectstatic`
2. Manually run: `railway run python manage.py collectstatic --noinput`
3. Check STATIC_URL and STATIC_ROOT in settings.py

### Issue: Database Migration Errors
**Cause:** Migrations not run on Railway
**Fix:** `railway run python manage.py migrate`

### Issue: Custom Domain Not Working
**Cause:** DNS not updated or CNAME wrong
**Fix:** Check CNAME matches Railway's value, wait 24hrs for DNS propagation

---

## 🔐 Security Reminders

1. **NEVER commit .env file** - It's in .gitignore, keep it that way
2. **SECRET_KEY is unique** - Generate new one for production
3. **HTTPS enforced** - Settings automatically enforce it when DEBUG=False
4. **Database backups** - Railway auto-backs up PostgreSQL daily
5. **Email credentials** - Store securely in Railway dashboard, not in code

---

## 📱 First Customer Order Process

When you get your first real order:

1. **Customer submits order** → Redirected to payment_pending page
2. **Customer receives payment instructions** (showing payment code)
3. **Customer sends payment** via Brother's phone number (manual for MVP)
4. **You verify payment** in Django admin:
   - Go to Orders → Find order
   - Check payment_reference matches receipt
   - Mark as shipped when ready
5. **Customer gets shipping notification** via email

---

## 🔄 Monitoring & Maintenance

### Daily Tasks
- Check emails are being sent (look at order confirmations)
- Spot-check Django admin for new orders/quotes
- Review error logs in Railway

### Weekly Tasks
- Backup important order data
- Test quote request flow with test customer
- Monitor server performance (CPU, memory in Railway)

### Monthly Tasks
- Review quote requests and follow up
- Archive old orders
- Test payment flow end-to-end

---

## 📈 Performance Tips

- **Images:** Keep under 500KB, use JPEG for product photos
- **Database queries:** Already optimized in views
- **Static files:** Railway serves via CDN automatically
- **Email:** Use async tasks for high volume (future improvement)

---

## 🆘 Support & Troubleshooting

### Railway Documentation
- [Django Deployment](https://docs.railway.app/guides/django)
- [PostgreSQL Setup](https://docs.railway.app/databases/postgresql)
- [Custom Domains](https://docs.railway.app/networking/custom-domains)

### Django Docs
- [Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Email Configuration](https://docs.djangoproject.com/en/5.2/topics/email/)

### Local Troubleshooting
```bash
# Check migrations
python manage.py showmigrations

# Run specific migration
python manage.py migrate payment 0026

# Check static files
python manage.py collectstatic --dry-run

# Test email
python manage.py shell
from django.core.mail import send_mail
send_mail('Test', 'This is a test', 'from@email.com', ['to@email.com'])
```

---

## ✅ Deployment Status

| Component | Status | Notes |
|-----------|--------|-------|
| Django 5.2 | ✅ Ready | All features tested |
| PostgreSQL | ✅ Ready | Railway auto-provisions |
| Static Files | ✅ Ready | Collectstatic configured |
| Media Files | ✅ Ready | Stored in /media (or S3) |
| Email | ⏳ Needs Setup | Gmail credentials required |
| Quotes | ✅ Ready | Confirmation flow working |
| Orders | ✅ Ready | Payment pending flow ready |
| Sellers | ✅ Ready | Signup and dashboard working |
| PDF Export | ✅ Ready | ReportLab configured |
| HTTPS | ✅ Ready | Auto-enforced in production |

---

## 🎉 You're Ready to Launch!

Once you've:
1. ✅ Set all environment variables in Railway
2. ✅ Deployed the code
3. ✅ Run migrations
4. ✅ Tested key features
5. ✅ Set up custom domain

**Solchart is LIVE!** 🚀

Good luck with your launch! Remember: you can always iterate and improve after going live. Start with the MVP features, get real customer feedback, then enhance.
