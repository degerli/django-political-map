# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-18 23:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('politicalplaces', '0008_auto_20170317_1636'),
    ]

    operations = [
        migrations.AddField(
            model_name='politicalplace',
            name='postal_code',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
