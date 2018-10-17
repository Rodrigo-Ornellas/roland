#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.db import models
import datetime
from django.utils import timezone
from django.conf import settings

TTINTA_CHOICES = (
    ('0', 'Solvente'),
    ('1', 'Sublimatica'),
    ('2', 'UV'),
    ('3', 'N/A'),
                    )

INKVENDOR_CHOICES = (
    ('0', 'Test 1'),
    ('1', 'Test 2'),
    ('2', 'Test 3'),
    ('3', 'N/A'),
                    )

class Client(models.Model):
    company = models.CharField(u'Company', max_length=32)
    address = models.CharField(u'Address', max_length=32, blank=True)
    city = models.CharField(u'City', max_length=32, blank=True)
    complement = models.CharField(u'Complement', max_length=32, blank=True)
    phone = models.CharField(u'Phone', max_length=32, blank=True)
    contact = models.CharField(u'Contact', max_length=32, blank=True)
    email = models.EmailField(u'E-mail', max_length=128, blank=True)
    comments = models.CharField(u'Comments', max_length=32, blank=True)

    def __str__(self):
        return self.company

class Modelo(models.Model):
    model = models.CharField(u'Model', db_index=True, max_length=8)
    heads = models.PositiveIntegerField(u'Heads')
    scan = models.PositiveIntegerField(u'Scan Life')
    pump = models.PositiveIntegerField(u'Pump Life')
    felt = models.PositiveIntegerField(u'Felt Life')
    tube = models.PositiveIntegerField(u'Tube Life')
    wipe = models.PositiveIntegerField(u'Wiper Life')
    uvlamp = models.PositiveIntegerField(u'UVLamp Life') # null=True, blank=True)

    def __str__(self):
        return self.model


class Machine(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE,default=None)
    model = models.ForeignKey('Modelo', on_delete=models.CASCADE,default=None)
    serial = models.CharField(u'Numero de Serie', db_index=True, max_length=8)
    typtinta = models.CharField(max_length=24, choices=TTINTA_CHOICES, blank=True)
    install = models.DateField(default=timezone.now) #u'Data da Instalacao'
    comments = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return self.serial

# ForeignKey > https://docs.djangoproject.com/en/1.4/ref/models/fields/
# https://docs.djangoproject.com/en/2.0/ref/models/fields/#django.db.models.ForeignKey.on_delete
# https://www.valentinog.com/blog/django-missing-argument-on-delete/
class Peck(models.Model):
    model = models.ForeignKey(u'Modelo', on_delete=models.CASCADE, default=None)
    machine = models.ForeignKey(u'Machine', on_delete=models.CASCADE, default=None)
    #   ink_vendor = models.ForeignKey(u'InkVendor', on_delete=models.CASCADE, default=None)
    firmware = models.DecimalField(u'Versao do Firmware', decimal_places=2, max_digits=5)
    pSerial = models.CharField(u'Numero de Serie', default='AABBCCE', db_index=True, max_length=8)
    pModelo = models.CharField(u'Model', default=None, db_index=True, max_length=8)
    createDate = models.DateField(u'Data do Relatorio')
    ink = models.CharField(u'Tipo de Tinta', max_length=32)
    bat = models.CharField(u'Estado da Bateria', max_length=16)
    feed = models.PositiveIntegerField(u'Motor Feed', default=1)
    scan = models.PositiveIntegerField(u'Motor Scan', default=1)
    pump = models.PositiveIntegerField(u'Pump Scan', default=1)
    limp = models.PositiveIntegerField(u'Menu Cleaning', default=1)
    clean = models.PositiveIntegerField(u'Last Head Clean', default=1)
    wipe = models.PositiveIntegerField(u'Wiping Count', default=1)
    liq = models.PositiveIntegerField(u'Liquido na Garrafa', default=1)
    filepath = models.FileField(upload_to='uploaded/', default='dummy-file')
    # upldate = models.DateField(default=timezone.now)
    # upldate = models.DateField(default=datetime.date.today())  #auto_now_add=True,
    # comments = models.CharField(max_length=120, null=True)
    # https://matthiasomisore.com/web-programming/django-error-you-are-trying-to-add-a-non-nullable-field-to-submission-without-a-default/

    def __str__(self):
        return str(self.pModelo + ' - ' + self.pSerial)

    # def uploaded(self):
    #     return datetime.datetime.now() <= self.upldate

    # def create(cls, file):
    #     peck = cls(filepath=file)
    #     return peck


    #return now - datetime.timedelta(days=1) <= self.pub_date <= now

    #def __unicode__(self):
    #return u"arquivo id: %s" % self.peck.pk

    #class Meta:
        #unique_together = ["serial", "data"]
        # http://stackoverflow.com/questions/3052975/django-models-avoid-duplicates
        # http://wenda.baba.io/questions/5343583/django-saving-with-unique-together-and-deleting-objects-via-inlineformset-cau.html

    # def __unicode__(self):
    #     return self.id

class InkVendor(models.Model):
        vendorname = models.CharField(max_length=96)
        typtinta = models.CharField(max_length=24, choices=TTINTA_CHOICES)


# http://django-adaptors.readthedocs.org/en/latest/index.html
# http://stackoverflow.com/questions/2719038/where-should-signal-handlers-live-in-a-django-project
# https://github.com/anthony-tresontani/django-adaptors/blob/master/docs/index.rst
# http://stackoverflow.com/questions/11200063/django-csv-importer-integer-error

# ===========================================================================================
