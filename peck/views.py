#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpRequest, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.conf import settings
from django.views.generic.edit import UpdateView
from django.views import generic
from django.views.generic import FormView, DetailView, ListView
from django.core.files.storage import FileSystemStorage

from django.core.exceptions import ObjectDoesNotExist
# from django.urls import path, register_converter, reverse, re_path
# from django.core.context_processors import csrf
import json

from .models import Peck, Machine, Modelo, Client, InkVendor, TTINTA_CHOICES
from .forms import PeckForm

from itertools import chain
from datetime import date, datetime, timedelta, time
from collections import Counter
from math import fabs
import email
import getpass, imaplib
import os
import sys
import re

#==================================================================
# 1) HOME view
def index(request):
    lista_pecks = Peck.objects.all().order_by('id')
    context = {'lista_pecks': lista_pecks}
    template = 'peck/index.html'
    return render(request, template, context, content_type="text/html")

#==================================================================
# 2) Meta
# def dmeta(request):
#     # exercicio django book chapter 7
#     # http://www.djangobook.com/en/2.0/chapter07.html
#     values = request.META.items()
#     values.sort()
#     print (values)
#     html = []
#     for k, v in values:
#         html.append('<tr><td>%s</td><td>%s</td></tr>' % (k, v))
#     return HttpResponse('<table>%s</table>' % '\n'.join(html))

# def display_meta(request):
#     values = request.META
#     html = []
#     for k in sorted(values):
#         html.append('<tr><td>%s</td><td>%s</td></tr>' % (k, values[k]))
#     return HttpResponse('<table>%s</table>' % '\n'.join(html))

#==================================================================
# 3) Busca de Cliente
def search_cli(request):
    print (request.GET)
    print (request.GET['query'])
    if 'query' in request.GET and request.GET['query']:
        query = request.GET['query']
        #listao = {}
        busca = Machine.objects.filter(client__icontains=query) | Machine.objects.filter(serial__icontains=query)
        db = Client.objects.filter(company__icontains=query) | Client.objects.filter(contact__icontains=query)
        # print (busca)
        context = {'db': db, 'query': query}
        template = 'peck/index.html'
        return render(request, template, context, content_type="text/html")

    else:
        return HttpResponse('ERRO 004: VIEW: search_cli > Nenhum cliente ou serial encontrado.')

#==================================================================
# 4) Downloads attachment files from GMAIL account
def baixar(request):
    # Dados de Login e DEFINICOES de VARIAVEIS
    # =========================================
    # definicao de seguranca do GOOGLE para aplicacoes MENOS seguras
    # https://www.google.com/settings/security/lesssecureapps

    # Something in lines of http://stackoverflow.com/questions/348630/how-can-i-download-all-emails-with-attachments-from-gmail
	# Make sure you have IMAP enabled in your gmail settings.
	# Right now it won't download same file name twice even if their contents are different.

	# ============================================================
	# https://gist.github.com/baali/2633554
	# Aplicação faz o download dos ANEXOS na conta do GMAIL
	# na pasta "peck" para a pasta "baixados" na raiz do diretorio atual
	# ============================================================

    #userName = raw_input('Enter your GMail username:')
    #passwd = getpass.getpass('Enter your password: ')
    userName = "ornellas.rodrigo@gmail.com"
    passwd = "adrianna3="
    pastaemail = "amply"
    detach_dir = os.path.join(settings.ROOTDIR, 'templates')      #diretorio local onde serão baixados os arquivos
    pastalocal = 'uploaded'                     # esta pasta não pode ter mais do que um diretorio e nem barra antes ou depois

    #print detach_dir
    #print str(os.path.join(detach_dir, pastalocal))
    #print os.listdir(detach_dir)
    if pastalocal not in os.listdir(detach_dir):
        os.mkdir(os.path.join(detach_dir, pastalocal))
        print ("Pasta > uploaded criada")
    else:
        print ("Pasta > uploaded EXISTENTE")

    # Realiza Login com os dados acima
    pecks = {} # variavel para enviar os dados para o template HTML
    down = []
    bad = []
    try:
        imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
        typ, accountDetails = imapSession.login(userName, passwd)
        if typ != 'OK':
            print ('ERRO 006: VIEW: baixar > Not able to sign in!')
            raise
