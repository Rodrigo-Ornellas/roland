# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib import messages

#==================================================================
# 1) User Registrations

def register(request):
    if  request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            # messages.debug
            # messages.info
            # messages.success
            # messages.warning
            # messages.error
            return redirect('peck:peck-home')

    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form' : form})


