import os
import string
import random
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# set timezone to Europe/Rome
timezone.activate("Europe/Rome")

# -- Default Methods --
def generate_username():
    code_length = 6  # You can adjust the length of the lobby code as needed
    characters = string.ascii_uppercase + string.digits
    return 'user-'.join(random.choices(characters, k=code_length))

def generate_tournament_id():
    # autoincremental ID
    return Torneo.objects.count() + 1

# -- Models --
class Agenzia(models.Model):
    ID = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=64, null=False, blank=False)
    def __str__(self):
        return f"{self.nome}"
    
    # when an Agenzia is created, create a new folder in the 'db' folder
    def save(self, *args, **kwargs):
        super(Agenzia, self).save(*args, **kwargs)
        if not os.path.exists(f"db/{self.nome}"):
            os.mkdir(f"db/{self.nome}") 

    # when an Agenzia is blocked; change the password for it and every user with that agenzia to 'blocked'
    def block(self, *args, **kwargs):
        super(Agenzia, self).save(*args, **kwargs)
        user = User.objects.get(username=self.nome)
        user.set_password('blocked')
        user.save()

class Giocatore(models.Model):
    username = models.CharField(max_length=64, primary_key=True, default=generate_username)
    agenzia = models.CharField(max_length=64)
    bilancio = models.FloatField(null=False, blank=False, default=0.00 )

    # when a Giocatore is created, create a new file .csv in the 'db' folder, subfolder of the agenzia
    # the file will contain the history of the Giocatore, with the date and the amount of money added or removed with a description
    def save(self, *args, **kwargs):
        super(Giocatore, self).save(*args, **kwargs)
        if not os.path.exists(f"db/{self.agenzia}/{self.username}.csv"):
            with open(f"db/{self.agenzia}/{self.username}.csv", "w") as f:
                f.write("date,amount,description" + "\n")

    # add bilancio to the Giocatore and write the transaction in the .csv file
    def add_bilancio(self, amount, description):
        # convert the amount to a float with 2 decimal digits
        amount = float("{:.2f}".format(amount))
        # approximate the amount to 2 decimal digits
        amount = round(amount, 2)
        self.bilancio += amount
        self.bilancio = float("{:.2f}".format(self.bilancio))
        self.save()
        # append the transaction to the .csv file
        with open(f"db/{self.agenzia}/{self.username}.csv", "a") as f:
            f.write(f"{timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')},{amount},{description}" + "\n")

    # remove bilancio to the Giocatore and write the transaction in the .csv file
    def remove_bilancio(self, amount, description):
        # if the amount is greater than the bilancio, raise an error
        if amount > self.bilancio:
            raise ValueError("amount is greater than bilancio")
        # convert the amount to a float with 2 decimal digits
        amount = float("{:.2f}".format(amount))
        # approximate the amount to 2 decimal digits
        amount = round(amount, 2)
        self.bilancio -= amount
        self.bilancio = float("{:.2f}".format(self.bilancio))
        self.save()
        # append the transaction to the .csv file
        with open(f"db/{self.agenzia}/{self.username}.csv", "a") as f:
            f.write(f"{timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')},{-amount},{description}" + "\n")

    def __str__(self):
        return f"{self.username}"

