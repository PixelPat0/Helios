from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Load .env once
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-please-change')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# HTTPS/SSL Settings (enforce in production)
# Only enforce HTTPS when not in DEBUG mode (i.e., in production)
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # 1 year in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Additional Security Headers
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking by denying framing in iframes
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "code.jquery.com"),
    'style-src': ("'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"),
    'img-src': ("'self'", "data:", "https:"),
    'font-src': ("'self'", "fonts.gstatic.com", "cdn.jsdelivr.net"),
    'connect-src': ("'self'",),
    'object-src': ("'none'",),
    'frame-ancestors': ("'none'",),
} if not DEBUG else {}

SECURE_BROWSER_XSS_FILTER = True  # Enable browser XSS protection header
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'  # Control referrer information

# ALLOWED_HOSTS: read comma-separated env var; when empty default to localhost for local dev only.
_raw_allowed = os.getenv('ALLOWED_HOSTS', '')
if _raw_allowed:
    ALLOWED_HOSTS = [h.strip() for h in _raw_allowed.split(',') if h.strip()]
else:
    # safe local default so runserver works when DEBUG=True; in production set ALLOWED_HOSTS env var
    ALLOWED_HOSTS = ['localhost', '127.0.0.1'] if DEBUG else []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'store',
    'cart',
    'payment',
    'crispy_forms',
    'crispy_bootstrap4',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecom.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart',
                'ecom.context_processors.newsletter_form',
                'ecom.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecom.wsgi.application'

# DATABASE
# Prefer DATABASE_URL (Railway) when present, otherwise use local sqlite for dev.
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('RAILWAY_DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = ['static/']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email (env-driven)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@helios.example')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
TEST_SELLER_EMAIL = os.getenv('TEST_SELLER_EMAIL', 'test.seller@example.com')

# ============================================================================
# TEMPORARY MVP PAYMENT SYSTEM SETTINGS
# ============================================================================
# WARNING: This is a temporary manual payment system for MVP phase.
# FUTURE IMPROVEMENTS:
# 1. Integrate with proper payment gateway (Stripe, Flutterwave, PayPal, etc.)
# 2. Implement automated payment verification and webhook handling
# 3. Remove manual bank account details and use API-driven payment processing
# 4. Add PCI compliance and secure payment tokenization
# 5. Implement real-time payment status updates
# 6. Add automated email notifications on payment success/failure
#
# WHEN READY TO UPGRADE:
# - Remove BUSINESS_ACCOUNT_NAME and BUSINESS_BANK_ACCOUNT settings
# - Replace payment_pending.html with payment gateway integration
# - Update payment/views.py to handle webhook callbacks
# - Implement payment.models.Payment for tracking transactions
# - Add payment retry logic and reconciliation
# ============================================================================

# Business account details for temporary manual payment system
BUSINESS_ACCOUNT_NAME = os.getenv('BUSINESS_ACCOUNT_NAME', 'Solchart (Zambia) Ltd')
BUSINESS_BANK_ACCOUNT = os.getenv('BUSINESS_BANK_ACCOUNT', 'XXXXX-XXXXX-XXXXX')  # Update with actual bank account
BUSINESS_CONTACT_EMAIL = os.getenv('BUSINESS_CONTACT_EMAIL', 'solchartzm@gmail.com')

# Payment system configuration
# TODO: Replace these with actual payment gateway credentials when upgrading
# PAYMENT_GATEWAY = 'stripe'  # or 'flutterwave', 'paypal', etc.
# STRIPE_API_KEY = os.getenv('STRIPE_API_KEY', '')
# STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')

CRISPY_TEMPLATE_PACK = 'bootstrap4'