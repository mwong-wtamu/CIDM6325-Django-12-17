# Generated by Django 5.0.9 on 2024-11-23 15:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_alter_image_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='image',
            old_name='image',
            new_name='file',
        ),
    ]
