# Payment System - Quick Reference

## Files Structure

```
payment/
├── models.py              # Order, OrderItem, Seller models
├── views.py               # Checkout, payment handling views
├── admin.py              # Django admin configuration
├── utils.py              # ← PAYMENT LOGIC (PRIMARY FILE FOR API)
├── forms.py              # Payment forms
├── urls.py               # URL routing
├── decorators.py         # Permission decorators
├── email_utils.py        # Email notifications
│
└── templates/
    └── payment/
        ├── payment_pending.html       # Instructions after order creation
        ├── billing_info.html          # Checkout form
        └── order_details.html         # Order confirmation
```

---

## Current MVP Flow (✅ Working)

### Customer Journey

```
1. Add items to cart
   ↓
2. Go to checkout
   ↓
3. Enter shipping address
   ↓
4. Submit order (status='pending')
   ↓
5. Redirected to payment_pending page
   ↓
6. See payment code: HLS-1001-A7K2
   ↓
7. Customer sends money to brother's account with code
   ↓
8. [Admin verifies payment in Django Admin]
   ↓
9. Admin clicks: "✓ Confirm Payment Received"
   ↓
10. Order status changes to 'paid'
    ↓
11. Email confirmation sent to customer
```

---

## Key Code Locations

### 1. When to Use PaymentProcessor

**File:** `payment/utils.py` (lines 55-105)

```python
# MVP: Just records the payment
payment_result = PaymentProcessor.process_payment(order, payment_method, ref)

# Returns:
{
    'success': True,
    'message': 'Payment submitted for verification',
    'requires_manual_verification': True,  # ← Key: Still needs admin approval
    'instruction': 'Admin will verify payment in Django admin'
}
```

### 2. When to Use PaymentConfirmation

**File:** `payment/utils.py` (lines 126-189)

**Called from:**
- Django admin action (manual verification)
- Future webhook handler (automatic verification)

```python
result = PaymentConfirmation.confirm_payment_received(order)

# Returns:
{
    'success': True,
    'message': 'Payment confirmed for Order #1001',
    'order_status': 'paid',
    'date_paid': datetime
}
```

### 3. Payment Admin Actions

**File:** `payment/admin.py` (lines 67-95)

Three one-click actions:
- `confirm_payment_received()` - Pending → Paid
- `mark_processing()` - Paid → Processing
- `mark_shipped()` - Processing → Shipped

---

## Order Status Lifecycle

```
pending
  ↓ [Admin confirms payment]
paid
  ↓ [Admin marks processing]
processing
  ↓ [Admin marks shipped]
shipped
  ↓ [Customer confirms delivery OR auto-confirm after X days]
delivered
```

### Status Timestamps

```python
order.date_ordered      # Auto: When order created
order.date_paid         # Auto: When confirmed as paid
order.date_processed    # Auto: When moved to processing
order.date_shipped      # Auto: When marked shipped
order.date_delivered    # Auto: When delivered
```

---

## Payment Fields in Order Model

```python
# Customer info
order.full_name         # Customer name
order.email             # Customer email
order.phone_number      # Customer phone
order.shipping_address  # Full shipping address
order.amount_paid       # Total order amount (K)

# Payment tracking
order.payment_code      # HLS-{ID}-{CODE} ← Customer includes with payment
order.payment_method    # airtel, mtn, zamtel, card, cod
order.payment_reference # Transaction ID (if customer provided)
order.status            # pending/paid/processing/shipped/delivered

# Timestamps
order.date_ordered      # When order was created
order.date_paid         # When payment was confirmed
order.date_processed    # When fulfillment started
order.date_shipped      # When package shipped
order.date_delivered    # When delivery confirmed
```

---

## Common Tasks

### Task 1: Process an Incoming Payment

**Scenario:** Customer sent K50,000 with message "HLS-1001-A7K2"

**Steps:**
1. Go to Django Admin → Payments → Orders
2. Search for "HLS-1001" or order ID "1001"
3. Click the order to view details
4. Verify amount matches K50,000
5. Select checkbox and choose action: "✓ Confirm Payment Received"
6. Click "Go"
7. ✅ Status changes to "paid"
8. ✅ Email automatically sent to customer

### Task 2: Prepare Order for Shipment

**Steps:**
1. Go to Orders list
2. Filter by status: "paid"
3. Select the order
4. Choose action: "→ Mark as Processing"
5. Click "Go"
6. ✅ Status changes to "processing"
7. ✅ Seller gets notification
8. Start picking/packing items

