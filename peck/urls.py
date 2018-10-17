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
from django.views.static import *
from peck import views, models
from peck.views import getgraph


app_name = 'peck'
urlpatterns = [
    url(r'^peck/listafirm/<str:ser>', views.lista_firm, name="lista_firm"),
    url(r'^peck/listapeck/$', views.l_pecks, name="listapeck"),
    url(r'^peck/details/(\d+)', views.d_pecks, name="detailspeck"),
    url(r'^peck/report/(?P<sall>\d+)/$', views.report, name="report"),
    url(r'^peck/arq/$', views.sobe_arq, name="uploadfile"),
    url(r'^peck/docs/$', views.l_docs, name="listadocs"),
	url(r'^peck/modelos/$', views.l_mod, name="vermodelos"),
    url(r'^peck/listaclis/$', views.l_clis, name="listaclis"),
    url(r'^peck/listmachine/$', views.l_machine, name="listmachine"),
    url(r'^peck/uploaded/(?P<filename>\w+)/$$', views.vertxt, name="vertxt"),
    url(r'^peck/baixar/$', views.baixar, name="baixar"),
    url(r'^peck/search/$', views.search_cli, name='search'),
    url(r'^peck/$', views.index, name='vhome'),
    url(r'^peck/api/getgraph/$', views.getgraph, name='apig1')
   	]

if settings.DEBUG:
        urlpatterns += [
            url(r'^peck/uploaded/(?P<path>)$', serve, {
                'document_root': settings.MEDIA_ROOT,
            }),
        ]
