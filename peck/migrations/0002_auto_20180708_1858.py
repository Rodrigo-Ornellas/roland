# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-09 01:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peck', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='peck',
            name='clean',
            field=models.PositiveIntegerField(default=1, verbose_name='Last Head Clean'),
        ),
        migrations.AlterField(
            model_name='peck',
            name='feed',
            field=models.PositiveIntegerField(default=1, verbose_name='Motor Feed'),
        ),
        migrations.AlterField(
            model_name='peck',
            name='limp',
            field=models.PositiveIntegerField(default=1, verbose_name='Menu Cleaning'),
        ),
        migrations.AlterField(
            model_name='peck',
            name='liq',
            field=models.PositiveIntegerField(default=1, verbose_name='Liquido na Garrafa'),
        ),
        migrations.AlterField(
            model_name='peck',
            name='pump',
            field=models.PositiveIntegerField(default=1, verbose_name='Pump Scan'),
        ),
        migrations.AlterField(
            model_name='peck',
            name='scan',
            field=models.PositiveIntegerField(default=1, verbose_name='Motor Scan'),
        ),
        migrations.AlterField(
            model_name='peck',
            name='wipe',
            field=models.PositiveIntegerField(default=1, verbose_name='Wiping Count'),
        ),
    ]