#        else:
#            print 'Login ok'

        # PASTA especificada "peck" e emails NAO VISTOS ou > '(UNSEEN)' 'SUBJECT'
        imapSession.select(pastaemail)
        typ, data = imapSession.search(None, '(UNSEEN)')
        if typ != 'OK':
            print ('ERRO 007: VIEW: baixar > searching Inbox.')
            raise

        #print data
        #print type(data)
        if not data:
            print ('ERRO 012: VIEW: baixar > todos arquivos JÁ baixados.')
            raise

        for msgId in data[0].split():
            typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
            if typ != 'OK':
                print ('ERRO 008: VIEW: baixar > Error fetching mail.')
                raise

            emailBody = messageParts[0][1]
            mail = email.message_from_string(emailBody)
            #decode = email.header.decode_header(mail['Subject'])[0]
            #subject = unicode(decode[0])
            for part in mail.walk():
                if part.get_content_maintype() == 'multipart':
                    #print part.as_string()
                    continue

                if part.get('Content-Disposition') is None:
                    # print part.as_string()
                    continue

                fileName = part.get_filename()
                #fileExt = fileName.split(".")[-1]
                #print fileExt
                print (fileName)
                if bool(fileName):
                    filePath = os.path.join(detach_dir, pastalocal, fileName)
                    if not os.path.isfile(filePath): #and fileName.split(".")[-1] == "txt": # arquivos somente com extensao TXT
                        # download attachment > python how to download a file from gmail
                        # http://stackoverflow.com/questions/348630/how-can-i-download-all-emails-with-attachments-from-gmail
                        try:
                            fp = open(filePath, 'wb')
                            fp.write(part.get_payload(decode=True))
                            fp.close()
                            print ("DOWNLOADING " + msgId + " > " + fileName)
                            down.append(fileName)
                        except:
                            bad.append(fileName)
                            print ("ERRO 009: VIEW: baixar > no download possible.")
                            continue

        imapSession.close()
        imapSession.logout()

    except :
        print ('ERRO 010: VIEW: baixar > Not able to download all attachments.')

    pecks["down"] = down
    pecks["bad"] = bad
    context = {'pecks': pecks}
    template = 'peck/baixados.html'
    return render(request, template, context, content_type="text/html")

#==================================================================
# 5) View para apresentar arquivo PECK em formato texto
def vertxt(request, peckfile):
    content = peckfile
    return HttpResponse(content, content_type='text/plain')
    #html = "<html><body>content %s.</body></html>" % content
    #return HttpResponse(html, content_type='text/plain')

#==================================================================
# 6) List of clients
def l_clis(request):
    listao = {}
    listao ['pek'] = Peck.objects.all()
    listao ['maq'] = Machine.objects.all()
    listao ['mod'] = Modelo.objects.all()
    listao ['cli'] = Client.objects.all()
    listao ['ink'] = TTINTA_CHOICES

    context = {'listao': listao}
    template = 'peck/l_clientes.html'
    return render(request, template, context, content_type="text/html")

#==================================================================
# 7) List of Machines
def l_machine(request):
    listao = {}
    listao ['pek'] = Peck.objects.all()
    listao ['maq'] = Machine.objects.all()
    listao ['mod'] = Modelo.objects.all()
    listao ['cli'] = Client.objects.all()
    listao ['ink'] = TTINTA_CHOICES

    context = {'listao': listao}
    template = 'peck/l_maqs.html'
    return render(request, template, context, content_type="text/html")

#def l_maqs(request):
#    maq = Machine.objects.all()
#    template = 'peck/l_maqs.html'
#    context = {'maq': maq}
#    return render(request, template, context)    

#==================================================================
# 7b) Machines Details
def machine_details(request, maq_serial):
    peks = {}
    peks ['arr'] = Peck.objects.filter(pSerial=maq_serial)
    peks ['cli'] = Peck.objects.filter(pSerial=maq_serial).first()

    context = {'peks': peks}
    template = 'peck/maq_details.html'
    return render(request, template, context, content_type="text/html")


