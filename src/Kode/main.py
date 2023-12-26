import sqlite3
import io
import re
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
import math

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
    for aar in range(2001,2023):
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
    # return FjernAlmindeligeOrd(forbindelse.fetchall())
    return forbindelse.fetchall()

def MestBrugteOrdAlleAar():
    ordbog = {}
    for aar in range(2001,2023):
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

def årHvorOrdNævnes(årRække, ordListe):
    # ordList er en liste af lister, hvor hver indre lister indeholder alle de ønskede mutationer af et ord, hvor det skal tælles hvor mange forskellige år, disse ord er blevet sagt.
    nævneÅr = []
    for ord in ordListe:
        årligeForekomster = HvorMangeGangeNaevnes([ord], årRække)[ord]
        for forekomst in årligeForekomster:
            if forekomst[1] > 0 and not forekomst[0] in nævneÅr:
                nævneÅr.append(forekomst[0])
    return len(nævneÅr)

def plotOrdPerAar(ord, forekomstListe, grænseVærdi):
    #Aarstal
    xAkse = [e[0] for e in forekomstListe]
    #Forekomster
    yAkse = [e[1] for e in forekomstListe]

    # plt.figure(figsize=(8, 6), dpi=80)
    fig, (ax0, ax1) = plt.subplots(nrows=1, ncols=2, figsize=(12,6))
    fig.subplots_adjust(bottom=0.3)
    ax0.bar(xAkse, yAkse)
    ax0.tick_params(labelrotation=45)
    ax0.set_xticks(np.arange(min(xAkse), max(xAkse)+1, 1.0))
    ax0.set_xlabel('Årstal')
    ax0.set_ylabel('Forekomster')
    ax0.set_title('Gange ' + ord + ' blev sagt i dronningens nytårstaler')

    ax0.axhline(y=grænseVærdi, linewidth=1, color='r')

    text = ord + ' nævnes ' + str(round(gennemsnitligtGangeOrdNævnes(range(2001,2023),ord),2)) + ' gange fra 2001 til 2022.'
    plt.figtext(0.1, 0.15, text)    
    
    text = ord + ' nævnes ' + str(round(gennemsnitligtGangeOrdNævnes(range(2016,2023),ord),2)) + ' gange fra 2016 til 2022.'
    plt.figtext(0.1, 0.10, text)

    over = 0
    under = 0
    for tal in yAkse:
        if tal < grænseVærdi:
            under += 1
        elif tal > grænseVærdi:
            over += 1
    ax1.pie([over, under], labels=["Over: " + str(over), "Under: " + str(under)], colors=['red', 'deepskyblue'])
    
    plt.sca(ax1)
    text = str(round(over/(over+under) * 100, 2)) + ' % af årene fra 2001 til 2022 nævnes ' + ord + ' flere end ' + str(grænseVærdi) + ' gange.'
    plt.figtext(0.5, 0.15, text)

    nævntIÅrRække = HvorMangeGangeNaevnes([ord], range(2016,2023))[ord]
    over = 0
    under = 0
    for tal in nævntIÅrRække:
        if tal[1] < grænseVærdi:
            under += 1
        elif tal[1] > grænseVærdi:
            over += 1
    text = str(round(over/(over+under) * 100, 2)) + ' % af årene fra 2016 til 2022 nævnes ' + ord + ' flere end ' + str(grænseVærdi) + ' gange.'
    plt.figtext(0.5, 0.1, text)


    fig.savefig("../Diagrammer/" + ord + "_2001_til_2023.png")
    fig.clf()

