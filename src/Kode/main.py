import sqlite3
import io
import re
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np

def HentTale(Aarstal):
    fil = io.open("../Taler/" + str(Aarstal) + ".txt","r", encoding="utf-8")
    tekst = fil.read()
    fil.close()
    return tekst

def TekstTilListe(Tekst):
    ord = re.sub("[^\w]", " ", Tekst).split()
    return [x.lower() for x in ord]

def TaelForekomster(Ordliste):
    return Counter(Ordliste).most_common()

def KlargoerDatabase():
    forbindelse = sqlite3.connect('DronningeDatabasen.db')
    forbindelse.execute("""DROP TABLE IF EXISTS NytaarsTale""")
    forbindelse.execute("""
    CREATE TABLE IF NOT EXISTS NytaarsTale (
        Ord TEXT,
        Forekomster INTEGER,
        Aar INTEGER
    )
    """)
    forbindelse.commit()
    return forbindelse

def DatabaseForbindelse():
    return sqlite3.connect('DronningeDatabasen.db')

def IndsaetOrdlisteIDatabase(Ordliste, AarsTal, DatabaseForbindelse):
    DatabaseForbindelse.executemany("INSERT INTO NytaarsTale VALUES (?, ?, " + str(AarsTal) + " )", Ordliste)
    DatabaseForbindelse.commit()

def IndsaetAlleTalerIDatabasen():
    forbindelse = DatabaseForbindelse()
    for aar in range(2001,2022):
        IndsaetOrdlisteIDatabase(TaelForekomster(TekstTilListe(HentTale(aar))), aar, forbindelse)

def FjernAlmindeligeOrd(Ordliste):
    if(len(Ordliste) < 1):
        return Ordliste
    fil = io.open("../AlmindeligeOrd.txt","r", encoding="utf-8")
    almindeligeOrd = fil.read()
    fil.close()

    almindeligeOrd = TekstTilListe(almindeligeOrd)

    rensedeOrd = []
    for ord in Ordliste:
        if(not ord[0] in almindeligeOrd):
            rensedeOrd.append(ord)
    
    return rensedeOrd



def MestBrugteOrdIAar(Aar):
    forbindelse = DatabaseForbindelse().cursor()
    forbindelse.execute("SELECT Ord, Forekomster FROM NytaarsTale WHERE Aar = :aarstal", {"aarstal":Aar})
    return FjernAlmindeligeOrd(forbindelse.fetchall())

def MestBrugteOrdAlleAar():
    ordbog = {}
    for aar in range(2001,2022):
        ordliste = MestBrugteOrdIAar(aar)
        for ord in ordliste:
            if (ord[0] in ordbog):
                ordbog[ord[0]] = ordbog[ord[0]] + ord[1]
            else:
                ordbog[ord[0]] = ord[1]
    nyOrdbog = {}
    for ord in ordbog:
        if(ordbog[ord] > 10):
            nyOrdbog[ord] = ordbog[ord]
    return nyOrdbog

def HvorMangeGangeNaevnes(oddsOrd, aarRaekke):
    ordPerAar = {}
    forbindelse = DatabaseForbindelse().cursor()

    for ord in oddsOrd:
        liste = []
        for aar in aarRaekke:
            forbindelse.execute("SELECT Aar, Forekomster FROM NytaarsTale WHERE Aar = :aarstal AND Ord = :ord", {"aarstal":aar,"ord":ord})
            gangeOrdBlevSagt = forbindelse.fetchone()
            if(gangeOrdBlevSagt == None):
                liste.append((aar,0))
            else:
                liste.append(gangeOrdBlevSagt)
        ordPerAar[ord] = liste
    return ordPerAar
    
def gennemsnitligtGangeOrdNævnes(aarRaekke, ord):
    forekomster = HvorMangeGangeNaevnes([ord], aarRaekke)[ord]
    forekomster = [e[1] for e in forekomster]
    forekomster = sum(forekomster)
    antalAar = len(aarRaekke)
    return forekomster/antalAar


def plotOrdPerAar(ord, forekomstListe, grænseVærdi):
    #Aarstal
    xAkse = [e[0] for e in forekomstListe]
    #Forekomster
    yAkse = [e[1] for e in forekomstListe]

    plt.figure(figsize=(8, 6), dpi=80)
    plt.subplots_adjust(bottom=0.3)
    plt.bar(xAkse, yAkse)
    plt.xticks(np.arange(min(xAkse), max(xAkse)+1, 1.0))
    plt.xticks(rotation=45)
    plt.xlabel('Årstal')
    plt.ylabel('Forekomster')
    plt.title('Gange ' + ord + ' blev sagt i dronningens nytårstaler')

    plt.axhline(y=grænseVærdi, linewidth=1, color='r')

    text = ord + ' nævnes ' + str(gennemsnitligtGangeOrdNævnes(range(2001,2022),ord)) + ' gange fra 2001 til 2021.'
    plt.figtext(0.1, 0.15, text)    
    
    text = ord + ' nævnes ' + str(gennemsnitligtGangeOrdNævnes(range(2016,2022),ord)) + ' gange fra 2016 til 2021.'
    plt.figtext(0.1, 0.10, text)
    
    plt.savefig("../Diagrammer/" + ord + "_2001_til_2021.png")
    plt.clf()



if __name__ == "__main__":
    # KlargoerDatabase()
    IndsaetAlleTalerIDatabasen()
    oddsOrdDict = {
        "danmark": 7.5,
        "danske": 4.5,
        "tak": 3.5,
        "grønland": 3.5,
        "færøerne": 2.5,
        "nytår": 2.5,
        "samfund": 2.5,
        "verden": 2.5,
        "nytårsønsker": 2.5
    }
    ordbog = HvorMangeGangeNaevnes(oddsOrdDict, range(2001, 2022))
    for ord in ordbog:
        plotOrdPerAar(ord, ordbog[ord], oddsOrdDict[ord])
    # print(gennemsnitligtGangeOrdNævnes(range(2015,2020), 'grønland'))