#==================================================================
# 8) List of Modelos
def l_mod(request):
    lista_modelos = Modelo.objects.all()
    context = {'lista_modelos': lista_modelos}
    template = 'peck/l_modelos.html'
    return render(request, template, context, content_type="text/html")

#==================================================================
# 9) List of Documents
def l_docs(request):
    documents = Peck.objects.all()
    template = 'peck/l_docs.html'
    context = {'documents': documents}
    return render(request, template, context, content_type="text/html")

#==================================================================
# 12) Detalhes do peck report selecionado
def detailPeck(request, peck_id):
    # d_pecks(request, newdoc.id, newdoc)
    # Pegando os valores no banco de dados
    # print('peck_id' + str(peck_id))
    # p = Peck.objects.all()
    # for i in p:
    #     print (i.pk)

    peck = Peck.objects.get(pk=int(peck_id))
    maq = Machine.objects.get(serial=peck.pSerial)

    # Como enviar dois objetos para a pagina HTML (template)
    # http://www.tangowithdjango.com/book/chapters/models_templates.html
    tohtml = {}
    tohtml ['pek'] = Peck.objects.get(pk=int(peck_id))
    tohtml ['mac'] = Machine.objects.get(serial=peck.pSerial)
    tohtml ['c'] = Client.objects.get(pk=maq.client.pk)
    # detalhe_peck ['doc'] = doc

    # Envio dos dados para a pagina HTML
    context = {'tohtml': tohtml}
    template = 'peck/d_peck.html'
    return render(request, template, context, content_type="text/html")


#==================================================================
# 13) list all peck reports
def l_pecks(request):
    arqs = {}
    lista_pecks = {}
    lista_pecks = Peck.objects.all()

    context = {'lista_pecks': lista_pecks}
    template = 'peck/l_pecks.html'
    return render(request, template, context, content_type="text/html")


# ============================================================================================
# 11a) Method CALLED by Report METHOD
def calscan(d_peck, d_maq, d_mod):
        # Calculos referentes ao motor SCAN
        # =================================
        dscan = {}
        # a) Tempo (dias) entre os dois ultimos PECK reports (difdays)
        difdays = (d_peck[0].data - d_peck[1].data).days

        # b) Tempo (horas) de uso do motor SCAN entre os dois ultimos PECK reports (difscan)
        difscan = (d_peck[0].scan - d_peck[1].scan)

        # c) Media de horas de uso do motor SCAN
        medscan = float(difscan) / float(difdays)

        # d) Porcentagem da vida util do motor SCAN
        percscan = str(round((float(d_peck[0].scan) / float(d_mod.scan)),3)*100)+"%"

        # e) Estimativa da PROXIMA troca do motor SCAN
        delta = (float(d_mod.scan) - float(d_peck[0].scan)) / medscan
        proxima = d_peck[0].data + timedelta(days=delta)

        # f) Estimativa de tempo até a proxima troca e horas de uso HOJE
        passou = (datetime.now().date()) - proxima
        qdias = ((datetime.now().date()) - d_peck[0].data).days
        scanhoje = d_peck[0].scan + (medscan * qdias)
        if passou.days < 0:
            obs = "> faltam " + str(int(fabs(passou.days))) + " dias para a proxima troca do motor"
        else:
            obs = "> passaram " + str(int(fabs(passou.days))) + " dias da data da troca do motor"


        # Construindo Lista > dconta
        dscan ["difdays"] = difdays
        dscan ["difscan"] = difscan
        dscan ["medscan"] = round(medscan,1)
        dscan ["percscan"] = percscan
        dscan ["proxima"] = proxima
        dscan ["obs"] = obs
        dscan ["scanhoje"] = round(scanhoje, 1)

        # Imprimindo os valores
#        print "difdays = " + str(difdays)
#        print "difscan = " + str(difscan)
#        print "media scan = " + str(medscan)
#        print "% scan = " + percscan
#        print "delta = " + str(delta)
#        print "proxima = " + str(proxima)
#        print "passou = " + str(passou)

        return dscan

