# Generated by Django 3.2.5 on 2021-07-27 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0003_auto_20210727_1932'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='age',
            field=models.IntegerField(blank=True, null=True, verbose_name='age'),
        ),
    ]