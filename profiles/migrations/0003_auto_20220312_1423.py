# Generated by Django 3.0 on 2022-03-12 14:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_relationship'),
    ]

    operations = [
        migrations.RenameField(
            model_name='relationship',
            old_name='reciever',
            new_name='receiver',
        ),
    ]
