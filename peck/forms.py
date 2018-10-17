    #!/usr/bin/python
# -*- coding: utf-8 -*-

from django import forms
from .models import Peck

# https://stackoverflow.com/questions/4271686/object-has-no-attribute-save-django
# https://godjango.com/35-upload-files/
# class PeckForm(forms.Form):
#     file = forms.FileField( label='File Name' ) #upload_to='/uploaded/'


class PeckForm(forms.Form):
    class Meta:
        model = Peck
        fields = [
            "filepath",
            ]