### Task 3: Mark Order as Shipped

**Steps:**
1. Go to Orders list
2. Find the order (status should be "processing")
3. Select checkbox
4. Choose action: "📦 Mark as Shipped"
5. Click "Go"
6. ✅ Status changes to "shipped"
7. ✅ Email sent to customer with tracking

### Task 4: Find an Order by Payment Code

**Steps:**
1. Go to Django Admin → Payments → Orders
2. Use Search box (top right)
3. Type the payment code: `HLS-1001`
4. Hit Enter
5. Order will appear
6. Click to view/edit

---

## Important: What NOT to Touch

### ❌ Don't modify these fields manually in the database

- `order.date_paid` - Set automatically by `update_status()`
- `order.date_processed` - Set automatically
- `order.date_shipped` - Set automatically
- `order.status` - Use the admin actions instead
- `order.payment_code` - Auto-generated, don't touch

### ✅ Safe to modify in admin

- `order.payment_reference` - Add customer's transaction ID if missing
- `order.phone_number` - Update if customer provided wrong number
- `order.cancellation_notes` - Add notes if cancelling order

---

## Testing Checklist

### Manual Testing (MVP)

- [ ] Create test order with real amount
- [ ] Verify payment code generated (format: `HLS-{ID}-{code}`)
- [ ] Check payment_pending page shows correct info
- [ ] Send test payment to brother's account
- [ ] In Django admin, confirm payment received
- [ ] Verify order status changed to "paid"
- [ ] Check email was sent to customer
- [ ] Mark as processing
- [ ] Mark as shipped
- [ ] Check customer received all emails

### Data Integrity

- [ ] Order totals are correct
- [ ] Commission amounts calculated (8%)
- [ ] Seller earnings tracked properly
- [ ] All order items created
- [ ] Customer can view their order

---

## Payment Code Format

**Format:** `HLS-{OrderID}-{3RandomChars}`

**Examples:**
```
HLS-1001-A7K2
HLS-1002-Z9M1
HLS-1003-K3P5
```

**Why this format?**
- `HLS` = Helios (recognizable)
- `1001` = Order ID (links to exact order)
- `A7K2` = Random (prevents guessing)

**Customer should send:**
```
To: Brother's number
Amount: K50,000
Message: HLS-1001-A7K2
```

---

## Error Messages & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Order not found" | Invalid order ID | Check order number is correct |
| "Amount mismatch" | Wrong amount sent | Check customer sent exact amount |
| "Payment code missing" | No code in message | Ask customer to resend with code |
| "Order already paid" | Trying to confirm twice | Order is already confirmed |
| "Status conflict" | Trying wrong action | Check order is in correct status |

---

## Logging & Debugging

### View Payment Logs

```python
# In Django shell:
python manage.py shell

from payment.models import Order
order = Order.objects.get(id=1001)
order.payment_method
order.payment_reference
order.date_paid
order.status
```

### Check Payment History

```python
# Get last 10 orders
Order.objects.all().order_by('-date_ordered')[:10]

# Get pending orders
Order.objects.filter(status='pending')

# Get paid orders
Order.objects.filter(status='paid')

# Get orders by payment method
Order.objects.filter(payment_method='airtel')
```

---

## When to Upgrade to Real Payment API

**Upgrade when:**
- ✅ Processed 10-15 successful manual orders
- ✅ Received business registration documents
- ✅ Have capital for payment provider integration
- ✅ Ready to stop manual verification

**Upgrade process:**
1. Choose payment provider (Payfast recommended)
2. Sign up and get API credentials
3. Follow PAYMENT_INTEGRATION_GUIDE.md
4. Test with sandbox environment
5. Deploy to production
6. Keep manual system as backup

**Timeline:** 2-3 weeks for integration + testing

---

## Support & Next Steps

### If something breaks:

1. Check Django logs: `python manage.py shell`
2. Check email settings in `.env`
3. Verify order data in admin
4. Run: `python manage.py migrate` if migration error
5. Restart Django server

### For API integration questions:

See: `PAYMENT_INTEGRATION_GUIDE.md`

### For payment settings:

See: `.env.example` and `settings.py`

---

**Last Updated:** January 21, 2026  
**Version:** MVP 1.0  
**Status:** ✅ Ready for production
