# Generated by Django 2.2.16 on 2022-01-15 14:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20220115_1552'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Comment',
        ),
    ]
