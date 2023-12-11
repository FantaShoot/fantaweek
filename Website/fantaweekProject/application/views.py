# File:         views.py
# Descrizione: questo file contiene le view dell'applicazione

# --- Imports ---
import shutil
import pandas as pd
import numpy as np
from django.db.models import Q
from django.urls import reverse
from application.models import *
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.models import User, Group
from dateutil.relativedelta import relativedelta, SU
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout



# --- Views ---


# GENERAL VIEWS ---------------------------------------------------------------

# view: index_view
# descrizione: pagina principale del sito
# funzionamento: 
# - Se l'utente non è loggato, viene mostrata la pagina di login
# - Se l'utente è loggato ed è un admin vedrà la pagina per gli admin
# - Se l'utente è loggato ed è un agenzia vedrà la pagina per le agenzie
# - Se l'utente è loggato ed è un utente vedrà la pagina per gli utenti
def index_view(request):
    # context variables
    agenzie = None
    bilancio = None
    giocatori = None
    portieri = None
    difensori = None
    centrocampisti = None
    attaccanti = None
    transazioni = None
    tornei = None
    tornei_precedenti = None
    iscrizioni = None
    squadre = None
    squadre_attuali = None
    # retrieve settimana from db/Calendario
    settimana = None
    # retrieve messages from url if None, set to None
    error_message = request.GET.get('error_message')
    success_message = request.GET.get('success_message')
    if error_message == 'None':
        error_message = None
    if success_message == 'None':
        success_message = None

    
    # authentication
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        # if the user is not None
        if user is not None:
            # if user is in group Agenzia and is blocked
            if user.groups.filter(name='Agenzia').count() != 0 and user.check_password('blocked'):
                error_message = 'agenzia sospesa'        
            # if user is in group Giocatore and its Agency is blocked
            elif user.groups.filter(name='Giocatore').count() != 0:
                agenzia = Giocatore.objects.get(username=username).agenzia
                if User.objects.get(username=agenzia).check_password('blocked'):
                    error_message = 'agenzia sospesa'
                else:
                    login(request, user)
            else:
                login(request, user)
        else:
            error_message = 'credenziali errate'
      
    # se l'utente è loggato
    if request.user.is_authenticated:
        # se è admin
        if request.user.is_superuser:
            # prendo tutti gli utenti con gruppo Agenzia
            agenzie = User.objects.filter(groups__name='Agenzia')

        # se è un agenzia
        elif request.user.groups.filter(name='Agenzia').count() != 0:
            # prendo tutti gli utenti con gruppo Giocatore e la sua agenzia
            giocatori = Giocatore.objects.filter(agenzia=request.user.username)
            # recupera dal file .csv "db/azienda" le transazioni dei giocatori associati all'agenzia to numpy array
            transazioni = pd.DataFrame(columns=['date', 'giocatore', 'amount', 'description']).to_numpy()
            for giocatore in giocatori:
                # prendo tutti i movimenti del giocatore
                movimenti = pd.read_csv(f'db/{giocatore.agenzia}/{giocatore.username}.csv')
                # aggiungo la colonna 'giocatore' e rioordino le colonne
                movimenti['giocatore'] = giocatore.username
                movimenti = movimenti[['date', 'giocatore', 'amount', 'description']]
                # se non è vuoto, converto in numpy array e concateno
                if movimenti.shape[0] != 0:
                    movimenti = movimenti.to_numpy()
                    transazioni = np.concatenate((transazioni, movimenti), axis=0)

            # se non è vuoto lo converto in dataframe e converto in html con spaziatura
            if transazioni.shape[0] != 0:
                transazioni = pd.DataFrame(transazioni, columns=['date', 'giocatore', 'amount', 'description'])
                # ordino per data
                transazioni = transazioni.sort_values(by=['date'], ascending=False)
                transazioni = transazioni.to_html(index=False, justify='center', classes='table table-striped table-bordered table-hover table-sm table-responsive')

        # se è un giocatore
        elif request.user.groups.filter(name='Giocatore').count() != 0:
            # prendo il suo bilancio
            bilancio = Giocatore.objects.get(username=request.user.username).bilancio
            # prendo i suoi movimenti
            agenzia = Giocatore.objects.get(username=request.user.username).agenzia
            transazioni = pd.read_csv(f'db/{agenzia}/{request.user.username}.csv')
            # se non è vuoto lo converto in dataframe e converto in html con spaziatura
            if transazioni.shape[0] != 0:
                transazioni = pd.DataFrame(transazioni, columns=['date', 'amount', 'description'])
                # ordino per data
                transazioni = transazioni.sort_values(by=['date'], ascending=False)
                transazioni = transazioni.to_html(index=False, justify='center', classes='table table-striped table-bordered table-hover table-sm table-responsive')
            portieri = Calciatore.objects.filter(ruolo='P').order_by('-mediaFV')
            difensori = Calciatore.objects.filter(ruolo='D').order_by('-mediaFV')
            centrocampisti = Calciatore.objects.filter(ruolo='C').order_by('-mediaFV')
            attaccanti = Calciatore.objects.filter(ruolo='A').order_by('-mediaFV')
            # prendo le squadre del giocatore
            squadre = Squadra.objects.filter(utente=request.user)
            # prendo la settimana corrispondente alla data odierna
            calendario = pd.read_csv(f'db/Calendario.csv')
            calendario['Data'] = pd.to_datetime(calendario['Data'], format='%d/%m/%y')
            # Prendo la domenica della settimana corrente
            sunday = timezone.localdate() + relativedelta(weekday=SU(0))
            # Find the row where the 'Data' column is equal to the current Sunday
            settimana = calendario.loc[calendario['Data'].dt.date == sunday]['Partite'].values[0]
            settimana = settimana.split(';')
            # prendo le classifiche dei tornei precedenti 15 giorni
            tornei_precedenti = Torneo.objects.filter(
                Q(dataInizio__gt=timezone.now() - timezone.timedelta(days=15)) & Q(dataFine__gt=timezone.now() - timezone.timedelta(days=15)) & Q(concluso=True)
            )
            # prendo le squadre attualmente registrabili
            squadre_attuali = Squadra.objects.filter(utente=request.user)
                    
            # prendo i primi 3 punteggi
            for torneo in tornei_precedenti:
                classifica = Iscrizione.objects.filter(torneo=torneo).order_by('-punteggio')[:3]
                # per ogni punteggio prendo il punteggio dei primi 3 giocatori
                if classifica.count() == 0:
                    pass
                elif classifica.count() == 1:
                    torneo.p1 = classifica[0].punteggio
                    torneo.p1n = classifica[0].squadra
                    torneo.p1v = round(torneo.montepremi * 0.5, 2)
                elif classifica.count() == 2:
                    torneo.p1 = classifica[0].punteggio
                    torneo.p1n = classifica[0].squadra
                    torneo.p1v = round(torneo.montepremi * 0.5, 2)
                    torneo.p2 = classifica[1].punteggio
                    torneo.p2n = classifica[1].squadra
                    torneo.p2v = round(torneo.montepremi * 0.25, 2)
                else:
                    torneo.p1 = classifica[0].punteggio
                    torneo.p1n = classifica[0].squadra
                    torneo.p1v = round(torneo.montepremi * 0.5, 2)
                    torneo.p2 = classifica[1].punteggio
                    torneo.p2n = classifica[1].squadra
                    torneo.p2v = round(torneo.montepremi * 0.25, 2)
                    torneo.p3 = classifica[2].punteggio
                    torneo.p3n = classifica[2].squadra
                    torneo.p3v = round(torneo.montepremi * 0.15, 2)

    # prendo i tornei che sono disponibili data di oggi deve essere compresa tra dataInizio e dataFine; il torneo non deve essere concluso
    tornei = Torneo.objects.filter(
        Q(dataInizio__lte=timezone.localdate()) & Q(dataFine__gte=timezone.localdate()) & Q(concluso=False)
    )
    # prendo i tornei attuali che non sono conclusi la data di oggi deve essere compresa tra dataInizio e dataInizio + 7 giorni e il torneo non deve essere concluso
    t_tornei = Torneo.objects.filter(
        Q(dataInizio__lte=timezone.localdate() + timezone.timedelta(days=7)) & Q(dataInizio__gte=timezone.localdate()) & Q(concluso=False)
    )
    # prendo le iscrizioni dei tornei attuali
    iscrizioni = Iscrizione.objects.filter(torneo__in=t_tornei)
    # per ogni iscrizione aggiungo modulo e giocatori
    for iscrizione in iscrizioni:
        sq = Squadra.objects.filter(nome=iscrizione.squadra, utente=iscrizione.utente)
        print(sq)
        if sq.count() == 1:
            iscrizione.ordine = sq[0].ordine
            iscrizione.g1 = sq[0].g1
            iscrizione.g2 = sq[0].g2
            iscrizione.g3 = sq[0].g3
            iscrizione.g4 = sq[0].g4
            iscrizione.g5 = sq[0].g5
            iscrizione.g6 = sq[0].g6
            iscrizione.g7 = sq[0].g7
            iscrizione.g8 = sq[0].g8
            iscrizione.g9 = sq[0].g9
            iscrizione.g10 = sq[0].g10
            iscrizione.g11 = sq[0].g11    
        tn = Torneo.objects.get(ID=iscrizione.torneo)
        iscrizione.quota = tn.quota
    # aggiungo la quantità di squadre iscritte al torneo
    for torneo in tornei:
        torneo.iscritti = Iscrizione.objects.filter(torneo=torneo).count()

    context = {
        'agenzie': agenzie,
        'bilancio': bilancio,
        'giocatori': giocatori,
        'transazioni': transazioni,
        'portieri': portieri,
        'difensori': difensori,
        'centrocampisti': centrocampisti,
        'attaccanti': attaccanti,
        'tornei': tornei,
        'tornei_precedenti': tornei_precedenti,
        'iscrizioni': iscrizioni,
        'squadre': squadre,
        'squadre_attuali': squadre_attuali,
        'settimana': settimana,
        'error_message': error_message,
        'success_message': success_message,
    }

    return render(request, 'index.html', context=context)

