#!/usr/bin/env python3
"""Prueba de que la edición TTS conserva preguntas y elimina ruido editorial."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import json
import re
import sys
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else "dist")
SUP=ROOT/"audiolibro/suplemento-examen-2026.txt"
original=SUP.read_text(encoding="utf8")
raw=(OUT/"SAA-C03-Audiolibro-BASE-TEXTUAL.txt").read_text(encoding="utf8")
spoken=(OUT/"SAA-C03-Audiolibro-Curso.txt").read_text(encoding="utf8")
listen=(OUT/"SAA-C03-SOLO-ESCUCHAR.txt").read_text(encoding="utf8")
recalled=(OUT/"SAA-C03-Repaso-Espaciado.txt").read_text(encoding="utf8")
full=OUT/"SAA-C03-Audiolibro-COMPLETO.txt"
audit=json.loads((OUT/"AUDITORIA-ESCUCHA.json").read_text(encoding="utf8"))
assert raw.endswith(original+"\n"),"El suplemento fuente no se conservó literalmente"
assert listen==spoken,"El PDF y el TXT de escucha no parten del mismo texto"
assert raw in full.read_text(encoding="utf8"),"El maestro documental perdió contenido sin editar"
assert audit["fluido"]["mode"]=="fluido" and audit["repaso"]["mode"]=="repaso"
expected=list(range(1,73))+[74]
for text in [spoken,recalled]:
    markers=[int(x) for x in re.findall(r"(?m)^Capítulo (\d+)\. ",text)]
    assert markers==expected, f"Orden incorrecto: {markers}"
    for forbidden in [r"(?m)^Fuente:",r"(?mi)^SHA256:",r"(?mi)^FUENTE DOCUMENTAL:",
                      r"(?m)^Comparación\. ",r"(?m)^REPASO ESPACIADO\.",
                      r"(?m)^PAUSA DE RECUPERACIÓN ACTIVA\.",
                      r"(?mi)^https?://",r"(?m)^Referencia bronze"]:
        assert re.search(forbidden,text) is None,f"Ruido de lectura: {forbidden}"
    assert "bronze/" not in text, "Quedaron rutas de fuentes Bronze pronunciables"
    assert "URL oficial:" not in text, "Quedaron tablas con enlaces pronunciables"
    for must in ["AllowedOrigins","ENI secundaria","AWS Quick Sight","Amazon Comprehend",
                 "Amazon Polly","Alternativa E."]:
        assert must in text, f"Falta contenido del suplemento: {must}"
assert "Repasemos las ideas centrales" not in spoken
assert "Recordemos una idea de capítulos anteriores" in recalled
assert "Capítulo 73." not in spoken
# El libro con fuentes sigue archivado pero no forma parte de la lectura de voz.
assert "CAPÍTULO 73. Trazabilidad 155 fuentes oficiales" in raw

# La conversión no puede perder ninguna alternativa de los ejercicios.
def options(text):
    return Counter(re.findall(r"(?m)^Alternativa ([A-E])\.\s*(.+)$",text))
raw_options=options(raw)
assert raw_options, "Sin alternativas de preguntas en el original"
assert options(spoken)==raw_options, "Alguna alternativa se modificó o eliminó"
assert options(recalled)==raw_options, "Se alteraron alternativas en modo repaso"

for zipname,narration in [
    ("SAA-C03-Capitulos-TTS.zip",spoken),
    ("SAA-C03-Capitulos-REPASO-TTS.zip",recalled)]:
    with ZipFile(OUT/zipname) as z:
        filenames=z.namelist()
        chapters=[x for x in filenames if re.fullmatch(r"Capitulo-\d+\.txt",x)]
        assert len(chapters)==72, f"Los 72 capítulos de estudio no están separados: {len(chapters)}"
        assert "Capitulo-73.txt" not in filenames
        assert "074-Suplemento-Examen-2026.txt" in filenames
        combined="".join(z.read(x).decode("utf8") for x in filenames)
        assert combined==narration,"El ZIP no reconstruye exactamente el texto narrable"
        supplement=z.read("074-Suplemento-Examen-2026.txt").decode("utf8")
        assert supplement.startswith("Capítulo 74.")
        assert "Fuentes oficiales de esta actualización:" not in supplement

# El PDF de lectura no puede reintroducir material técnico por error.
pdf=PdfReader(str(OUT/"SAA-C03-Audiolibro-Curso.pdf"))
sample="\n".join(p.extract_text() or "" for p in pdf.pages[:4])
assert "Fuente: silver/" not in sample
assert "SHA256" not in sample
assert "Capítulo 1." in sample
assert "Audiolibro narrable y referencia" not in sample, "Hay pies técnicos en las páginas TTS"
assert (OUT/"SAA-C03-SOLO-ESCUCHAR.pdf").is_file()
assert (OUT/"SAA-C03-Repaso-Espaciado.pdf").is_file()

# El test propio del suplemento también se ejecuta mediante este validador.
blocks=original.split("PREGUNTA NUEVA")
multiple=[b.split("PAUSA.")[0] for b in blocks[1:]
          if "Selecciona DOS de CINCO opciones" in b[:180]]
assert len(multiple)==2
for b in multiple:
    for letter in "ABCDE":
        assert f"Alternativa {letter}." in b
print(json.dumps({"result":"PASS","oral_chapters":72,"supplements":1,
    "source_exam_options":sum(raw_options.values()),
    "oral_exam_options":sum(options(spoken).values()),
    "pdf_course_pages":len(pdf.pages),
    "metadata_filtered":audit["fluido"]["counters"].get("metadatos_eliminados",0),
    "reference_chapter_preserved_only_in_documentary":True},ensure_ascii=False))
