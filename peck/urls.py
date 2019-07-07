#!/usr/bin/python
# -*- coding: utf-8 -*-

"""amply URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url, include, re_path
from django.views.static import *
from peck import views, models
from peck.views import getgraph


app_name = 'peck'
urlpatterns = [
    re_path(r'^listapeck/$', views.l_pecks, name="peck-listpecks"),
    re_path(r'^details/(?P<peck_id>\d+)$', views.detailPeck, name="peck-details"),
    # re_path(r'^details/(\d+)', views.detailPeck, name="peck-details"),        
    re_path(r'^report/(?P<sall>\d+)/$', views.report, name="peck-report"),
    re_path(r'^arq/$', views.sobe_arq, name="peck-uploadfile"),
    re_path(r'^docs/$', views.l_docs, name="peck-listdocs"),
	re_path(r'^modelos/$', views.l_mod, name="peck-listmodels"),
    re_path(r'^listaclis/$', views.l_clis, name="peck-listclients"),
    re_path(r'^listmachine/$', views.l_machine, name="peck-listmachine"),
    re_path(r'^machinedetails/(?P<maq_serial>\w+)/$', views.machine_details, name="peck-machinedet"),
    re_path(r'^uploaded/(?P<filename>\w+)/$$', views.vertxt, name="peck-vertxt"),
    re_path(r'^baixar/$', views.baixar, name="peck-download"),
    re_path(r'^search/$', views.search_cli, name='peck-searchcli'),
    re_path(r'^$', views.index, name='peck-home'),
    # re_path(r'^api/getgraph/$', views.getgraph, name='peck-getgraph')
   	]

# if settings.DEBUG:
#         urlpatterns += [
#             url(r'^peck/uploaded/(?P<path>)$', serve, {
#                 'document_root': settings.MEDIA_ROOT,
#             }),
#         ]
