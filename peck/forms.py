#!/usr/bin/python
# -*- coding: utf-8 -*-

from django import forms
from .models import *

# https://stackoverflow.com/questions/4271686/object-has-no-attribute-save-django
# https://godjango.com/35-upload-files/
class PeckForm(forms.Form):
    file = forms.FileField( label='Nome do Aqrquivo' ) #upload_to='/uploaded/'
