# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-10-17 01:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peck', '0005_auto_20181016_1833'),
    ]

    operations = [
        migrations.RenameField(
            model_name='machine',
            old_name='client_id',
            new_name='client',
        ),
        migrations.RenameField(
            model_name='machine',
            old_name='model_id',
            new_name='model',
        ),
        migrations.RenameField(
            model_name='modelo',
            old_name='modelo',
            new_name='model',
        ),
        migrations.RenameField(
            model_name='peck',
            old_name='machine_id',
            new_name='machine',
        ),
        migrations.RenameField(
            model_name='peck',
            old_name='model_id',
            new_name='model',
        ),
        migrations.AlterField(
            model_name='peck',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
