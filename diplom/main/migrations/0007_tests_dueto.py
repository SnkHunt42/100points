# Generated by Django 5.0.4 on 2024-05-13 10:32

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_questions_image_tasks_tutor_tests_tutor'),
    ]

    operations = [
        migrations.AddField(
            model_name='tests',
            name='dueto',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]