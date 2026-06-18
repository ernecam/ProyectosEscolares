import os
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from PyPDF2 import PdfReader
from docx import Document
import string

nltk.download("punkt")
nltk.download("stopwords")
nltk.download('punkt_tab')

# CARPETA_CORPUS = ruta de la carpeta del corpus

ARCHIVO_TOKENS = "1Diccionario.xlsx"
ARCHIVO_LIMPIO = "2DiccMinus.xlsx"
ARCHIVO_STOPWORDS = "3DiccSinStopWords.xlsx"
ARCHIVO_STEMMING = "4DiccSteams.xlsx"

def leer_documento(ruta_archivo):
    archivo = ruta_archivo.lower()

    if archivo.endswith(".txt"):
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif archivo.endswith(".pdf"):
        texto = ""
        reader = PdfReader(ruta_archivo)
        for page in reader.pages:
            contenido = page.extract_text()
            if contenido:
                texto += contenido + "\n"
        return texto

    elif archivo.endswith(".docx"):
        texto = ""
        doc = Document(ruta_archivo)
        for p in doc.paragraphs:
            texto += p.text + "\n"
        return texto

    return ""

diccionario = set()

for archivo in os.listdir(CARPETA_CORPUS):
    ruta = os.path.join(CARPETA_CORPUS, archivo)

    if not os.path.isfile(ruta):
        continue  

    texto = leer_documento(ruta)

    if texto.strip():
        tokens = word_tokenize(texto)
        diccionario.update(tokens)

df_tokens = pd.DataFrame(sorted(diccionario), columns=["Token"])
df_tokens.to_excel(ARCHIVO_TOKENS, index=False)
print("Archivo generado:", ARCHIVO_TOKENS)


diccionario_limpio = []

for palabra in df_tokens["Token"]:
    palabra = palabra.lower()
    palabra = palabra.translate(str.maketrans("", "", string.punctuation))
    if palabra.strip():
        diccionario_limpio.append(palabra)

df_limpio = pd.DataFrame(sorted(set(diccionario_limpio)), columns=["Token"])
df_limpio.to_excel(ARCHIVO_LIMPIO, index=False)
print("Archivo generado:", ARCHIVO_LIMPIO)


stop_words = set(stopwords.words("spanish"))

sin_stopwords = [p for p in df_limpio["Token"] if p not in stop_words]

df_stop = pd.DataFrame(sorted(set(sin_stopwords)), columns=["Token"])
df_stop.to_excel(ARCHIVO_STOPWORDS, index=False)
print("Archivo generado:", ARCHIVO_STOPWORDS)


stemmer = SnowballStemmer("spanish")
stems = [stemmer.stem(p) for p in df_stop["Token"]]

df_stem = pd.DataFrame(sorted(set(stems)), columns=["Token"])
df_stem.to_excel(ARCHIVO_STEMMING, index=False)
print("Archivo generado:", ARCHIVO_STEMMING)

print("\n PROCESO COMPLETO. Los 4 archivos se generaron correctamente.\n")
