#!/usr/bin/python
# -*- coding: utf-8 -*-

from .models import Peck, Machine, Modelo, Client, InkVendor
from django.contrib import admin


# class PeckAdmin(admin.ModelAdmin):
    # list_display = ('pSerial', 'pModelo', 'firmware', 'date',)
    # search_fields = ['fone', 'nomecompleto', 'logradouro',]
    # list_filter = ('tipo',)

# class UpdocAdmin(admin.ModelAdmin):
#     list_display = ('docfile',)

# class MaquinaAdmin(admin.ModelAdmin):
#     list_display = ('serial', 'client', 'machine_id', 'typtinta')

# class ModelosAdmin(admin.ModelAdmin):
#     list_display = ('modelo', 'qtecab', 'scan', 'pump', 'wipe', 'felt')

# admin.site.register(Peck, PeckAdmin)
admin.site.register(Peck)
admin.site.register(Machine)
admin.site.register(Modelo)
admin.site.register(Client)
admin.site.register(InkVendor)
# admin.site.register(Modelo, ModeloAdmin)
