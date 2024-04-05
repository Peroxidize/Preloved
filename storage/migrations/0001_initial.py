# Generated by Django 5.0.3 on 2024-04-02 16:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extension', models.CharField(max_length=10)),
                ('type', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='StorageBucket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.CharField(max_length=1028)),
                ('fileTypeID', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='storage.filetype')),
                ('bucketStorageID', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='storage.storagebucket')),
            ],
        ),
    ]
