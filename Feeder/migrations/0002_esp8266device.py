# Generated by Django 5.1.2 on 2025-04-08 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Feeder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ESP8266Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Pet Feeder', max_length=100)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, protocol='IPv4')),
                ('port', models.PositiveIntegerField(default=80)),
                ('last_connected', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=False)),
            ],
        ),
    ]
