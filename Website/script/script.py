# Combina Statistiche*.xlsx e Voti*.xlsx in un unico file csv

import os
import pandas as pd
import numpy as np

# controlliamo i file nella cartella
for file in os.listdir():
    if file.startswith('Statistiche') and file.endswith('.xlsx'):
        os.rename(file, 'Statistiche.xlsx')
    elif file.startswith('Voti') and file.endswith('.xlsx'):
        os.rename(file, 'Voti.xlsx')

# se non ci sono i file necessari, esce dal programma
if not os.path.isfile('Statistiche.xlsx') or not os.path.isfile('Voti.xlsx'):
    print('File non trovati')
    exit()


# -- STATISTICHE --
# carico il file  'Statistiche.xlsx'
stats = pd.read_excel('Statistiche.xlsx', sheet_name='Tutti')
# the first row is the header
stats.columns = stats.iloc[0]
# I drop the first row
stats = stats.drop(stats.index[0])
# take only R, Nome, Squadra, Fm
stats = stats[['R', 'Nome', 'Squadra', 'Fm']]

# -- VOTI --
# carico il file 'Voti.xlsx'
voti = pd.read_excel('Voti.xlsx', sheet_name='Italia')
# la 5a riga è il l'header
voti.columns = voti.iloc[4]
# drop the first 4 rows
voti = voti.drop(voti.index[0:5])
# drop a row if at column Ruolo is a NaN or ALL or Ruolo
voti = voti.dropna(subset=['Ruolo'])
voti = voti[voti.Ruolo != 'ALL']
voti = voti[voti.Ruolo != 'Ruolo']

# -- COMBINAZIONE --
# uniamo i due dataframe in un unic dataframe con R, Nome, Squadra, Fm, Voto

# creiamo un nuovo df con R, Nome, Squadra, Fm, Voto
df = pd.DataFrame(columns=['R', 'Nome', 'Squadra', 'Fm', 'Punteggio'])
# aggiungiamo i dati di stats e voti basandoci sul nome
for index, row in stats.iterrows():
    name = row['Nome']
    voto = voti[voti['Nome'] == name]
    # if there is a value for Voto and it isnt a string, use it else use 0
    if len(voto) > 0 and not isinstance(voto['Voto'].values[0], str):
        # punteggio = voto + (Gf*3) + (Gs*-1) + (Rp*3) + (Rs*-3) + (Rf*3) + (Au*2) + (Amm*-0.5) + (Esp*-1) + (Ass)
        punteggio = voto['Voto'].values[0] + (voto['Gf'].values[0]*3) + (voto['Gs'].values[0]*-1) + (voto['Rp'].values[0]*3) + (voto['Rs'].values[0]*-3) + (voto['Rf'].values[0]*3) + (voto['Au'].values[0]*2) + (voto['Amm'].values[0]*-0.5) + (voto['Esp'].values[0]*-1) + (voto['Ass'].values[0])
    else:
        punteggio = 0
    df.loc[index] = [row['R'], row['Nome'], row['Squadra'], row['Fm'], punteggio]

# -- SALVATAGGIO --
# salviamo il dataframe in un file csv, sovrascrive se gia esistente
df.to_csv('Calciatori.csv', index=False)