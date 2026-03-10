# 📧 Solchart Email System Guide

## Overview
Your email system has a solid foundation with `email_utils.py` handling all notifications through a centralized approach. Here's the current state and how to manage it through MVP.

---

## 1️⃣ CURRENT EMAIL SYSTEM STATUS

### ✅ What's Working

#### A. **Admin Order Notifications** (`admin_order_notification.html`)
- **Trigger**: When an order is placed
- **Recipients**: All superusers + ADMIN_EMAIL setting
- **Content**: 
  - Order ID and customer details
  - Seller breakdown (items, totals, commissions)
  - Total commission amount
- **Flow**: 
  1. Order created → `process_order()` calls `send_order_notifications()` 
  2. Function groups items by seller
  3. Email sent with seller breakdown for easy processing

#### B. **Seller Order Notifications** (`seller_order_notification.html`)
- **Trigger**: When an order with seller items is placed
- **Recipients**: Individual sellers (email from `seller.email` or `seller.user.email`)
- **Content**:
  - Order ID
  - Items to fulfill (product name, quantity, price)
  - CTA: "Login to dashboard to manage fulfillment"
- **Flow**:
  1. System groups items by seller
  2. Each seller gets ONE email listing ONLY their items
  3. Plus in-app notification on dashboard

#### C. **Customer Order Confirmation** (`customer_order.html`)
- **Trigger**: When order is placed
- **Recipients**: Customer email from order
- **Content**:
  - Order ID
  - Order summary (items, quantities, prices)
  - Total amount
  - Delivery notification message
- **Flow**:
  1. Sent with order created
  2. Simple confirmation - doesn't include payment instructions yet

### ⚠️ What's Partially Implemented

#### D. **Seller Welcome Email** (`seller_welcome.html`)
- **Status**: Template exists BUT NOT BEING SENT ❌
- **Issue**: No trigger in `seller_signup()` view
- **Content**: 
  - Welcome greeting
  - Approval confirmation
  - Next steps (login, complete profile, upload products)
  - Dashboard button
- **Missing**: Link to seller dashboard, email sending code

### ❌ What's NOT Implemented Yet

#### E. **Payment Instructions Email**
- **Missing**: When order moves to "awaiting payment" status
- **Should include**: Bank account details, payment code, deadline
- **Needed for**: Customers who didn't see payment_pending.html page

#### F. **Payment Confirmation Email**
- **Missing**: When payment is verified as received
- **Should include**: Payment receipt, order moving to processing
- **Notification**: For admins and sellers

#### G. **Admin Seller Approval/Rejection**
- **Missing**: Email to seller when account approved/rejected
- **Critical for**: Seller experience, on-boarding flow

#### H. **Order Status Updates**
- **Missing**: Shipped, delivered, returned notifications
- **Needed for**: Customer satisfaction, order tracking

---

## 2️⃣ EMAIL BACKEND CONFIGURATION

### Current Setting (in `settings.py`)
```python
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@helios.example')
```

### Your Current Setup
- **Backend**: Console (prints to terminal) - **DEVELOPMENT ONLY**
- **From Email**: noreply@helios.example

### Testing Console Output
When emails are sent in development:
1. They appear in your terminal/console
2. Check your Django runserver terminal for output
3. Emails won't actually be sent to real addresses

---

## 3️⃣ MVP STAGE MANAGEMENT STRATEGY

### Phase 1: NOW (Manual MVP Phase)
**What you need to do:**

1. **For Customers**:
   - Current: Basic order confirmation email works ✅
   - **Action**: Update `customer_order.html` to include payment instructions
   - **Why**: Customers see order confirmation but don't know how to pay

2. **For Sellers**:
   - Current: Order notifications work ✅
   - **Action**: Implement seller welcome email in `seller_signup()`
   - **Why**: Sellers don't know they need approval
   - **Manual for now**: Manually approve sellers in Django admin

3. **For Admin**:
   - Current: Full order breakdown notifications ✅
   - **Action**: Create Django admin panel approval system
   - **Why**: You need to manually approve new sellers

