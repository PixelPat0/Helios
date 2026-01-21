# MVP Payment System Documentation

## Overview

This is a **manual payment verification system** designed for the first 10-15 orders before integrating a full payment gateway. It's safe, trackable, and audit-proof.

---

## How It Works

### Customer Flow (Buyer)

1. **Customer adds items to cart** and completes checkout
2. **Order is created** with status = `pending`
3. **Unique Payment Code is generated** automatically (e.g., `HLS-1001-A7K2`)
4. **Customer is redirected** to payment instructions page showing:
   - Order ID and total amount
   - Your brother's phone number (receiving account)
   - **Payment code to include in transfer message**
   - Step-by-step instructions

### Your Flow (Order Verification)

1. **You receive payment** into your brother's account
2. **You verify** the amount matches the order
3. **You check** the payment message contains the payment code
4. **You go to Django admin** → Orders
5. **You select the order** and click action: **"✓ Confirm Payment Received"**
6. **System automatically:**
   - Changes order status to `paid`
   - Records payment date/time
   - Sends confirmation email to customer
   - Notifies seller (if multi-seller)
7. **Order is ready** for processing/fulfillment

---

## Admin Quick Start

### View All Orders

```
Django Admin → Orders
```

**Columns shown:**
- Order ID
- Payment Code (what customer sent)
- Customer Name
- Email
- Amount Paid
- Status (pending/paid/processing/shipped)
- Date Ordered

### Confirm a Payment

1. **Go to Orders list**
2. **Check the box** next to pending order
3. **Select action:** "✓ Confirm Payment Received (Pending → Paid)"
4. **Click "Go"**

✅ Done! Status changes to "paid" automatically.

### Process an Order

1. **Verify payment is confirmed** (status = "paid")
2. **Select the order**
3. **Choose action:** "→ Mark as Processing"
4. **Click "Go"**

The system will:
- Set status to `processing`
- Record the processing date
- Notify seller to start fulfillment

### Mark as Shipped

1. **When you ship the package**, select the order
2. **Choose action:** "📦 Mark as Shipped"
3. **Click "Go"**

The system will:
- Set status to `shipped`
- Record the shipped date/time
- Send shipping confirmation email to customer

---

## Payment Code Explanation

### Format
```
HLS-{OrderID}-{RandomSuffix}
Examples:
  HLS-1001-A7K2
  HLS-1002-K9P1
  HLS-1003-Z3M5
```

### Why Use It?

If multiple payments come in on the same day, you need to know **which payment is for which order**.

**Without payment code:** 
- Payment received: K50,000
- But which of 3 orders is it for? 😕

**With payment code:**
- Payment received: K50,000 for "HLS-1001-A7K2"
- Instantly matches to Order #1001 ✅

---

## Settings Configuration

To make this work, update your `settings.py` or `.env`:

```python
# .env file
BROTHER_PHONE_NUMBER="+260977123456"  # Add this
BROTHER_NAME="Helios Zambia (Brother Account)"  # Add this
BUSINESS_EMAIL="helios.zambia@gmail.com"  # Update this
```

Then in your `settings.py`:
```python
BROTHER_PHONE = os.getenv('BROTHER_PHONE_NUMBER', '+260977XXXXXX')
BROTHER_NAME = os.getenv('BROTHER_NAME', 'Helios Zambia')
BUSINESS_EMAIL = os.getenv('BUSINESS_EMAIL', 'helios@example.com')
```

Update the `payment_pending.html` template to use these settings:
```django
{{ brother_number }}  → pulls from settings
{{ brother_name }}    → pulls from settings
```

---

## Audit Trail & Safety

### What Gets Recorded?

