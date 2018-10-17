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

# from .peck import views
# from .peck import forms
# from django.urls import path, register_converter
# from django.urls import reverse, re_path
# from django.urls import url, pattern
# admin.autodiscover()

app_name = 'peck'
urlpatterns = [

    # 16) Admin
    # url(r'^admin/', admin.site.urls),

    # 15) List of Firmwares
    # path('listafirm/<str:ser>', views.lista_firm, name="lista_firm"),
    url(r'^peck/listafirm/<str:ser>', views.lista_firm, name="lista_firm"),

    # 14) Edit Machine Profile Information
    # path('peck/editmaq/', views.editmaq, name="editmaq"),

    # 13)
    # url(r'^peck/listapeck/$', views.l_pecks),
    url(r'^peck/listapeck/$', views.l_pecks, name="listapeck"),
    #path('listapeck/', views.l_pecks, name="listapeck"),

    # 12)
    # url(r'^peck/detalhe/(?P<peck_id>\d+)/$', views.d_pecks),
    # url(r'^peck/detalhe/(?P<peck_id>\d+)/$', views.d_pecks),
    # path('<int:question_id>/results/', views.results, name='results'),
    # path('detalhe/<int:peck_id>/', views.d_pecks, name='detailspeck'),
    # url(r'^peck/details/(?P<peck_id>\d+)/$', views.d_pecks, name="detailspeck"),
    url(r'^peck/details/(\d+)', views.d_pecks, name="detailspeck"),

    # 11)
    # path('report/(<str:sall>/', views.report, name='report'),
    # url(r'^peck/report/(?P<sall>\w+)/$', views.report),
    # url(r'^peck/report/(?P<sall>\d+)/$', views.report),
    url(r'^peck/report/(?P<sall>\d+)/$', views.report, name="report"),

    # 10) Method to UPLOAD files
    # url(r'^peck/arq/$', views.sobe_arq,),
    # path('arq/', views.sobe_arq, name='uploadfile'),
    url(r'^peck/arq/$', views.sobe_arq, name="uploadfile"),

    # 9) List of UPLOADED documents
    # url(r'^peck/docs/$', views.l_docs),
    # path('docs/', views.l_docs, name='listadocs'),
    url(r'^peck/docs/$', views.l_docs, name="listadocs"),

    # 8) List of Machine SERIAL numbers
    #url(r'^peck/maqs/$', views.l_maqs),

    # 7) List of Machine Models
	url(r'^peck/modelos/$', views.l_mod, name="vermodelos"),
    # path('modelos/', views.l_mod, name='vermodelos'),

    # 6) List of Clients
    url(r'^peck/listaclis/$', views.l_clis, name="listaclis"),
    # path('listaclis/', views.l_clis, name='listaclis'),

    # 5) VerText is a method to see the original PECK file
    url(r'^peck/uploaded/(?P<filename>\w+)/$$', views.vertxt, name="vertxt"),
    # path('uploaded/<path:filename>/', views.vertxt, name='vertxt'),

    # 4) Download method
    url(r'^peck/baixar/$', views.baixar, name="baixar"),
    # path('baixar/', views.baixar, name='baixar'),

    # 3) Search method
    url(r'^peck/search/$', views.search_cli, name='search'),
    # path('search/', views.search_cli, name='search'),

    # 2) Meta class???
    # url(r'^peck/meta/$', views.dmeta),
    # path('peck/dmeta/', views.dmeta, name='dmeta'),

    # 1) Home Page
    # url(r'^peck/$', views.index, name='index'),
    url(r'^peck/$', views.index, name='vhome'),
    # path('', views.index, name='vhome'),
    # url(r'^$', include('amply.peck.urls')),

   	]
    # + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
#     (r'^static/peck/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

# ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
