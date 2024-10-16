# Generated by Django 5.0.3 on 2024-04-02 16:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('preloved_auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoadVoucher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('voucher_code', models.CharField(max_length=20)),
                ('value', models.IntegerField()),
                ('is_redeemed', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sizeType', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('tagID', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('itemID', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('isFeminine', models.BooleanField(default=True)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=20)),
                ('isTaken', models.IntegerField(default=0)),
                ('size', models.ForeignKey(default=1, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.size')),
            ],
        ),
        migrations.CreateModel(
            name='Slug',
            fields=[
                ('slugID', models.AutoField(primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=255, unique=True)),
                ('isDeleted', models.IntegerField(default=0)),
                ('isThumbnail', models.IntegerField(default=0)),
                ('itemID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slugs', to='store.item')),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('storeID', models.AutoField(primary_key=True, serialize=False)),
                ('storeName', models.CharField(max_length=255)),
                ('locationID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stores', to='preloved_auth.location')),
                ('shopOwnerID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stores', to='preloved_auth.shopowner')),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='storeID',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='store.store'),
        ),
        migrations.CreateModel(
            name='ItemTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.item')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.tag')),
            ],
            options={
                'unique_together': {('item', 'tag')},
            },
        ),
    ]
