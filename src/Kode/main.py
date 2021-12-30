import sqlite3
import io
import re
from collections import Counter

def HentTale(Aarstal):
    fil = io.open("../Taler/" + str(Aarstal) + ".txt","r", encoding="utf-8")
    tekst = fil.read()
    fil.close()
    return tekst

def TekstTilListe(Tekst):
    return re.sub("[^\w]", " ", Tekst).split()

def TaelForekomster(Ordliste):
    return Counter(Ordliste).most_common()

def KlargoerDatabase():
    forbindelse = sqlite3.connect('DronningeDatabasen.db')
    forbindelse.execute("""DROP TABLE IF EXISTS NytaarsTale""")
    forbindelse.execute("""
    CREATE TABLE IF NOT EXISTS NytaarsTale (
        Ord TEXT,
        AAR INTEGER,
        Forekomster INTEGER
    )
    """)
    forbindelse.commit()
    return forbindelse

# def TilfoejAarstalTilOrdliste(OrdListe,AarsTal):
#     print("hej")
#     for e in OrdListe:
#         e.append

def IndsaetOrdlisteIDatabase(Ordliste, AarsTal, DatabaseForbindelse):
    DatabaseForbindelse.executemany("INSERT INTO NytaarsTale VALUES (?, ?, " + str(AarsTal) + " )", Ordliste)
    DatabaseForbindelse.commit()
        

if __name__ == "__main__":
    # print("GUD BEVARE DANMARK")
    tale = HentTale(2002)
    liste = TekstTilListe(tale)
    optaelling = TaelForekomster(liste)
    
    forbindelse = KlargoerDatabase()
    IndsaetOrdlisteIDatabase(optaelling, 2002, forbindelse)