### Phase 2: Quick Wins (First 2-4 weeks)
```
Priority 1: Fix seller welcome email
- Add send_generic_email() call to seller_signup()
- Provide login link
- Set expectations (approval pending)

Priority 2: Enhance customer confirmation
- Include payment deadline
- Add payment code if order is pending
- Include support contact info

Priority 3: Add payment verification email
- When admin manually marks payment received
- Send to seller and customer: "Order confirmed, moving to processing"
```

### Phase 3: Scheduled for Later (Once payment gateway ready)
```
- Automated payment status emails
- Webhook-based notifications
- Payment reminders (24hr before deadline)
- Failed payment alerts
```

---

## 4️⃣ HOW TO TEST EMAILS NOW

### Option A: Console Backend (Current)
```bash
# Emails print to your terminal
python manage.py runserver

# When you create an order:
# Terminal shows: "[Email] To: customer@example.com\n..."
```

### Option B: File Backend (Recommended for MVP)
If you want to see actual email files:

**Edit `.env`:**
```
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
EMAIL_FILE_PATH=./email_logs
```

**Then emails save to:** `email_logs/` folder as text files

### Option C: Gmail Backend (Production-ready, later)
When ready to send real emails:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=solchartzm@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # See Gmail App Passwords
```

---

## 5️⃣ WHAT TO IMPLEMENT NOW

### Immediate Priority 1: Fix Seller Welcome Email

**Edit `payment/views.py` - seller_signup function:**

```python
def seller_signup(request):
    if request.method == 'POST':
        form = SellerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            if hasattr(user, "seller_profile"):
                user.seller_profile.is_active = False
                user.seller_profile.save()
            
            # NEW: Send welcome email
            try:
                seller_context = {
                    'seller': user.seller_profile,
                    'login_url': request.build_absolute_uri('/seller/login/'),
                }
                send_generic_email(
                    subject='Welcome to Solchart - Account Under Review',
                    template_name='payment/emails/seller_welcome',
                    context=seller_context,
                    recipient_list=[user.email]
                )
            except Exception as e:
                print(f"Error sending seller welcome email: {e}")
            
            message.success(request, "Your seller application has been submitted successfully! We'll review it and get back to you shortly.")
            return redirect('home')
    else:
        form = SellerSignupForm()
    return render(request, 'payment/seller_signup.html', {'form': form})
```

### Immediate Priority 2: Enhance Customer Order Email

**Edit `payment/templates/payment/emails/customer_order.html`:**

```django-html
<div style="font-family:Arial,Helvetica,sans-serif">
  <h3>Order Confirmation #{{ order.id }}</h3>
  <p>Dear {{ order.full_name }},</p>
  
  <p>Thank you for your order! Here's your order summary:</p>
  <ul>
    {% for it in items %}
      <li>{{ it.product.name }} x {{ it.quantity }} @ ZMK {{ it.price }}</li>
    {% endfor %}
  </ul>
  
  <p><strong>Order Total:</strong> ZMK {{ order.amount_paid }}</p>
  
  {% if order.payment_status != 'completed' %}
  <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #0099ff;">
    <h4>⏳ Next Step: Complete Payment</h4>
    <p>Your order is confirmed but awaiting payment. Please complete payment within <strong>24 hours</strong>.</p>
    <p><strong>Payment Code:</strong> {{ payment_code }}</p>
    <p><strong>Bank Account:</strong> [Your Business Account]</p>
    <p>Full payment instructions: <a href="{{ payment_instructions_url }}">Click here to view payment page</a></p>
  </div>
  {% else %}
  <div style="background: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50;">
    <p>✅ Payment received! We're processing your order and will notify you when it ships.</p>
  </div>
  {% endif %}
  
  <p>Questions? Contact us: <a href="mailto:solchartzm@gmail.com">solchartzm@gmail.com</a></p>
</div>
```

---

## 6️⃣ EMAIL FLOW DIAGRAM

```
ORDER PLACEMENT
    ↓
process_order() → send_order_notifications()
    ↓
[Separates by recipient type]
    ├─→ ADMIN EMAIL
    │   - All superusers
    │   - ADMIN_EMAIL setting
    │   - Content: Full breakdown with commission
    │
    ├─→ SELLER EMAILS (one per seller)
    │   - seller.email or seller.user.email
    │   - Content: Only THEIR items
    │   - Plus: In-app dashboard notification
    │
    └─→ CUSTOMER EMAIL
        - order.email
        - Content: Confirmation + payment instructions
        - Status-based: Shows if payment pending/completed


