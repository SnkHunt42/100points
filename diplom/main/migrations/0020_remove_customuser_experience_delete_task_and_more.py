# Generated by Django 5.0.4 on 2024-05-23 09:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_question'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='experience',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
        migrations.DeleteModel(
            name='Experience',
        ),
    ]
