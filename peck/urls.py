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
from django.conf.urls import url, include
# from django.views.static import *
from peck import views, models
from peck.views import getgraph


app_name = 'peck'
urlpatterns = [
    url(r'^listapeck/$', views.l_pecks, name="peck-listpecks"),
    url(r'^details/(?P<peck_id>\d+)$', views.detailPeck, name="peck-details"),
    # url(r'^details/(\d+)', views.detailPeck, name="peck-details"),
    url(r'^report/(?P<sall>\d+)/$', views.report, name="peck-report"),
    url(r'^arq/$', views.sobe_arq, name="peck-uploadfile"),
    url(r'^docs/$', views.l_docs, name="peck-listdocs"),
	url(r'^modelos/$', views.l_mod, name="peck-listmodels"),
    url(r'^listaclis/$', views.l_clis, name="peck-listclients"),
    url(r'^listmachine/$', views.l_machine, name="peck-listmachine"),
    url(r'^machinedetails/(?P<maq_serial>\w+)/$', views.machine_details, name="peck-machinedet"),
    url(r'^uploaded/(?P<filename>\w+)/$$', views.vertxt, name="peck-vertxt"),
    url(r'^baixar/$', views.baixar, name="peck-download"),
    url(r'^search/$', views.search_cli, name='peck-searchcli'),
    url(r'^$', views.index, name='peck-home'),
    # url(r'^api/getgraph/$', views.getgraph, name='peck-getgraph')
   	]

# if settings.DEBUG:
#         urlpatterns += [
#             url(r'^peck/uploaded/(?P<path>)$', serve, {
#                 'document_root': settings.MEDIA_ROOT,
#             }),
#         ]