# 11c) Method CALLED by Report Method
def calpump(d_peck, d_maq, d_mod):
        # Calculos referentes ao BOMBA/PUMP
        # =================================
        dpump = {}

        # a) Tempo (dias) entre os dois ultimos PUMP reports (difdays)
        difdays = (d_peck[0].data - d_peck[1].data).days

        # b) BOMBADAS de uso da PUMP entre os dois ultimos PECK reports (difpump)
        difpump = (d_peck[0].pump - d_peck[1].pump)

        # c) Media de BOMBADAS por dia
        medpump = float(difpump) / float(difdays)

        # d) Porcentagem da vida util da PUMP/BOMBA
        percpump = str(round((float(d_peck[0].pump) / float(d_mod.pump)),3)*100)+"%"

        # e) Estimativa da PROXIMA troca da PUMP
        delta = (float(d_mod.pump) - float(d_peck[0].pump)) / medpump
        proxima = d_peck[0].data + timedelta(days=delta)

        # f) Estimativa de tempo até a proxima troca e horas de uso HOJE
        passou = (datetime.now().date()) - proxima
        qdias = ((datetime.now().date()) - d_peck[0].data).days
        hoje = d_peck[0].pump + (medpump * qdias)
        if passou.days < 0:
            obs = "> faltam " + str(int(fabs(passou.days))) + " dias para a proxima troca do motor"
        else:
            obs = "> passaram " + str(int(fabs(passou.days))) + " dias da data da troca do motor"


        # Construindo Lista > dconta
        dpump ["difdays"] = difdays
        dpump ["difpump"] = difpump
        dpump ["medpump"] = round(medpump, 1)
        dpump ["percpump"] = percpump
        dpump ["proxima"] = proxima
        dpump ["obs"] = obs
        dpump ["hoje"] = round(hoje, 1)

        # Imprimindo os valores
#        print "difdays = " + str(difdays)
#        print "difscan = " + str(difscan)
#        print "media scan = " + str(medscan)
#        print "% scan = " + percscan
#        print "delta = " + str(delta)
#        print "proxima = " + str(proxima)
#        print "passou = " + str(passou)

        return dpump

# 11b) Method CALLED by Report Method
def calmaint(d_peck, d_maq, d_mod, difd):
        # Calculos referentes a LIMPEZA das CABECAS
        # =========================================

        # g) Array with the results to be RETURNED
        dmaint = {}

        # a) Tempo (dias) entre os dois ultimos reports (difdays)
        difdays = difd

        # b) VEZES que foram realizadas limpezas nas cabeças entre os dois ultimos reports
        diftime = (d_peck[0].limp - d_peck[1].limp)

        # c) Media de LIMPEZAS por semana
        media = (float(diftime) / float(difdays)) * 7

        # d) Tempo desde a ULTIMA limpeza das cabecas
        wlast = float((d_peck[0].ultima) / 7)
        if wlast <= 2.0:
            txt = "Boa regularidade ate 2 semanas"
        elif wlast > 2.0 and wlast <= 4.0:
            txt = "Não esqueça da limpeza. Mais de 2 semanas."
        elif wlast > 4.0 and wlast <= 8.0:
            txt = "Nenhuma limpeza a mais de 4 semanas"
        elif wlast > 8.0:
            txt = "Nenhuma limpeza a mais de 8 semanas"

        # h) last time the maintenance has been made
        tlast = d_peck[0].ultima

        # e) Estimativa da PROXIMA troca da PUMP
