# Generated by Django 5.0.3 on 2024-04-02 16:15

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Status',
            fields=[
                ('statusID', models.AutoField(primary_key=True, serialize=False)),
                ('status_name', models.CharField(max_length=255)),
                ('level', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('ticketID', models.AutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('expected_seller_fulfillment', models.DateField(null=True)),
                ('expected_buyer_fulfillment', models.DateField(null=True)),
                ('itemID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='store.item')),
                ('status', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='tickets.status')),
                ('storeID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='store.store')),
                ('userID', models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