SELLER SIGNUP
    ↓
seller_signup() → [MISSING: send welcome email]
    ├─→ SELLER EMAIL (should send)
    │   - Welcome message
    │   - Approval status
    │   - Login link
    │
    └─→ ADMIN IN-APP NOTIFICATION (manually review)
        - New seller pending approval
```

---

## 7️⃣ SETTINGS CONFIGURATION CHECKLIST

Your `settings.py` already has good bones. Here's what you have:

```python
# ✅ Email backend (development-friendly)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ✅ From address (set in .env)
DEFAULT_FROM_EMAIL = 'noreply@helios.example'

# ✅ Admin setting (used in send_order_notifications)
ADMIN_EMAIL = 'admin@example.com'  # Add your actual email

# ✅ Business email (for support links)
BUSINESS_CONTACT_EMAIL = 'solchartzm@gmail.com'
```

**Update your `.env`:**
```env
ADMIN_EMAIL=patrick@solchart.com  # Your email for order notifications
DEFAULT_FROM_EMAIL=orders@solchart.com  # Domain-based sender
```

---

## 8️⃣ MVP TO PRODUCTION ROADMAP

### Month 1-2: MVP Manual Phase
- ✅ Customer order confirmations (currently working)
- ✅ Admin gets all orders
- ✅ Sellers get their items
- ⚠️ Seller welcome email (FIX NOW)
- 🔧 Manual payment verification (you mark as paid in admin)
- 🔧 Manual seller approval (you approve in admin)

### Month 3: Improve MVP
- Add payment status change emails
- Add seller account approval/rejection emails
- Add order status update emails (shipped, delivered)
- Upgrade to Gmail SMTP backend

### Month 4+: Payment Gateway Integration
- When you integrate Stripe/Flutterwave/etc:
  - Remove manual payment verification
  - Add automated payment success emails
  - Add webhook handlers for payment events
  - Remove payment code system
  - Remove manual bank account showing

### Production Ready:
- Email template versioning system
- Email logs database for compliance
- Unsubscribe mechanisms
- Email retry logic
- Template variable validation

---

## 9️⃣ QUICK REFERENCE: Email Templates

| Template | When Sent | To | Status |
|----------|-----------|-----|--------|
| admin_order_notification | Order placed | All admins | ✅ Working |
| seller_order_notification | Order placed | Each seller | ✅ Working |
| customer_order | Order placed | Customer | ✅ Working but needs enhancement |
| seller_welcome | Seller signup | New seller | ❌ Template exists, no trigger |
| seller_approval | Admin approves | Seller | ❌ Missing |
| payment_confirmation | Payment received | Customer + seller | ❌ Missing |
| order_shipped | Marked shipped | Customer | ❌ Missing |
| order_delivered | Marked delivered | Customer | ❌ Missing |

---

## 🔟 TROUBLESHOOTING

### "I don't see any emails"
1. Check `EMAIL_BACKEND` in settings - should be `console` for development
2. Check your terminal where Django runs
3. Look for `[Email]` output in console

### "Sellers not getting emails"
1. Verify `seller.email` or `seller.user.email` is populated
2. Check logs in `email_utils.py` - look for exceptions
3. Test with console backend first to see if it tries to send

### "Admin not getting emails"
1. Set `ADMIN_EMAIL` in `.env`
2. Verify superuser accounts exist with email addresses
3. Check `logger.info()` output for delivery confirmation

---

## 📋 ACTION ITEMS FOR TODAY

- [ ] Add seller welcome email trigger to `seller_signup()`
- [ ] Enhance customer_order.html with payment instructions
- [ ] Create `EMAIL_SYSTEM_GUIDE.md` (this file) for reference
- [ ] Set `ADMIN_EMAIL` in your `.env` to receive notifications
- [ ] Test by creating a test order and checking terminal output
- [ ] Document any missing pieces you discover

---

## Need Help?

Key files to reference:
- `payment/email_utils.py` - Core email logic
- `payment/templates/payment/emails/` - Email HTML templates
- `payment/views.py` - Where emails are triggered
- `ecom/settings.py` - Email backend configuration