class Torneo(models.Model):
    ID = models.AutoField(primary_key=True)
    dataInizio = models.DateField()
    dataFine = models.DateField()
    quota = models.FloatField()
    montepremi = models.FloatField(null=False, blank=False, default=0.00)
    concluso = models.BooleanField(default=False)

    # get ID from the autoincremental method
    def save(self, *args, **kwargs):
        super(Torneo, self).save(*args, **kwargs)
        self.ID = generate_tournament_id()
        
    # get ID from the autoincremental method
    def __str__(self):
        return f"{self.ID}"

    # concludi torneo divide the montepremi between the first 3 players with the highest score in a 50%, 25%, 15%
    def concludi(self, *args, **kwargs):
        super(Torneo, self).save(*args, **kwargs)
        # if the torneo is already concluded pass
        if self.concluso:
            pass
        else:
            # for every iscrizione in the torneo, update the punteggio
            iscrizioni = Iscrizione.objects.filter(torneo=self.ID)
            for iscrizione in iscrizioni:
                iscrizione.update_punteggio()
            # get the first 3 players with the highest score and in date order
            iscrizioni = Iscrizione.objects.filter(torneo=self.ID).order_by("-punteggio", "dataIscrizione")[:3]
            # divide the montepremi between the first 3 players with the highest score in a 50%, 25%, 15%
            # round the prizes to 2 decimal digits
            primo = float("{:.2f}".format(self.montepremi * 0.5))
            secondo = float("{:.2f}".format(self.montepremi * 0.25))
            terzo = float("{:.2f}".format(self.montepremi * 0.15))
            if iscrizioni.count() == 0:
                pass
            elif iscrizioni.count() == 1:
                Giocatore.objects.get(username=iscrizioni[0].utente).add_bilancio(primo, f"Vincita torneo")
            elif iscrizioni.count() == 2:
                Giocatore.objects.get(username=iscrizioni[0].utente).add_bilancio(primo, f"Vincita torneo")
                Giocatore.objects.get(username=iscrizioni[1].utente).add_bilancio(secondo, f"Vincita torneo")
            else:
                Giocatore.objects.get(username=iscrizioni[0].utente).add_bilancio(primo, f"Vincita torneo")
                Giocatore.objects.get(username=iscrizioni[1].utente).add_bilancio(secondo, f"Vincita torneo")
                Giocatore.objects.get(username=iscrizioni[2].utente).add_bilancio(terzo, f"Vincita torneo")
            # set the torneo as concluded
            self.concluso = True
            self.save()
    
class Calciatore(models.Model):
    ruolo = models.CharField(max_length=64, null=False, blank=False)
    cognome = models.CharField(max_length=64, null=False, blank=False)
    squadra = models.CharField(max_length=64, null=False, blank=False)
    punteggio = models.IntegerField(null=False, blank=False, default=0)
    mediaFV = models.IntegerField(null=False, blank=False, default=0)

    def __str__(self):
        return f"{self.cognome} {self.squadra} {self.mediaFV}"

class Squadra(models.Model):
    ID = models.AutoField(primary_key=True)
    utente = models.CharField(max_length=64)
    nome = models.CharField(max_length=64)
    ordine = models.CharField(max_length=64)
    g1 = models.CharField(max_length=64)
    g2 = models.CharField(max_length=64)
    g3 = models.CharField(max_length=64)
    g4 = models.CharField(max_length=64)
    g5 = models.CharField(max_length=64)
    g6 = models.CharField(max_length=64)
    g7 = models.CharField(max_length=64)
    g8 = models.CharField(max_length=64)
    g9 = models.CharField(max_length=64)
    g10 = models.CharField(max_length=64)
    g11 = models.CharField(max_length=64)
    
    def __str__(self):
        return f"{self.nome}"
    
    # substitute ' ' with '_'