For each order, the system stores:
- ✅ Order ID (auto-incremented, unique)
- ✅ Payment Code (customer's reference)
- ✅ Payment Method (airtel/mtn/zamtel/card/cod)
- ✅ Payment Reference (if customer provided)
- ✅ Amount Paid (exact amount)
- ✅ Date Ordered (when order was created)
- ✅ Date Paid (when you confirmed payment)
- ✅ Customer Name & Email
- ✅ Status Timeline (pending → paid → processing → shipped → delivered)

### Proof for Business Registration

When you apply for business registration or open a business account, you can show:

1. **Order List (Export from Admin)**
   - CSV export showing all orders, amounts, dates
   
2. **Bank Statement**
   - Shows deposits matching order amounts
   - With payment code references in the messages

3. **Email Confirmations**
   - Order confirmations sent to customers
   - Payment confirmation emails
   - Shipping confirmations

4. **Django Admin Audit**
   - Timestamps for every status change
   - Who confirmed what payment and when

---

## What to Do When Payment Comes In

### Checklist

- [ ] Check amount matches order total
- [ ] Check payment message contains the payment code
- [ ] Go to Django Admin → Orders
- [ ] Find the order by payment code or order ID
- [ ] Click "Confirm Payment Received" action
- [ ] Verify email confirmation was sent to customer
- [ ] Move order to "Processing"
- [ ] Prepare package for shipment

### Example

**Payment received:**
```
Amount: K50,000
From: 0977123456 (Airtel Money)
Message: HLS-1001-A7K2 - Helios Order
```

**Actions:**
1. Go to Orders → Find Order #1001
2. Click "Confirm Payment Received"
3. Status now = "paid" ✅
4. Email sent to customer ✅
5. Select again, click "Mark as Processing"
6. Status now = "processing" ✅

---

## Troubleshooting

### Order Not Found

**Problem:** Payment came in but you can't find the order in admin

**Solution:**
1. Go to Orders list
2. Use **Search** field (top right)
3. Search by:
   - **Order ID** (just the number, e.g., `1001`)
   - **Payment Code** (e.g., `HLS-1001`)
   - **Customer Name** or **Email**

### Payment Code Not Generated

**Problem:** Order created but payment_code field is empty

**Solution:**
1. Click the order to edit it
2. Scroll to "MVP Payment Tracking" section
3. Click "Save" — the system will auto-generate the code

### Customer Sent Payment Without Code

**Problem:** Customer paid K50,000 but didn't include the payment code

**Solution:**
1. Contact customer via email (you have their email)
2. Ask for bank screenshot of their payment
3. Manually match amount to order
4. In Django admin, edit the order:
   - Set `payment_reference` = their transaction ID
   - Click "Confirm Payment Received" action
5. Send them email confirmation

---

## Email Notifications

### What Customers Receive

**Order Confirmation Email:**
- Order ID & items
- Total amount
- Payment instructions
- Payment code to use
- Your brother's phone number
- Deadline (24 hours)

**Payment Confirmed Email:**
- "Your payment has been verified"
- Order status changed to "Paid"
- Processing begins
- Expected delivery date (if set)

**Shipped Email:**
- "Your order has shipped!"
- Tracking info (if available)
- Delivery timeframe

---

## Future Upgrade Path

When you're ready to integrate a real payment gateway (after first 10-15 orders):

1. Keep this manual system as **backup**
2. Add Payfast/Zamtel API integration
3. Automatic payment verification (webhook)
4. Status changes automatically on confirmation
5. No more manual admin action needed

The database schema is already ready for this upgrade — just add the webhook handler.

---

## Quick Reference

| Action | Where | How |
|--------|-------|-----|
| **View Orders** | Admin → Payment → Orders | List view shows all orders + payment codes |
| **Confirm Payment** | Admin → Orders → (Select) | Action: "✓ Confirm Payment Received" |
| **Mark Processing** | Admin → Orders → (Select) | Action: "→ Mark as Processing" |
| **Mark Shipped** | Admin → Orders → (Select) | Action: "📦 Mark as Shipped" |
| **Search Order** | Admin → Orders | Use Search field (top right) |
| **Find by Payment Code** | Admin → Orders Search | Type "HLS-1001" |
| **Export Orders** | Admin → Orders → Export | Download CSV for records |

---

## Database Fields Reference

```python
# Order model
order.id                 # Unique order ID (1, 2, 3...)
order.payment_code       # HLS-{ID}-{3chars}
order.full_name          # Customer name
order.email              # Customer email
order.amount_paid        # K amount
order.status             # pending/paid/processing/shipped/delivered
order.payment_method     # airtel/mtn/zamtel/card/cod
order.payment_reference  # Transaction ID (if customer provided)
order.date_ordered       # When order was created
order.date_paid          # When payment was confirmed
order.date_processed     # When processing started
order.date_shipped       # When package shipped
order.date_delivered     # When delivered
order.phone_number       # Customer phone
order.shipping_address   # Full delivery address
```

---

## Support

If you encounter issues:
1. Check the **Troubleshooting** section above
2. Review the **Order Details** in Django admin
3. Check email logs if notifications fail
4. Check Django logs: `python manage.py shell` → `Order.objects.all()`

---

**Version:** MVP v1.0  
**Last Updated:** January 21, 2026  
**Status:** Production Ready for Manual Orders
