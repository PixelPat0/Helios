"""
payment/management/commands/check_pending_payments.py

Quick command to view all pending payments waiting for confirmation.
Usage: python manage.py check_pending_payments
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from payment.models import Order
from decimal import Decimal


class Command(BaseCommand):
    help = 'Display all pending payments waiting for confirmation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Show orders pending for more than X hours (default: 24)'
        )

    def handle(self, *args, **options):
        hours_threshold = options['hours']
        
        # Get all pending orders
        pending_orders = Order.objects.filter(status='pending').order_by('date_ordered')
        
        if not pending_orders.exists():
            self.stdout.write(self.style.SUCCESS('✓ No pending orders!'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n⏳ PENDING PAYMENTS ({pending_orders.count()} total)\n'))
        self.stdout.write('=' * 100)
        
        now = timezone.now()
        overdue_count = 0
        
        for order in pending_orders:
            # Calculate time pending
            time_pending = now - order.date_ordered
            hours_pending = time_pending.total_seconds() / 3600
            
            # Check if overdue
            is_overdue = hours_pending > hours_threshold
            if is_overdue:
                overdue_count += 1
            
            # Format output
            status_badge = '⚠️  OVERDUE' if is_overdue else '⏳ PENDING'
            
            self.stdout.write(
                f'\n{status_badge} | Order #{order.id}\n'
                f'  Payment Code: {order.payment_code or "NOT GENERATED"}\n'
                f'  Customer: {order.full_name}\n'
                f'  Email: {order.email}\n'
                f'  Amount: K{order.amount_paid}\n'
                f'  Ordered: {order.date_ordered.strftime("%Y-%m-%d %H:%M:%S")} '
                f'({int(hours_pending)}h ago)\n'
                f'  Payment Method: {order.payment_method or "Not specified"}\n'
            )
        
        # Summary
        self.stdout.write('=' * 100)
        self.stdout.write(
            self.style.WARNING(
                f'\n📊 SUMMARY:\n'
                f'  Total Pending: {pending_orders.count()}\n'
                f'  Overdue (24h+): {overdue_count}\n'
            )
        )
        
        # Total amount pending
        total_pending = pending_orders.aggregate(total=sum('amount_paid'))['total'] or Decimal('0.00')
        self.stdout.write(
            f'  Total Amount: K{total_pending:,.2f}\n'
        )
        
        # Next steps
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ ACTION: Go to Django Admin → Payment → Orders\n'
                f'  Select pending order(s) and use action: "Confirm Payment Received"\n'
            )
        )