#        delta = (float(d_mod.pump) - float(d_peck[0].pump)) / medpump
#        proxima = d_peck[0].data + timedelta(days=delta)
#
#        # f) Estimativa de tempo até a proxima troca e horas de uso HOJE
#        passou = (datetime.now().date()) - proxima
#        qdias = ((datetime.now().date()) - d_peck[0].data).days
#        hoje = d_peck[0].pump + (medpump * qdias)
#        if passou.days < 0:
#            obs = "> faltam " + str(int(fabs(passou.days))) + " dias para a proxima troca do motor"
#        else:
#            obs = "> passaram " + str(int(fabs(passou.days))) + " dias da data da troca do motor"


        # Construindo Lista > dconta
        dmaint ["difdays"] = difdays
        dmaint ["diftime"] = diftime
        dmaint ["media"] = round(media)
        dmaint ["tlast"] = tlast
        dmaint ["txt"] = txt
 #       dmaint ["hoje"] = hoje

        # Imprimindo os valores
        print ("difdays = " + str(difdays))
        print ("diftime = " + str(diftime))
        print ("media = " + str(media))
        print ("txt = " + str(txt))
        print ("tlast = " + str(tlast))
        return dmaint



# 11) MAIN METHOD
def report(request, sall):

	# call to CALSCAN (11a) method
	# call to CALMAINT (11b) method
	# call to CALPUMP (11c) method

    # 1) Pegando os valores no banco de dados
    d_peck = Peck.objects.filter(serial=str(sall)).order_by('-data')[:2]
    d_maq = Machine.objects.get(serial=sall)

    # 2) Inicio dos Calculos
    detalhe_peck = {}

    # 3) Verifica se modelo da maquina existe na base de dados
    try:
        d_mod = Modelo.objects.get(modelo=d_peck.first().modelo)
        #print (str(d_mod))
    except:
        err = []
        err = {"mensagem" : 'ERRO 015: VIEW: report > Modelo da maquina AINDA não cadastrado na base de dados. FAVOR pedir ao admin CADASTRAR'}
        context = {'err': err}
        template = 'peck/d_pecks.html'
        return render(request, template, context, content_type="text/html")

    print ("report: " + str(len(d_peck)))
    if len(d_peck) > 1:
        difd = (d_peck[0].data - d_peck[1].data).days
        detalhe_peck ['pec2'] = d_peck[1]

        # Motor SCAN
        d_scan = {}
        d_scan = calscan(d_peck, d_maq, d_mod)
        detalhe_peck ['scan'] = d_scan

        # Pump / Tubulação
        d_pump = {}
        d_pump = calpump(d_peck, d_maq, d_mod)
        detalhe_peck ['pump'] = d_pump

        # Limpeza de Cabeca
        d_maint = {}
        d_maint = calmaint(d_peck, d_maq, d_mod, difd)
        detalhe_peck ['maint'] = d_maint


    # 3) Como enviar dois objetos para a pagina HTML (template)
    # http://www.tangowithdjango.com/book/chapters/models_templates.html
    # Amarrar os calculos a variavel DETALHE_PECK
    detalhe_peck ['pec1'] = d_peck.first()
    detalhe_peck ['mac'] = d_maq
    detalhe_peck ['mod'] = d_mod

    # 4) Envio dos dados para a pagina HTML
    context = {'detalhe_peck': detalhe_peck}
    template = 'peck/report.html'
    return render(request, template, context, content_type="text/html")


# --------------- PARSE do ARQUIVO PECK -------------------------------------------