class Iscrizione(models.Model):
    ID = models.AutoField(primary_key=True)
    utente = models.CharField(max_length=64)
    torneo = models.CharField(max_length=64)
    squadra = models.CharField(max_length=64)
    dataIscrizione = models.DateField()
    punteggio = models.FloatField(null=False, blank=False, default=0.00)

    
    # get infos
    def get_classifica(self):
        torneo = Torneo.objects.get(ID=self.torneo)
        dataInizio = torneo.dataInizio
        dataFine = torneo.dataFine
        punteggioprimo = Iscrizione.objects.filter(torneo=self.torneo).order_by("-punteggio")[0].punteggio
        punteggiosecondo = Iscrizione.objects.filter(torneo=self.torneo).order_by("-punteggio")[1].punteggio
        punteggioterzo = Iscrizione.objects.filter(torneo=self.torneo).order_by("-punteggio")[2].punteggio
        punteggio = self.punteggio
        return torneo, dataInizio, dataFine, punteggioprimo, punteggiosecondo, punteggioterzo, punteggio

    # update the punteggio of the Iscrizione based on the giocatori in the squadra
    def update_punteggio(self, *args, **kwargs):
        super(Iscrizione, self).save(*args, **kwargs)
        print(self.squadra)
        # if squadra is not found pass
        try:
            squadra = Squadra.objects.get(nome=self.squadra, utente=self.utente)
        except Exception as e:
            if type(e).__name__ == 'ObjectDoesNotExist':
                # Handle the case when the squadra is not found
                print(f"Squadra with nome={self.squadra} and utente={self.utente} not found.")
                return
            else:
                # Handle other exceptions if needed
                print(f"An error occurred: {e}")
                return
        squadra = Squadra.objects.get(nome=self.squadra, utente=self.utente)
        self.punteggio = 0
        cognomeg1 = squadra.g1.split(" ")[0:-2]
        cognomeg1 = " ".join(cognomeg1)
        squadrag1 = squadra.g1.split(" ")[-2]
        g1 = Calciatore.objects.get(cognome=cognomeg1, squadra=squadrag1)
        self.punteggio += g1.punteggio
        cognomeg2 = squadra.g2.split(" ")[0:-2]
        cognomeg2 = " ".join(cognomeg2)
        squadrag2 = squadra.g2.split(" ")[-2]
        g2 = Calciatore.objects.get(cognome=cognomeg2, squadra=squadrag2)
        self.punteggio += g2.punteggio
        cognomeg3 = squadra.g3.split(" ")[0:-2]
        cognomeg3 = " ".join(cognomeg3)
        squadrag3 = squadra.g3.split(" ")[-2]
        g3 = Calciatore.objects.get(cognome=cognomeg3, squadra=squadrag3)
        self.punteggio += g3.punteggio
        cognomeg4 = squadra.g4.split(" ")[0:-2]
        cognomeg4 = " ".join(cognomeg4)
        squadrag4 = squadra.g4.split(" ")[-2]
        g4 = Calciatore.objects.get(cognome=cognomeg4, squadra=squadrag4)
        self.punteggio += g4.punteggio
        cognomeg5 = squadra.g5.split(" ")[0:-2]
        cognomeg5 = " ".join(cognomeg5)
        squadrag5 = squadra.g5.split(" ")[-2]
        g5 = Calciatore.objects.get(cognome=cognomeg5, squadra=squadrag5)
        self.punteggio += g5.punteggio
        cognomeg6 = squadra.g6.split(" ")[0:-2]
        cognomeg6 = " ".join(cognomeg6)
        squadrag6 = squadra.g6.split(" ")[-2]
        g6 = Calciatore.objects.get(cognome=cognomeg6, squadra=squadrag6)
        self.punteggio += g6.punteggio
        cognomeg7 = squadra.g7.split(" ")[0:-2]
        cognomeg7 = " ".join(cognomeg7)
        squadrag7 = squadra.g7.split(" ")[-2]
        g7 = Calciatore.objects.get(cognome=cognomeg7, squadra=squadrag7)
        self.punteggio += g7.punteggio
        cognomeg8 = squadra.g8.split(" ")[0:-2]
        cognomeg8 = " ".join(cognomeg8)
        squadrag8 = squadra.g8.split(" ")[-2]
        g8 = Calciatore.objects.get(cognome=cognomeg8, squadra=squadrag8)
        self.punteggio += g8.punteggio
        cognomeg9 = squadra.g9.split(" ")[0:-2]
        cognomeg9 = " ".join(cognomeg9)
        squadrag9 = squadra.g9.split(" ")[-2]
        g9 = Calciatore.objects.get(cognome=cognomeg9, squadra=squadrag9)
        self.punteggio += g9.punteggio
        cognomeg10 = squadra.g10.split(" ")[0:-2]
        cognomeg10 = " ".join(cognomeg10)
        squadrag10 = squadra.g10.split(" ")[-2]
        g10 = Calciatore.objects.get(cognome=cognomeg10, squadra=squadrag10)
        self.punteggio += g10.punteggio
        cognomeg11 = squadra.g11.split(" ")[0:-2]
        cognomeg11 = " ".join(cognomeg11)
        squadrag11 = squadra.g11.split(" ")[-2]
        g11 = Calciatore.objects.get(cognome=cognomeg11, squadra=squadrag11)
        self.punteggio += g11.punteggio
        self.save()
 
    def __str__(self):
        return f"{self.utente}"
