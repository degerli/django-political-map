# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-21 00:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import politicalplaces.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('politicalplaces', '0005_auto_20170119_1737'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('place', politicalplaces.fields.PlaceField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='politicalplaces.PoliticalPlace')),
            ],
        ),
    ]
