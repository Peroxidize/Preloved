# Generated by Django 5.1.1 on 2024-10-14 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='slug',
            name='isModelRegistered',
            field=models.BooleanField(default=False),
        ),
    ]
