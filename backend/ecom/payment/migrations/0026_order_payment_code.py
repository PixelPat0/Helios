# payment/migrations/0026_order_payment_code.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0025_alter_orderitem_commission_rate'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_code',
            field=models.CharField(
                blank=True,
                help_text='Unique payment code (e.g., HLS-1001-A7K2) for customer to include with payment',
                max_length=20,
                null=True,
                unique=True,
            ),
        ),
    ]
