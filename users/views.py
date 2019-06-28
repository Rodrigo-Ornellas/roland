# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

#==================================================================
# 1) User Registrations

def register(request, *args, **kwargs):
    if  request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data['password1']
            newuser = User.objects.create_user(username=username, password=password)
            form.save()
            # User.objects.create_user(username=username, password=password)
            messages.success(request, 'Account created for {}!'.format(username))
            # authenticate(user)
            # login(request, user)
            # messages.debug
            # messages.info
            # messages.success
            # messages.warning
            # messages.error
            return redirect('peck:peck-home')

    else:
        form = UserCreationForm()
        
    return render(request, 'users/register.html', {'form' : form})