# 10) Method CALLED by "sobe_arq" Method
def parsepk(filepath):

    # Open uploaded file
    fname = open(filepath, 'r')

    # cabeca = {'VS-640':'1','XJ-740':'6','RS-640':'4','SP-540i':'2','RE-640':'1', 'LEJ-640':'6', 'XC-540':'6', 'VS-540':'1', 'LEF-12':'3','VP-300i':'4',}

    # Init control VARIABLES
    sep1 = ":"
    rank = list()
    # rank.append(None)
    lin = 0
    hcount = 0
    heads = 0
    conta = 0
    controle = 14
    err = ""

    # return VARIABLES 1
    modelo = ""
    data = ""
    ink = ""
    firmware = ""
    serial = ""

    # return VARIABLES 2
    hfeed = ""
    hscan = ""
    tpump = ""
    hclean = ""
    tlimp = ""
    hwipe = ""
    botliq = ""
    batst = ""
    totlin = len(open(filepath).readlines(  ))
    # print '>>> totlin: ' + str(totlin)

    # loop through the file lines to extract the data
    for linha in fname:
        lin = lin + 1
        tst = linha.split(sep1)

        # 1
        # print conta
        if (linha.startswith("Model") or linha.startswith("MODEL") ) and conta < controle and modelo == "":
            modelo = tst[1].strip()
            # print (str(conta) + " > 1-modelo > " + modelo)
            conta = conta + 1

        # 2
        elif (linha.startswith("Version") or linha.startswith("VERSION") or linha.startswith("  MAIN") or linha.startswith("FirmwareVer") ) and conta < controle and firmware == "":
            firmware = tst[1].strip()
            conta = conta + 1
            # print (str(conta) + " > 2-versao > " + firmware)

        # 3
        elif ( linha.startswith("Serial N") or linha.startswith("SERIAL N") ) and conta < controle and serial == "":
            serial = tst[1].strip()
            conta = conta + 1
            # print (str(conta) + " > 3-serial > " + serial)

        # 4
        elif ( linha.startswith("CurrentDate") or linha.startswith("Date") or linha.startswith("DATE") or linha.startswith("  DATE") ) and conta < controle and data == "":
            tst = tst[1].split(' ')
            for d in tst:
                if d.find("/") > 0:
                    dt = d.strip()
                    data = dt.replace("/", "-")
                    data = datetime.strptime(data, '%Y-%m-%d').date()
            conta = conta + 1
            # print (str(conta) + " > 4-data > " + str(data))

        # 5
        elif ( linha.startswith("InkMode") or linha.startswith("Ink type") or linha.startswith("INK TYPE") or linha.startswith("  INK TYPE") ) and conta < controle and ink == "":
            ink = tst[1].strip()
            conta = conta + 1
            # print (str(conta) + " > 5-tinta > " + ink)

        # 6
        elif ( linha.startswith("HeadRank") or linha.startswith("Head rank") or linha.startswith("HEAD RANK") or linha.startswith("  HEAD RANK") ) and conta < controle and heads == 0:
            tst = tst[1].strip()
            rank.append(tst)
            try:
                h = Modelo.objects.get(model=modelo)
                heads = int(h.heads)
                conta = conta + 1
                hcount = hcount + 1
            except:
                print ("ERRO 002: VIEW: dados_ini > Essa maquina NAO esta cadastrada na tabela MODELO.")

        # 7
        # elif heads >= 1 and conta < controle:
        #     if heads > 1:
        #         hcount = hcount + 1
        #         tst = tst[1].strip()
        #         rank.append(tst)
        #         conta = conta + 1

        #8
        elif (linha.startswith("Motor feed") or linha.startswith("  MOTOR FEED") ) and conta < controle and hfeed == "":
            tst = tst[1].split("/")
            if "," in tst[0]:
                hfeed = tst[0].strip().replace(",", "")
            else:
                hfeed = tst[0].strip()
            conta = conta + 1
            # print (str(conta) + " > 8-hfeed > " + hfeed)

        #9
        elif ( linha.startswith("Motor scan") or linha.startswith("  MOTOR SCAN") )and conta < controle and hscan == "":
            tst = tst[1].split("/")
            hscan = tst[0].strip().replace(",", "")
            conta = conta + 1
            # print (str(conta) + " > 9-hscan > " + hscan)

        #10
        elif (linha.startswith("Pump Times ") or linha.startswith("  PUMP TIMES") ) and conta < controle and tpump == "":
            # pump = True
            tst = tst[1].split("/")
            tpump = tst[0].strip().replace(",", "")
            conta = conta + 1
            # print (str(conta) + " > 10-tpump > " + tpump)

        #11
        elif (linha.startswith("Maintenance Count") or linha.startswith("EnhancedMaintenance c") or linha.startswith("  MAINTENACE COUNT") ) and conta < controle and hclean == "":
            hclean = tst[1].strip().split(" ")[0]
            # print hclean
            conta = conta + 1
            # print (str(conta) + " > 11-hclean > " + hclean)

        # TESTING
        elif ( linha.startswith("Total time") or linha.startswith("ElapsedSinceManualCl") or linha.startswith("  TOTAL TIME")) and conta < controle and tlimp == ""  :
            # print "linha> " + linha
            # print "conta> " + str(conta)
            # print "hlimp> " + str(tlimp)
            # print "A> " + str(tst)
            # print "B> " + str(tst[1])
            # print "C> " + str(tst[1].strip())
            # print "D> " + str(tst[1].strip().split(" "))
            # print "E> " + str(tst[1].strip().split(" ")[0])
            tlimp = tst[1].strip().split(" ")[0] # .replace(",", "")
            conta = conta + 1
            # print (str(conta) + " > 12-hlimp > " + hlimp)

        #13
        elif ( linha.startswith("Wiping count") or linha.startswith("  WIPING COUNT") or re.findall('\\bWipe\\b', linha) ) and conta < controle and hwipe == "":
            tst = tst[1].strip().split(" ")
            # print ('>>>>>>>' + str(tst))
            # print linha
            if "," in tst[0]:
                hwipe = tst[0].replace(",", "")
            else:
                hwipe = tst[0]

            conta = conta + 1
            # print (str(conta) + " > 13-hwipe > " + hwipe)

        #14
        elif (linha.startswith("DrainLiq") or linha.startswith("Drain liq") or linha.startswith("  DRAIN LIQ") ) and conta < controle and botliq == "":
            tst = tst[1].strip().split(" ")
            # print ('>>>>>>>' + str(tst))
            # print linha
            if "." in tst[0]:
                botliq = tst[0].strip().split(".")[0]
            else:
                botliq = tst[0]
            conta = conta + 1
            # print (str(conta) + " > 14-botliq > " + botliq)

        #15
        elif (lin == totlin - 2 or linha.startswith("Battery") or linha.startswith("  BATTERY") ) and conta < controle and batst == "":
            if modelo == "BN-20":
                batst = "No Bat"
            else:
                batst = tst[1].strip()
            conta = conta + 1
            # print (str(conta) + " > 15-batst > " + batst)


        elif conta >= controle:
            fname.close()
            print ('<0  modelo > ' +  str(modelo))
            print ('<1  firmware > ' +  str(firmware))
            print ('<2  serial > ' +  str(serial))
            print ('<3  data > ' +  str(data))
            print ('<4  ink > ' +  str(ink))
            print ('<5  heads > ' +  str(heads))
            print ('<6  rank > ' +  str(rank))
            print ('<7  hfeed > ' +  str(hfeed))
            print ('<8  hscan > ' +  str(hscan))
            print ('<9  tpump > ' +  str(tpump))
            print ('<10 hclean > ' +  str(hclean))
            print ('<11 hlimp > ' +  str(tlimp))
            print ('<12 hwipe > ' +  str(hwipe))
            print ('<13 botliq > ' +  str(botliq))
            print ('<14 batst > ' +  str(batst))
            print ('<15 err > ' +  str(err))
            print ('<16 file > ' +  str(filepath))


            if (modelo != "" and firmware != "" and serial != "" and data != "" and ink != "" and hfeed != "" and hscan != "" and tpump != "" and hclean != "" and tlimp != "" and hwipe != "" and botliq != "" and batst != ""):
                    err = ""
                    return (modelo, firmware, serial, data, ink, heads, rank, hfeed, hscan, tpump, hclean, tlimp, hwipe, botliq, batst, err)
            else:
                    err = "ERRO 002: VIEW: parsepk > Durante o PARSING do PECK foi encontrado um erro."
                    return (modelo, firmware, serial, data, ink, heads, rank, hfeed, hscan, tpump, hclean, tlimp, hwipe, botliq, batst, err)

