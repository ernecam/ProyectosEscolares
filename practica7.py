import re
import unicodedata
import numpy as np
import pandas as pd
from collections import Counter
from nltk.stem.snowball import SnowballStemmer
from PyPDF2 import PdfReader

# =========================
# CONFIGURACIÓN
# =========================

PERCENTILES = [60, 75, 90]  # ← puedes cambiar
MIN_LEN = 5                 # longitud mínima de palabra

# =========================
# LECTURA PDF
# =========================

def leer_archivo_pdf(ruta):
    texto = ""
    reader = PdfReader(ruta)
    
    for pagina in reader.pages:
        contenido = pagina.extract_text()
        if contenido:
            texto += contenido + " "
    
    return texto


# =========================
# PREPROCESAMIENTO
# =========================

stopwords = set([
    "y", "o", "de", "la", "el", "los", "las", "un", "una", "en", "con", "por", "para", "a", "tu", "lo", "del", "su", 
    "se", "yo","es", "si", "que", "ella", "no", "les", "le", "mi", "mis", "sus", "sin", "ni", "me", "al", "os", "luego",
    "pero" 
])

def limpiar_texto(texto):
    texto = texto.lower()
    texto = texto.replace("\n", " ")
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-zñ\s]', '', texto)
    return texto

def tokenizar(texto):
    return texto.split()

def eliminar_stopwords(tokens):
    return [t for t in tokens if t not in stopwords]


# =========================
# SNOWBALL
# =========================

stemmer = SnowballStemmer("spanish")

def aplicar_snowball(tokens):
    return [stemmer.stem(t) for t in tokens]


# =========================
# ENTROPÍA
# =========================

def calcular_entropia(subcadena):
    if len(subcadena) == 0:
        return 0
    freq = Counter(subcadena)
    total = len(subcadena)
    entropia = 0
    for c in freq:
        p = freq[c] / total
        entropia -= p * np.log2(p)
    return entropia


# =========================
# SCORES POR PALABRA
# =========================

def obtener_scores_palabra(palabra):
    scores = []
    
    for i in range(1, len(palabra)):
        izquierda = palabra[:i]
        derecha = palabra[i:]
        
        h_izq = calcular_entropia(izquierda)
        h_der = calcular_entropia(derecha)
        
        score = h_izq + h_der
        scores.append((i, score))
    
    return scores

# VECTOR ENTROPIA

def vector_entropia_palabra(palabra):
    scores = obtener_scores_palabra(palabra)
    
    valores = [round(s, 4) for _, s in scores]
    
    valores.append(0)
    
    return valores

def vector_a_texto(vector):
    return ", ".join(map(str, vector))


# =========================
# CORTE TIPO STEM (ENTROPÍA)
# =========================

def corte_por_percentil(palabra, percentil, porcentaje_min=0.6):
    
    if len(palabra) < 4:
        return palabra

    scores = obtener_scores_palabra(palabra)
    valores = [s for _, s in scores]

    umbral = np.percentile(valores, percentil)

    limite = int(len(palabra) * porcentaje_min)

    for i, s in scores:
        if s >= umbral and i >= limite:
            return palabra[:i]

    return palabra
# =========================
# MÉTRICAS
# =========================

def total_caracteres(lista):
    return sum(len(p) for p in lista)


def calcular_precision(real, predicho):
    correctos = sum(1 for r, p in zip(real, predicho) if r == p)
    return correctos / len(real)


# =========================
# PROCESAMIENTO PRINCIPAL
# =========================

def procesar_texto(texto):

    texto = limpiar_texto(texto)
    tokens = tokenizar(texto)
    tokens = eliminar_stopwords(tokens)

    # Snowball (referencia)
    snowball = aplicar_snowball(tokens)

    resultados = {
        "Palabra": tokens,
        "Snowball": snowball
    }

    metricas = []

    # Total Snowball
    total_snow = total_caracteres(snowball)
    metricas.append(("Snowball", total_snow, 1.0))  

    # Entropía con distintos percentiles
    for p in PERCENTILES:
        stems_entropia = [corte_por_percentil(palabra, p) for palabra in tokens]
        
        resultados[f"Entropia_P{p}"] = stems_entropia
        
        total = total_caracteres(stems_entropia)
        precision = calcular_precision(snowball, stems_entropia)
        
        metricas.append((f"Percentil {p}", total, precision))

    vectores = [vector_a_texto(vector_entropia_palabra(p)) for p in tokens]


    # DataFrames
    df = pd.DataFrame(resultados)

    df["Vector_Entropia"] = [
        ", ".join(map(str, vector_entropia_palabra(p)))
    for p in df["Palabra"]
    ]
    df_metricas = pd.DataFrame(metricas, columns=["Metodo", "Total Caracteres", "Precision_vs_Snowball"])

    print("\n--- MÉTRICAS ---")
    print(df_metricas)

    # Exportar
    with pd.ExcelWriter("resultado.xlsx") as writer:
        df.to_excel(writer, sheet_name="Resultados", index=False)
        df_metricas.to_excel(writer, sheet_name="Metricas", index=False)

    return df


# =========================
# EJECUCIÓN
# =========================

ruta = r'D:\Documentos\Luis\CCO\Recuperacion Informacion\Profeta\Gibran-Profeta.pdf'

texto = leer_archivo_pdf(ruta)

resultado = procesar_texto(texto)

print(resultado.head())