# action: logout
# descrizione: submit al form di logout
@login_required
def logout_view(request):
    logout(request)
    return redirect('index')


# ADMIN VIEWS -----------------------------------------------------------------

# action: upload_file
# descrizione: submit al form di upload file (solo admin)
# funzionamento: controlla che il file sia un xlsx, 
# se il file è nominato 'statistiche.xlsx' sovrascrive i calciatori,
# se il file è nominato 'voti.xlsx' sovrascrive i voti,
@login_required
def upload_file_view(request):
    error_message = None
    success_message = None
    # se non è loggato o non è admin, non può usare questa funzione
    if not request.user.is_authenticated or request.user.is_superuser == False:
        print("non sei loggato o non sei un Admin")
        return redirect('index')
    
    else:
        if request.method == 'POST':
            file = request.FILES['file']
            print(file.name)
            # Se il file è chiamato 'Calciatori.csv' sovrascrivo i calciatori
            if file.name == 'Calciatori.csv':
                # salvo il file nella cartella db
                with open('db/Calciatori.csv', 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                # aggiorno i calciatori
                for index, row in pd.read_csv('db/Calciatori.csv').iterrows():
                    # se il calciatore non esiste, lo creo
                    if Calciatore.objects.filter(cognome=row['Nome']).count() == 0:
                        Calciatore.objects.create(cognome=row['Nome'], squadra=row['Squadra'], ruolo=row['R'], mediaFV=row['Fm'], punteggio=row['Punteggio'])
                    # se il calciatore esiste, lo aggiorno
                    elif Calciatore.objects.filter(cognome=row['Nome']).count() == 1:
                        calciatore = Calciatore.objects.get(cognome=row['Nome'])
                        calciatore.squadra = row['Squadra']
                        calciatore.ruolo = row['R']
                        calciatore.mediaFV = row['Fm']
                        calciatore.punteggio = row['Punteggio']
                        calciatore.save()
                    # se il Calciatore non esiste nella lista, lo elimino
                    else:
                        Calciatore.objects.filter(cognome=row['Nome']).delete()
                # ottengo la data inizio e fine dei prossimi tornei
                data_inizio = request.POST.get('start')
                data_fine = request.POST.get('end') 
                # calcolo della settimana precedente
                data_inizio_p = pd.to_datetime(data_inizio) - pd.Timedelta(days=7)
                data_fine_p = pd.to_datetime(data_fine) - pd.Timedelta(days=7)
                # concludo i tornei della settimana precedente che si trovano tra data_inizio_p e data_fine_p
                tornei = Torneo.objects.filter(dataInizio__gte=data_inizio_p, dataFine__lte=data_fine_p)
                for torneo in tornei:
                    torneo.concludi()
                # elimino tutte le squadre dopo 15 giorni
                iscrizioni = Iscrizione.objects.filter(torneo__in=tornei)
                for iscrizione in iscrizioni:
                    if Torneo.objects.get(ID=iscrizione.torneo).dataFine < timezone.now().date() - timezone.timedelta(days=15):
                        Squadra.objects.filter(nome=iscrizione.squadra).delete()             

                
                # creo nuovi tornei con le date se non esistono
                if Torneo.objects.filter(dataInizio=data_inizio, dataFine=data_fine).count() == 0:
                    Torneo.objects.create(dataInizio=data_inizio, dataFine=data_fine, quota=1)
                    Torneo.objects.create(dataInizio=data_inizio, dataFine=data_fine, quota=2.5)
                    Torneo.objects.create(dataInizio=data_inizio, dataFine=data_fine, quota=5)
                
                success_message = "calciatori aggiornati, tornei precedenti conlcusi e 3 nuovi tornei creati"

                
            else:
                error_message = "file non valido"
              
        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')

# action: download_db
# descrizione: submit al form di download db (solo admin)
# funzionamento: crea un file csv 'resoconto.csv' contenente tutte le modifiche nel corso del tempo indicato
# nella cartella db, crea un file .zip con la cartella db e lo scarica
@login_required
def download_db_view(request):
    # se non è loggato o non è admin, non può usare questa funzione
    if not request.user.is_authenticated or request.user.is_superuser == False:
        print("non sei loggato o non sei un Admin")
        return redirect('index')
    
    else:
        if request.method == 'POST':
            # prendo il tempo
            timestart = request.POST.get('start')
            timeend = request.POST.get('end')
            # creo il file csv nella cartella db
            with open('db/resoconto.csv', 'w') as f:
                f.write('data,username,agenzia,amount,description' + '\n')
                # prendo tutti i giocatori
                giocatori = Giocatore.objects.all()
                # per ogni giocatore
                for giocatore in giocatori:
                    # prendo tutti i movimenti del giocatore
                    movimenti = pd.read_csv(f'db/{giocatore.agenzia}/{giocatore.username}.csv')
                    # per ogni movimento
                    for index, movimento in movimenti.iterrows():
                        # se il movimento è compreso nel tempo selezionato
                        if movimento['date'] >= timestart and movimento['date'] <= timeend:
                            # scrivo il movimento nel file csv
                            f.write(f"{movimento['date']},{giocatore.username},{giocatore.agenzia},{movimento['amount']},{movimento['description']}" + '\n')

            # creo il file zip
            shutil.make_archive('db', 'zip', 'db')
            # scarico il file zip
            with open('db.zip', 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename=db.zip'
                return response

        return redirect('index')

# action: add_agency
# descrizione: submit al form di aggiunta agenzia (solo admin)
@login_required
def add_agency_view(request):
    # se non è loggato o non è admin, non può aggiungere agenzie
    if not request.user.is_authenticated or request.user.is_superuser == False: 
        print("non sei loggato o non sei un Admin")
        return redirect('index')
    
    else:
        error_message = None
        success_message = None
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)

        # se l'agenzia non esiste già, la crea
        if User.objects.filter(username=username).count() == 0:
            Agenzia.objects.create(nome=username)
            # oggetto user
            user = User.objects.create_user(username=username, password=password)
            user.save()
            # aggiungo user al gruppo Agenzia
            group = Group.objects.get(name='Agenzia')
            group.user_set.add(user)
            success_message = "agenzia aggiunta"
        else:
            error_message = "username gia' esistente"

        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')
    
@login_required
# action: modify_agency
# descrizione: submit al form di modifica agenzia (solo admin)
def modify_agency_view(request):
    # se non è loggato o non è admin, non può modificare agenzie
    if not request.user.is_authenticated or request.user.is_superuser == False:
        print("non sei loggato o non sei un Admin")
        return redirect('index')
    
    else:
        error_message = None
        success_message = None
        # prendi l'agenzia dal form
        username = request.POST.get('agenzia')
        password = request.POST.get('password')
        print(username)
        print(password)
        # se l'agenzia esiste, modifica la password dell'utente associato
        if User.objects.filter(username=username).count() != 0:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            success_message = "agenzia modificata"
        else:
            error_message = "agenzia non esistente"

        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')

# action: block_agency
# descrizione: submit al form di blocco agenzia (solo admin)
@login_required
def block_agency_view(request):
    # se non è loggato o non è admin, non può bloccare agenzie
    if not request.user.is_authenticated or request.user.is_superuser == False:
        print("non sei loggato o non sei un Admin")
        return redirect('index')
    
    else:
        error_message = None
        success_message = None
        # prendi l'agenzia dal form
        username = request.POST.get('agenzia')
        print(username)
        # se l'agenzia esiste, la blocca
        if User.objects.filter(username=username).count() != 0:
            agenzia = Agenzia.objects.get(nome=username)
            agenzia.block()
            success_message = "agenzia bloccata"
        else:
            error_message = "agenzia non esistente"
            
        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')


# AGENCY VIEWS ----------------------------------------------------------------

# action: add_user
# descrizione: submit al form di aggiunta utente (solo agenzia)
@login_required
def add_player_view(request):
    # se non è loggato o non è un agenzia, non può aggiungere giocatori
    if not request.user.is_authenticated or request.user.groups.filter(name='Agenzia').count() == 0:
        print("non sei loggato o non sei un agenzia")
        return redirect('index')
    
    else:
        success_message = None
        error_message = None
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)

        # se l'utente non esiste già, lo crea
        if User.objects.filter(username=username).count() == 0:
            Giocatore.objects.create(username=username, bilancio=0, agenzia=request.user)

            # oggetto user
            user = User.objects.create_user(username=username, password=password)
            user.save()
            # aggiungo user al gruppo Giocatore
            group = Group.objects.get(name='Giocatore')
            group.user_set.add(user)
            success_message = "giocatore aggiunto"
        else:      
            error_message = "username gia' esistente"
            

        # redirect to index with parameters
        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')

