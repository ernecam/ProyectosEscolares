from flask import Flask, render_template, send_from_directory, request
import os
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_FOLDER = os.path.join(BASE_DIR, "Corpus")

# INDEX_FOLDER = colocar ruta de archivo html para visualizar pag web
# ============================================================
#  FUNCIONES PARA CONVERSIÓN BOOLEANA
# ============================================================

# Prioridad de operadores
prioridad = {
    "no": 3,
    "y": 2,
    "o": 1
}

def es_operador(token):
    return token in ["y", "o", "no"]

def a_posfijo(tokens):
    """Convierte expresión infijo a posfijo (Polaca inversa)"""
    salida = []
    pila = []

    for token in tokens:
        if token == "(":
            pila.append(token)
        elif token == ")":
            while pila and pila[-1] != "(":
                salida.append(pila.pop())
            pila.pop()  # quitar "("
        elif es_operador(token):
            while (pila and pila[-1] != "(" and 
                   prioridad.get(pila[-1], 0) >= prioridad[token]):
                salida.append(pila.pop())
            pila.append(token)
        else:
            salida.append(token)

    while pila:
        salida.append(pila.pop())

    return salida


def evaluar_posfijo(tokens):
    """Simula la lectura paso a paso del posfijo"""
    pila = []
    print("\n--- LECTURA POSFIJO PASO A PASO ---\n")
    for token in tokens:
        print(f"Procesando: {token}")
        if not es_operador(token):
            pila.append(token)
            print(f"  Apila → {pila}")
        else:
            if token == "no":
                op = pila.pop()
                nuevo = f"(no {op})"
                pila.append(nuevo)
            else:
                right = pila.pop()
                left = pila.pop()
                nuevo = f"({left} {token} {right})"
                pila.append(nuevo)
            
            print(f"  Resultado parcial: {pila[-1]}")
        
    print("\nResultado final:", pila[0])
    print("-------------------------------------\n")


# ============================================================
#  RUTAS DE FLASK
# ============================================================

@app.route("/", methods=["GET", "POST"])
def index():
    archivos = os.listdir(INDEX_FOLDER)
    return render_template("index.html", archivos=archivos)


@app.route("/documento/<nombre>")
def abrir_documento(nombre):
    ruta = os.path.join(CORPUS_FOLDER, nombre)

    if nombre.endswith(".txt"):
        with open(ruta, "r", encoding="utf-8") as f:
            print("\n--- CONTENIDO TXT ---\n")
            print(f.read())

    elif nombre.endswith(".pdf"):
        reader = PdfReader(ruta)
        print("\n--- CONTENIDO PDF ---\n")
        for pagina in reader.pages:
            print(pagina.extract_text())

    elif nombre.endswith(".docx"):
        doc = Document(ruta)
        print("\n--- CONTENIDO DOCX ---\n")
        for p in doc.paragraphs:
            print(p.text)

    return send_from_directory(CORPUS_FOLDER, nombre)



@app.route("/consulta_booleana", methods=["POST"])
def consulta_booleana():
    expresion = request.form["expresion"]

    print("\n\n=====================================")
    print("EXPRESIÓN ORIGINAL:", expresion)
    print("=====================================")

    # Tokenizar separando paréntesis y palabras
    expresion_clean = (
        expresion.replace("(", " ( ")
                 .replace(")", " ) ")
    )
    tokens = expresion_clean.split()

    print("\nTokens:", tokens)

    # Convertir a posfijo
    posfijo = a_posfijo(tokens)

    print("\nNotación posfijo:", posfijo)

    # Evaluar posfijo paso a paso
    evaluar_posfijo(posfijo)

    return "<h2>Consulta procesada. Revisa la consola.</h2>"


if __name__ == "__main__":
    app.run(debug=True)
