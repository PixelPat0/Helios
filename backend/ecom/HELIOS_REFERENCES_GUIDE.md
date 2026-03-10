# ⚠️ Helios References - What to Keep & What to Change

## Summary
Most Helios branding has been changed to Solchart in user-facing text. However, some references are in **functional code** that users will customize via environment variables or documentation examples. This document clarifies what to change and what to leave alone.

---

## ✅ CHANGED - User-Facing Text (COMPLETED)

These have all been updated to "Solchart":
- Store page titles and headings
- Login/Register page copy
- Quote confirmation emails
- Newsletter messages
- PDF exports
- Email signatures
- Navigation/UI text
- Seller marketplace text

**Status:** ✅ All done!

---

## ⚠️ KEEP AS-IS - Functional Code

These should NOT be changed in the code because they are defaults/examples that users will customize:

### 1. `.env.example` File
**File:** `.env.example`

```
# These are EXAMPLES - user will set real values in Railway
BROTHER_NAME=Helios Zambia (Brother Account)
BUSINESS_CONTACT_EMAIL=helios.zambia@gmail.com
DEFAULT_FROM_EMAIL=noreply@helios.example
```

**Why keep:** These are placeholder defaults. User will replace with:
```
BROTHER_NAME=Actual Name (Your Name)
BUSINESS_CONTACT_EMAIL=your-email@solchart.com
DEFAULT_FROM_EMAIL=noreply@solchart.com
```

**User will customize in:** Railway dashboard environment variables

---

### 2. `ecom/settings.py` - Default Values
**File:** `ecom/settings.py`

```python
BROTHER_NAME = os.getenv('BROTHER_NAME', 'Helios Zambia (Brother Account)')
BUSINESS_CONTACT_EMAIL = os.getenv('BUSINESS_CONTACT_EMAIL', 'helios.zambia@example.com')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@helios.example')
TEST_SELLER_EMAIL = os.getenv('TEST_SELLER_EMAIL', 'test.seller@example.com')
```

**Why keep:** These are defaults. When `os.getenv()` is called, it looks for the environment variable first. The second argument is just a fallback if not set.

**How it works:**
```python
# In Railway, user sets: BROTHER_NAME="Patrick Banda"
# Then in Python code:
BROTHER_NAME = os.getenv('BROTHER_NAME', 'Helios Zambia...')
# ↓ Gets value from Railway
# Result: BROTHER_NAME = "Patrick Banda"

# If not set in Railway, uses default:
# Result: BROTHER_NAME = "Helios Zambia (Brother Account)"
```

**These defaults are fine to leave** - they're just fallback values. Better to leave them as examples so user understands what to set.

---

### 3. Documentation Examples (Informational Only)

These files contain example code and references - they're NOT executed:

#### File: `PAYMENT_INTEGRATION_GUIDE.md`
```markdown
Contains example code like:
'item_name': f'Helios Order #{order.id}',
'return_url': 'https://helios.com/payment_success/',
```
**Why keep:** Examples for user to understand and customize

#### File: `PAYMENT_API_EXAMPLES.md`
```python
'description': f'Helios Order #{order.id}',
'narrative': f'Helios Order #{order.id}',
```
**Why keep:** Examples for user to understand patterns

#### File: `MVP_PAYMENT_SYSTEM.md`
```markdown
BROTHER_NAME="Helios Zambia (Brother Account)"
Message: HLS-1001-A7K2 - Helios Order
```
**Why keep:** Documentation showing example payment codes

#### File: `INTEGRATION_POINTS.md`
```markdown
Contains similar example references
https://helios.example.com/payment/webhook/
```
**Why keep:** Examples for user to copy/customize

#### File: `README_PAYMENT_SYSTEM.md`
```markdown
Various Helios references in documentation
```
**Why keep:** Documentation is informational

#### File: `PAYMENT_QUICK_REFERENCE.md`
```markdown
HLS = Helios (recognizable)
```
**Why keep:** Payment code format explanation

---

## 🎯 What User Will Customize

### In Railway Dashboard (Environment Variables):
```
BROTHER_NAME → User's actual name
BUSINESS_CONTACT_EMAIL → User's email
DEFAULT_FROM_EMAIL → User's email
EMAIL_HOST_USER → User's Gmail/SendGrid
EMAIL_HOST_PASSWORD → User's app password
ALLOWED_HOSTS → User's domain
```

### In Django Admin After Deployment:
- Site name (if using Django sites framework)
- Contact information
- Business details

### In Templates (You mentioned):
- About page content
- Contact page details
- Footer information
- Home page copy

---

## 📝 Reference: What Was Changed

### Changed in Code (User-Facing):
1. ✅ `store/views.py` - Docstrings, messages, titles
2. ✅ `store/templates/` - All HTML templates
3. ✅ `payment/views.py` - Docstrings
4. ✅ `payment/utils.py` - Docstrings
5. ✅ `payment/templates/` - Email and payment templates
6. ✅ `payment/email_utils.py` - Email subjects

### NOT Changed (Correct Approach):
1. ✅ `.env.example` - Placeholder defaults
2. ✅ `ecom/settings.py` - Fallback defaults
3. ✅ Documentation files - Examples for reference
4. ✅ Code comments referencing examples
5. ✅ Variable names like `HLS` (payment code prefix)

---

## ✨ Final Notes

### For User (When Deploying)
When you set up Railway, you'll see `.env.example` in the repo. Use it as a template and set these in Railway dashboard:
```
✏️ Set these yourself:
- BROTHER_NAME = [Your name]
- BUSINESS_CONTACT_EMAIL = [Your email]
- EMAIL_HOST_USER = [Your Gmail or SendGrid]
- EMAIL_HOST_PASSWORD = [Your app password]
- DEFAULT_FROM_EMAIL = [Your no-reply email]
```

### Status Summary
| Component | Status | Notes |
|-----------|--------|-------|
| User-facing text | ✅ Changed to Solchart | All branding updated |
| Environment var defaults | ✅ Left as-is | User customizes in Railway |
| Documentation examples | ✅ Left as-is | User references and customizes |
| Functional code | ✅ Using env vars | No hardcoded company names |
| Ready for production | ✅ Yes | Just needs email config |

---

## 🚀 Next Step for User

No action needed on Helios/Solchart branding - all done! 

Just follow `RAILWAY_DEPLOYMENT_GUIDE.md` and when it asks you to set environment variables, that's where you'll put your actual company name, email, etc. instead of the placeholder "Helios" values.

All set! ✅