# 10) MAIN METHOD: Upload PECK file to the Database


def sobe_arq(request):

    # variables
    form = ""
    myfile = ""
    mod = ""
    res = []
    err = []
    context = []
    template = ""
    tohtml = {}

    # (B-5)
    if request.method == 'POST' and request.FILES['file']:
        form = PeckForm(request.POST, request.FILES)
        myfile = str(settings.BASE_DIR) + '/peck_files/' + str(request.FILES['file'])
        res = parsepk(myfile)
        print ("test>001")

        # check if machine serial exists
        #     if yes get machine_id
        #     if no create machine
        #         check if client exits
        #             if yes get client_id
        #             if no create client
        #                   provide client name only

        #  Test if MACHINE serial number is already in the DB

        # (A-9)
        try:
            # if positive, get machine db id
            machine = Machine.objects.get(serial=res[2])
            print (type(machine))
            print ("test>002")

        # (A-9)
        except ObjectDoesNotExist:
            print ("ERRO 101: VIEW: sobe_arq > Machine does not exist. Attempting to create a new Machine Object")

            # (C-13)
            try:
                # GET client name from FILE NAME
                client_name = str(request.FILES['file']).split('.')[0]
                print ("test>003")

            # (C-13)
            except:
                print ("ERRO 102: VIEW: sobe_arq > Unable to get CLIENT NAME from file name.")
            # (C-13)
            else:
                # if negative CREATE client object
                # (D-17)
                try:
                    print (str(client_name))
                    if (Client.objects.get(company=client_name)):
                        cli = Client.objects.get(company=client_name)
                        print ("test>004a")
                # (D-17)
                except:
                    # DoesNotExist
                    print ("ERRO 103: VIEW: sobe_arq > Unable to FIND the CLIENT.")
                    cli = Client(company=client_name)
                    cli.save()
                    print (cli)
                # (D-17)
                finally:
                    try:
                        mod = Modelo.objects.get(model=res[0])
                        print ("test>005")
                    except:
                        print ("ERRO 104: VIEW: sobe_arq > Unable to get MODEL from Database.")
                    else:
                        try:
                            machine = Machine(client=cli, model=mod, serial=res[2])
                            machine.save()
                            print ("test>009")
                        except:
                            print ("ERRO 107: VIEW: sobe_arq > Unable to create new MACHINE object.")

        # (A-9)
        finally:
            mod = Modelo.objects.get(model=res[0])
            print (mod)
            print (machine)
            try:
                print ("test>006")
                newpeck = Peck(
                    model=mod,
                    machine=machine,
                    firmware=res[1],
                    pSerial=res[2],
                    pModelo=res[0],
                    createDate=res[3],
                    ink=res[4],
                    bat=res[14],
                    feed=res[7],
                    scan=res[8],
                    pump=res[9],
                    limp=res[11],
                    clean=res[10],
                    wipe=res[12],
                    liq=res[13],
                    filepath=myfile )

                # Salvando dados na base de dados            
                newpeck.save()
                tohtml['pek'] = newpeck
                tohtml['c'] = cli

            except:
                print ("test>007")
                err = {"message" : "ERRO 105: VIEW: sobe_arq > Este arquivo PECK ja foi armazenado no banco de dados. Ou nao foi possivel a criacao do Objeto PECK."}
                context = {'err': err}
                template = 'peck/d_pecks.html'
                return render(request, template, context, content_type="text/html")

            else:
                # Definindo dados para RENDER
                print ("test>008")
                context = {'tohtml': tohtml }
                template = 'peck/d_pecks.html'
                return render(request, template, context, content_type="text/html")

    # (B-5)
    else:
        print ("test>009")
        err = {"message" : "ERRO 106: VIEW: sobe_arq > No file path was provided. Or no file selected."}
        context = {'err': err}
        template = 'peck/index.html'
        return render(request, template, context, content_type="text/html")


def getgraph(request, *args, **kwargs):
    labels = ["January", "February", "March", "April", "May", "June", "July"];
    p = Peck.objects.all()

    graph = {}
    setPeck = set()
    for peck in p:
        setPeck.add(peck.pModelo)

    for model in setPeck:
        graph[model] = Peck.objects.filter(pModelo=model).count()

    print (str(graph))

    # err = {"message" : "Graph executed."}
    # context = {'graph': graph}
    # template = 'peck/index.html'
    # return render(request, template, context, content_type="text/html")

    data = {
        "labels": setPeck,
        "quantity": len(setPeck),
    }
    return JsonResponse(graph)
