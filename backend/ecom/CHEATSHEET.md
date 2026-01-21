# Payment System - 1-Page Cheat Sheet

## Admin: Process an Order (30 seconds)

```
1. Get payment notification from customer
2. Go to: /admin/payment/order/
3. Search for: "HLS-1001" or order ID "1001"
4. Click order to open
5. Look for "MVP Payment Tracking" section
6. Verify payment_code field matches what customer sent
7. Verify amount matches
8. Scroll down, select order checkbox
9. Choose action: "✓ Confirm Payment Received"
10. Click "Go"
11. DONE! Order marked as paid, email sent to customer
```

## Order Lifecycle

```
pending
  ↓ [You confirm payment]
paid
  ↓ [You click "Mark as Processing"]
processing
  ↓ [You pack items and ship]
shipped
  ↓ [Customer confirms delivery]
delivered
```

## Payment Code Format

```
HLS-1001-A7K2

HLS       = Helios
1001      = Order ID
A7K2      = Random (for uniqueness)
```

## Customer Instruction Format

**Customer sees:**
```
Order #1001
Total: K50,000
Payment Code: HLS-1001-A7K2

Send to: Helios Zambia (Brother Account)
Phone: +260977123456
Message: HLS-1001-A7K2
```

## Admin Actions (One-Click)

| Action | Shortcut | What It Does |
|--------|----------|--------------|
| ✓ Confirm Payment Received | Pending → Paid | Order paid, email sent |
| → Mark as Processing | Paid → Processing | Start fulfillment |
| 📦 Mark as Shipped | Processing → Shipped | Package sent, email sent |

## Search Tips

```
By Order ID:        "1001"
By Payment Code:    "HLS-1001"
By Customer Name:   "Patrick"
By Email:           "customer@example.com"
```

## Key Fields to Check

```
order.id              → 1001
order.payment_code    → HLS-1001-A7K2
order.amount_paid     → 50000
order.status          → pending/paid/processing/shipped
order.payment_method  → airtel/mtn/zamtel
order.date_ordered    → When created
order.date_paid       → When you confirmed
```

## Settings Needed (in .env)

```
BROTHER_PHONE_NUMBER=+260977123456
BROTHER_NAME=Helios Zambia (Brother Account)
BUSINESS_CONTACT_EMAIL=helios.zambia@gmail.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Order not found | Use search feature (HLS-1001) |
| Payment code empty | Click Save on order, it will generate |
| Email not sending | Check EMAIL_BACKEND in .env |
| Can't confirm payment | Check order status (must be pending) |
| Amount doesn't match | Customer sent wrong amount |

## Payment Code Generation (Automatic)

```
When: Order is created
Code format: HLS-{ID}-{3CHARS}
Example: HLS-1001-A7K2
Unique: Yes (can't have duplicates)
Manual entry: NOT NEEDED (auto-generated)
```

## Workflow (Copy This)

```
STEP 1: Receive Payment Alert
└─ Customer paid K50,000 with message "HLS-1001-A7K2"

STEP 2: Verify in Admin
└─ Go to /admin/payment/order/
└─ Search "HLS-1001"
└─ Click order
└─ Check: payment_code matches, amount matches

STEP 3: Confirm Payment (One Click)
└─ Select checkbox
└─ Action: "✓ Confirm Payment Received"
└─ Click "Go"
└─ Email automatically sent to customer

STEP 4: Prepare Order
└─ Select order
└─ Action: "→ Mark as Processing"
└─ Click "Go"
└─ Start packing items

STEP 5: Ship Order
└─ Select order
└─ Action: "📦 Mark as Shipped"
└─ Click "Go"
└─ Shipping email sent to customer

STEP 6: Done!
└─ Order complete
└─ Customer has proof of purchase
└─ You have audit trail
```

## Email Notifications (Automatic)

| Event | Customer Gets |
|-------|----------------|
| Order Created | Confirmation + payment instructions |
| Payment Confirmed | "Your payment was verified" |
| Order Shipped | "Package is on its way" |
| Order Delivered | "Delivery confirmed" |

## Dates Tracked (Automatic)

```
date_ordered        → When you click "Confirm Payment Received"
date_paid           → Recorded automatically
date_processed      → When you click "Mark as Processing"
date_shipped        → When you click "Mark as Shipped"
date_delivered      → When customer confirms
```

## API Integration (Later)

```
When you have 10-15 orders:
1. Read: PAYMENT_INTEGRATION_GUIDE.md
2. Choose: Payfast (recommended)
3. Get: API credentials
4. Change: payment/utils.py PaymentProcessor
5. Add: Webhook handler in views.py
6. Test: With sandbox
7. Deploy: To production

Time: 2-3 weeks
Database Changes: NONE needed ✅
```

## Files You Care About

**Daily Use:**
- Django Admin: `/admin/payment/order/`

**Reference:**
- PAYMENT_QUICK_REFERENCE.md

**Documentation:**
- README_PAYMENT_SYSTEM.md (start here)
- PAYMENT_SYSTEM_SUMMARY.md (overview)

**Code (Don't touch unless developing):**
- payment/utils.py (payment logic)
- payment/views.py (checkout)

## Test This Works

```
1. Create sample order via website
2. Check payment_code is populated
3. Go to admin → Orders
4. Verify order appears with code
5. Click "Confirm Payment Received"
6. Check email was sent
7. Verify status changed to "paid"
8. You're good to launch!
```

## Backup: Manual Confirmation

If something breaks, you can still manually:
1. Go to Order in admin
2. Set status to "paid" 
3. Click Save
4. Send email to customer manually

(But this shouldn't be needed with the system set up)

## Remember

✅ Unique payment code links payment to order  
✅ Always verify amount before confirming  
✅ Admin actions handle everything else  
✅ All data is safe in Django admin  
✅ Emails automatic (when configured)  
✅ You can upgrade to real API anytime  

---

**Print this page. Keep it handy while processing orders.**

Last Updated: January 21, 2026
