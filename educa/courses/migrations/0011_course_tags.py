# Generated by Django 5.0.9 on 2024-11-25 03:36

import taggit.managers
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_text_file'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
