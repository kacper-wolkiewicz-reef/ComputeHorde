# Generated by Django 4.2.19 on 2025-07-08 19:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("test_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Validator2",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("ss58_address", models.CharField(max_length=48, unique=True)),
                ("is_active", models.BooleanField()),
            ],
        ),
    ]
