# Generated by Django 5.0.9 on 2024-11-23 15:53

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_remove_image_file_image_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.FileField(upload_to='images', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['png'])]),
        ),
    ]