# action: modify_user
# descrizione: submit al form di modifica utente (solo agenzia)
@login_required
def modify_player_view(request):
    # se non è loggato o non è un agenzia, non può modificare giocatori
    if not request.user.is_authenticated or request.user.groups.filter(name='Agenzia').count() == 0:
        print("non sei loggato o non sei un agenzia")
        return redirect('index')
    
    else:
        giocatori = Giocatore.objects.filter(agenzia=request.user)
        error_message = None
        success_message = None

        username = request.POST.get('giocatore')
        password = request.POST.get('password')
        print(username)
        print(password)

        # se l'utente esiste, modifica la password dell'utente associato
        if User.objects.filter(username=username).count() != 0:
            user = User.objects.get(username=username)

            # se la password è vuota, non la modifica
            if password != '':
                user.set_password(password)
                user.save()
                success_message = "giocatore modificato"

            # se addbilancio è vuoto, non fa nulla
            if request.POST.get('addbilancio') != '':
                amount = float(request.POST.get('addbilancio'))
                description = "ricarica effettuata dall'agenzia"
                giocatore = Giocatore.objects.get(username=username)
                giocatore.add_bilancio(amount, description)
                success_message = "Ricarica effettuata"

            # se removebilancio è vuoto, non fa nulla
            if request.POST.get('removebilancio') != '':
                amount = float(request.POST.get('removebilancio'))
                giocatore = Giocatore.objects.get(username=username)
                # se l'amount è maggiore del bilancio, non fa nulla
                if amount > giocatore.bilancio:
                    error_message = "Bilancio non sufficiente, bilancio attuale: " + str(giocatore.bilancio)
                else:
                    description = "Prelievo effettuato dall'agenzia"
                    success_message = "Prelievo effettuato"
                    giocatore.remove_bilancio(amount, description)
        else:
            error_message = "giocatore non esistente"
    
        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')
    

