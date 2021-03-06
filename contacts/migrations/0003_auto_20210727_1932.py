# Generated by Django 3.2.5 on 2021-07-27 19:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_alter_contact_age'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='birthday',
            field=models.DateField(blank=True, verbose_name='birthday'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='email',
            field=models.EmailField(blank=True, max_length=254, validators=[django.core.validators.RegexValidator(regex='(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$)')]),
        ),
    ]
