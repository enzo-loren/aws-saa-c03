#!/usr/bin/env python3
"""Pruebas específicas de cobertura post-blueprint SAA-C03 2026."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else "dist")
SUP=ROOT/"audiolibro"/"suplemento-examen-2026.txt"
COURSE=OUT/"SAA-C03-Audiolibro-Curso.txt"
ZIP=OUT/"SAA-C03-Capitulos-TTS.zip"
original=SUP.read_bytes()
generated=COURSE.read_bytes()
if original not in generated:
    raise SystemExit("FAIL: suplemento íntegro no está en el audiocurso")

text=original.decode("utf8")
required={
 "14 tareas oficiales": "tres más dos más cinco más cuatro",
 "S3 CORS": "AllowedOrigins",
 "S3 preflight": "preflight",
 "CORS no autoriza": "CORS no da autorización",
 "ENI para failover": "ENI secundaria",
 "Restricción de AZ": "misma zona de disponibilidad",
 "AWS Quick": "AWS Quick Sight",
 "Polly": "Polly convierte texto en voz",
 "Comprehend": "Comprehend ofrece procesamiento de lenguaje",
 "fuentes oficiales": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html",
}
for concept,phrase in required.items():
    if phrase.casefold() not in text.casefold():
        raise SystemExit("FAIL: falta contenido obligatorio "+concept)

with ZipFile(ZIP) as z:
    names=z.namelist()
    chapters=[n for n in names if re.fullmatch(r"Capitulo-\d+\.txt",n)]
    assert len(chapters)==73, f"FAIL: capítulos esperados 73, hallados {len(chapters)}"
    assert "074-Suplemento-Examen-2026.txt" in names
    assert z.read("074-Suplemento-Examen-2026.txt")==original

# Cada ejercicio creado para respuesta múltiple debe ofrecer cinco alternativas.
segments=text.split("PREGUNTA NUEVA")
multiple=[seg.split("PAUSA.")[0] for seg in segments[1:]
          if "Selecciona DOS de CINCO opciones" in seg[:120] or "Selecciona DOS de CINCO opciones" in seg[:180]]
if len(multiple)!=2:
    raise SystemExit("FAIL: se esperaban dos ejercicios originales Select TWO/5")
for i,segment in enumerate(multiple,1):
    for letter in "ABCDE":
        if f"Alternativa {letter}." not in segment:
            raise SystemExit(f"FAIL: ejercicio {i} carece de alternativa {letter}")
print("PASS: 73 capítulos, suplemento idéntico, 2 preguntas Select TWO con 5 opciones, contenido oficial indispensable y ZIP consistentes")