# PLAYER VIEWS ----------------------------------------------------------------

# action: create_team
# descrizione: submit al form di creazione squadra (solo giocatore)
@login_required
def create_team_view(request):
    # se non è loggato o non è un giocatore, non può creare squadre
    if not request.user.is_authenticated or request.user.groups.filter(name='Giocatore').count() == 0:
        print("non sei loggato o non sei un giocatore")
        return redirect('index')
    
    else:
        error_message = None
        success_message = None

        # prendo i calciatori dal form
        nome = request.POST.get('nome')
        portiere = request.POST.get('portiere')
        difensore1 = request.POST.get('difensore1')
        difensore2 = request.POST.get('difensore2')
        difensore3 = request.POST.get('difensore3')
        difensore4 = request.POST.get('difensore4')
        difensore5 = request.POST.get('difensore5')
        centrocampista1 = request.POST.get('centrocampista1')
        centrocampista2 = request.POST.get('centrocampista2')
        centrocampista3 = request.POST.get('centrocampista3')
        centrocampista4 = request.POST.get('centrocampista4')
        centrocampista5 = request.POST.get('centrocampista5')
        attaccante1 = request.POST.get('attaccante1')
        attaccante2 = request.POST.get('attaccante2')
        attaccante3 = request.POST.get('attaccante3')
        modulo = request.POST.get('modulo')
        print(modulo)

        # se l'utente non ha un'altra squadra, identica a quella che sta creando, la crea
        if Squadra.objects.filter(nome=nome, utente=request.user).count() == 0:
            # switch per il modulo
            if modulo == '3-4-3':
                g1 = portiere
                g2 = difensore1
                g3 = difensore2
                g4 = difensore3
                g5 = centrocampista1
                g6 = centrocampista2
                g7 = centrocampista3
                g8 = centrocampista4
                g9 = attaccante1
                g10 = attaccante2
                g11 = attaccante3
            elif modulo == '3-5-2':
                g1 = portiere
                g2 = difensore1
                g3 = difensore2
                g4 = difensore3
                g5 = centrocampista1
                g6 = centrocampista2
                g7 = centrocampista3
                g8 = centrocampista4
                g9 = centrocampista5
                g10 = attaccante1
                g11 = attaccante2
            elif modulo == '4-3-3':
                g1 = portiere
                g2 = difensore1
                g3 = difensore2
                g4 = difensore3
                g5 = difensore4
                g6 = centrocampista1
                g7 = centrocampista2
                g8 = centrocampista3
                g9 = attaccante1
                g10 = attaccante2
                g11 = attaccante3
            elif modulo == '4-4-2':
                g1 = portiere
                g2 = difensore1
                g3 = difensore2
                g4 = difensore3
                g5 = difensore4
                g6 = centrocampista1
                g7 = centrocampista2
                g8 = centrocampista3
                g9 = centrocampista4
                g10 = attaccante1
                g11 = attaccante2
            elif modulo == '4-5-1':
                g1 = portiere
                g2 = difensore1
                g3 = difensore2
                g4 = difensore3
                g5 = difensore4
                g6 = centrocampista1
                g7 = centrocampista2
                g8 = centrocampista3
                g9 = centrocampista4
                g10 = centrocampista5
                g11 = attaccante1
            elif modulo == '5-3-2':
                g1 = portiere
                g2 = difensore1
                g3 = difensore2
                g4 = difensore3
                g5 = difensore4
                g6 = difensore5
                g7 = centrocampista1
                g8 = centrocampista2
                g9 = centrocampista3
                g10 = attaccante1
                g11 = attaccante2
            elif modulo == '5-4-1':
                g1 = portiere
                g2 = difensore1
                g3 = difensore2
                g4 = difensore3
                g5 = difensore4
                g6 = difensore5
                g7 = centrocampista1
                g8 = centrocampista2
                g9 = centrocampista3
                g10 = centrocampista4
                g11 = attaccante1
            else:
                error_message = "modulo non valido"
                return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')
            # se non ha un'altra squadra, crea la squadra
            squadra = Squadra.objects.create(nome=nome, utente=request.user.username, ordine=modulo, g1=g1, g2=g2, g3=g3, g4=g4, g5=g5, g6=g6, g7=g7, g8=g8, g9=g9, g10=g10, g11=g11)
            squadra.save()
            success_message = "squadra creata"
        else:
            error_message = "squadra gia' esistente"

        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')


