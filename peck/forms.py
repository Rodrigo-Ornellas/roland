#!/usr/bin/python
# -*- coding: utf-8 -*-

from django import forms
from .models import *

# https://stackoverflow.com/questions/4271686/object-has-no-attribute-save-django
class PeckForm(forms.ModelForm):
    file = forms.FileField( label='Nome do Aqrquivo' ) #upload_to='/uploaded/'

    class Meta:
        model = Peck
        fields = '__all__'
