# Generated by Django 5.0.3 on 2024-04-02 16:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('preloved_auth', '0001_initial'),
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('is_deleted', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='preloved_auth.shopuser')),
            ],
        ),
        migrations.CreateModel(
            name='CollectionItemUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.IntegerField(default=0)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='preloved_collections.collection')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.item')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='preloved_auth.shopuser')),
            ],
            options={
                'unique_together': {('collection', 'user', 'item')},
            },
        ),
    ]