# action: subscribe_tournament
# descrizione: submit al form di iscrizione torneo (solo giocatore)
@login_required
def subscribe_tournament_view(request):
    # se non è loggato o non è un giocatore, non può iscriversi ai tornei
    if not request.user.is_authenticated or request.user.groups.filter(name='Giocatore').count() == 0:
        print("non sei loggato o non sei un giocatore")
        return redirect('index')
    
    else:
        error_message = None
        success_message = None

        # prendo il torneo e la squadra dal form
        torneo = request.POST.get('torneo')
        squadra = request.POST.get('squadra')
        quota = Torneo.objects.get(ID=torneo).quota

        # se il giocatore non ha abbastanza crediti, non può iscriversi
        if Giocatore.objects.get(username=request.user).bilancio < quota:
            error_message = "crediti insufficienti"
        # se la data di oggi non è compresa tra dataInizio e dataFine, non può iscriversi
        elif Torneo.objects.get(ID=torneo).dataInizio > timezone.localdate() or Torneo.objects.get(ID=torneo).dataFine < timezone.localdate():
            error_message = "torneo non disponibile"
        # se il giocatore è già iscritto al torneo con la stessa squadra, non può iscriversi
        elif Iscrizione.objects.filter(torneo=torneo, utente=request.user, squadra=squadra).count() != 0:
            error_message = "squadra gia' iscritta"
        # se la squadra non esiste, non può iscriversi
        elif Squadra.objects.filter(nome=squadra, utente=request.user).count() == 0:
            error_message = "squadra non esistente"
        else:
            # rimuovo la quota dal bilancio del giocatore
            giocatore = Giocatore.objects.get(username=request.user)
            giocatore.remove_bilancio(quota, f"iscrizione torneo")
            # aggiungo l'80% della quota al montepremi del torneo
            ttorneo = Torneo.objects.get(ID=torneo)
            ttorneo.montepremi += round(quota * 0.8, 2)
            ttorneo.save()
            iscrizione = Iscrizione.objects.create(utente=request.user.username, torneo=torneo, squadra=squadra, dataIscrizione=timezone.now(), punteggio=0)
            iscrizione.save()
            success_message = "iscrizione effettuata"
        return redirect(reverse('index') + f'?error_message={error_message}&success_message={success_message}')