def plotÅrHvorOrdNævnes(ordListe, årRække):
    antalSubplots = len(ordListe)
    kvadrat = math.ceil(math.sqrt(antalSubplots))
    ordIter = 0
    fig, axs = plt.subplots(nrows=kvadrat, ncols=kvadrat, figsize=(4*kvadrat, 4*kvadrat))
    for row in range(len(axs)):
        for ax in axs[row]:
            nævnt = årHvorOrdNævnes(årRække, ordListe[ordIter])
            ikkeNævnt = årRække.stop - årRække.start - nævnt
            ax.pie([nævnt, ikkeNævnt], labels=["Nævnt: " + str(nævnt), "Ikke nævnt: " + str(ikkeNævnt)], labeldistance=0.6, colors=["lime", "gainsboro"])
            titel = str(round(nævnt/(årRække.stop - årRække.start) * 100, 1)) + "% "
            for i in range(len(ordListe[ordIter])):
                if i != 0:
                    titel += ", "
                titel += ordListe[ordIter][i]

            ax.set_title(titel)

            ordIter += 1
            if ordIter >= len(ordListe):
                break
        if ordIter >= len(ordListe):
            break
    plotTitle = "Hvor mange år fra " + str(årRække.start) + " til " + str(årRække.stop) + " er odds-ord indgået i Dronningens nytårstale?"
    fig.suptitle(plotTitle, fontsize='xx-large')
    fig.savefig("../Diagrammer/singleHit_" + str(årRække.start) + "_til_" + str(årRække.stop) + ".png")
    fig.clf()

if __name__ == "__main__":
    # KlargoerDatabase()
    # IndsaetAlleTalerIDatabasen()
    oddsOrdDict = {
        "danmark": 8.5,
        "danske": 5.5,
        "tak": 4.5,
        "grønland": 2.5,
        "færøerne": 2.5,
        "nytår": 2.5,
        "samfund": 1.5,
        "verden": 4.5,
        "nytårsønsker": 2.5
    }
    ordbog = HvorMangeGangeNaevnes(oddsOrdDict, range(2001, 2023))
    for ord in ordbog:
        plotOrdPerAar(ord, ordbog[ord], oddsOrdDict[ord])
    # print(gennemsnitligtGangeOrdNævnes(range(2015,2020), 'grønland'))
    plotÅrHvorOrdNævnes([
        ["student", "studenter"], 
        ["folkefest"],
        ["verden"],
        ["glæde", "glæder"],
        ["nytårshilsen"],
        ["sydslesvig"],
        ["kronprinseparret"],
        ["folk"],
        ["fødselsdag", "fødselsdage"],
        ["nytårsønsker"],
        ["soldater"],
        ["unge"],
        ["ældre"],
        ["børnebørn"],
        ["kronprinsen"],
        ["kronprinsessen"],
        ["krig", "krigen"],
        ["mindretal"],
        ["børn"],
        ["nytårsaften"],
        ["politi", "politiet"],
        ["håb"],
        ["ukraine"],
        ["sommer", "sommeren"],
        ["stolt", "stolte"],
        ["europa"],
        ["forventning", "forventninger"],
        ["generationer"],
        ["klima", "klimaet"],
        ["jul", "julen"],
        ["jøder", "jødisk"],
        ["særligt"],
        ["dagligdag", "dagligdagen"],
        ["pårørende"],
        ["ansvar"],
        ["arbejde", "arbejdet"],
        ["frihed", "friheden"],
        ["sikkerhed"],
        ["hjerte", "hjertet"],
        ["nærmeste"],
        ["opmærksomhed", "opmærksomheden"],
        ["fred", "freden"],
        ["krise", "krisen"],
        ["taknemmelig", "taknemmelighed"],
        ["terror", "terroren"],
        ["muligheder"],
        ["grænse","grænsen"],
        ["mærkedag"],
        ["muslimer", "muslimsk"],
        ["baltiske"],
        ["atter"],
        ["befolkning", "befolkningen"],
        ["ensom", "ensomhed"],
        ["naturen", "naturens"],
        ["klimaforandringer", "klimaforandringerne"],
        ["konflikt", "konflikten"],
        ["sundhedspersonale", "sundhedspersonlaet"],
        ["israel"],
        ["usa"],
        ["civile"],
        ["frankrig"],
        ["alvor"],
        ["energi"],
        ["omsorg"],
        ["grev"],
        ["flygtninge"],
        ["washington"],
        ], range(2001,2023))
