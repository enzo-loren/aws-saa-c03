#!/usr/bin/env python3
"""Vista oral del audiocurso: eliminaciones clasificadas, sin tocar los originales.

El apéndice documental conserva TODAS las fuentes y su texto literal. Aquí se
descartan únicamente referencias, navegación y repetición optativa; se preservan
las explicaciones, tablas, cifras, preguntas, alternativas y respuestas.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import re

INTRO=(
  "AWS Certified Solutions Architect, nivel Associate. Preparación para el examen SAA C03.\n\n"
  "Aprenderás a seleccionar arquitecturas de AWS según la seguridad, la resiliencia, "
  "el rendimiento y el costo."
)
CHAPTER=re.compile(r"^CAPÍTULO (\d+)\. (.*)$")
RECAP=re.compile(r"^Recordatorio (\d+):\s*(.*)$")
SOURCE=re.compile(r"^Fuente:\s*",re.I)
SOURCES_HEADING=re.compile(r"^(?:Sección\.\s*)?(?:Fuentes? oficiales(?:\b|\s*\()|Trazabilidad completa del dominio\b)",re.I)
TECH=re.compile(r"^(?:SHA256:|FUENTE DOCUMENTAL:|REFERENCIA EXHAUSTIVA)",re.I)
WEB=re.compile(r"^https?://\S+$",re.I)
PREFIX={
 "Sección. ":"",
 "Comparación. ":"",
 "Descripción visual. ":"El diagrama presenta: ",
 "Pregunta de práctica. ":"Pregunta: ",
 "Respuesta razonada. ":"Respuesta: ",
 "Fragmento técnico. ":"Ejemplo técnico: ",
}
def digest(s): return sha256(s.encode("utf8")).hexdigest()
def rephrase(s):
    s=re.sub(r"\s*\(fuente\s+[A-Z]+-\d+\)","",s,flags=re.I)
    s=re.sub(r"\s*\((?:bronze|silver)/[^()]*\)","",s,flags=re.I)
    return re.sub(r"\s+"," ",s).strip()

def listening_text(raw,mode="fluido"):
    if mode not in ("fluido","repaso"): raise ValueError(mode)
    counters=Counter()
    skipped=[]
    out=[INTRO,""]
    source_chapter=0
    current_title=""
    first_heading=False
    in_reference_chapter=False
    in_references=False
    in_reference_section=False
    for line_no,rawline in enumerate(raw.splitlines(),1):
        s=rawline.strip()
        if not s:
            if out[-1]!="":out.append("")
            continue
        if set(s)=={"="}:
            counters["separadores"]+=1
            continue
        chapter=CHAPTER.match(s)
        if chapter:
            source_chapter=int(chapter.group(1))
            in_reference_chapter=(source_chapter==73)
            in_reference_section=False
            in_references=False
            if in_reference_chapter:
                counters["capitulo_de_fuentes_archivado"]+=1
                continue
            current_title=chapter.group(2)
            first_heading=True
            out.extend(["",f"Capítulo {source_chapter}. {current_title}",""])
            counters["capitulos"]+=1
            continue
        if s=="SUPLEMENTO DE COBERTURA EXAMEN SAA-C03. REVISIÓN DEL 17 DE NOVIEMBRE DE 2026.":
            in_reference_chapter=False
            in_references=False
            in_reference_section=False
            out.extend(["","Capítulo 74. Actualizaciones y práctica del examen SAA C03.",""])
            counters["suplementos"]+=1
            continue
        if in_reference_chapter:
            counters["lineas_de_fuentes_archivadas"]+=1
            continue
        if in_reference_section and s.startswith("Sección. ") and not SOURCES_HEADING.match(s):
            in_reference_section=False
        if in_reference_section:
            counters["lineas_bibliograficas"]+=1
            continue
        if s=="Fuentes oficiales de esta actualización:":
            in_references=True
            counters["bibliografias"]+=1
            continue
        if in_references:
            counters["lineas_bibliograficas"]+=1
            continue
        if SOURCES_HEADING.match(s):
            in_reference_section=True
            counters["bibliografias"]+=1
            continue
        if SOURCE.match(s) or TECH.match(s) or WEB.fullmatch(s) or re.match(r"^(?:bronze|silver)/\S+$",s):
            counters["metadatos_eliminados"]+=1
            skipped.append({"line":line_no,"sha256":digest(s),"reason":"metadata"})
            continue
        if (s.startswith("Pregunta anticipatoria:") or
            s.startswith("Referencia bronze del plan") or
            s.startswith("Referencia documental:") or
            s.startswith("La referencia documental exhaustiva empieza") or
            s.startswith("Guía oficial: https://") or
            s.startswith("El audiocurso mantiene el contenido") or
            s.startswith("Cuando oigas PAUSA,") or
            s.startswith("Página integrada desde la guía extendida") or
            s.startswith("A continuación se incluye la documentación textual") or
            s.startswith("Este pack fusiona dos versiones previas") or
            s.startswith("Esta sección actualiza") or
            s.startswith("Este suplemento")):
            counters["textos_de_proceso_omitidos"]+=1
            continue
        if s.startswith("AWS SAA-C03. AUDIOCURSO INTEGRAL.") or s=="FIN DEL CURSO PRINCIPAL.":
            counters["cabeceras_de_proceso"]+=1
            continue
        if s=="PAUSA DE RECUPERACIÓN ACTIVA." or s.startswith("Explica sin mirar el principio más importante de "):
            counters["interrupciones_eliminadas"]+=1
            continue
        if s.startswith("Recordatorio fiel al texto:"):
            counters["repeticiones_intermedias_eliminadas"]+=1
            continue
        if s.startswith("REPASO DE CIERRE."):
            if mode=="repaso":
                out.extend(["","Repasemos las ideas centrales antes de continuar."])
            counters["repasos_de_cierre"]+=1
            continue
        reminder=RECAP.match(s)
        if reminder:
            if mode=="repaso":out.append("Idea "+reminder.group(1)+". "+rephrase(reminder.group(2)))
            counters["ideas_de_cierre"]+=1
            continue
        if s.startswith("REPASO ESPACIADO."):
            if mode=="repaso":out.append("Recordemos una idea de capítulos anteriores. "+s[len("REPASO ESPACIADO. "):])
            counters["repasos_espaciados"]+=1
            continue
        if s=="Pausa y explica su regla central.":
            if mode=="repaso":out.append("¿Cuál era su idea principal?")
            counters["pausas_de_repaso"]+=1
            continue
        if s.startswith("Respuesta de verificación:"):
            if mode=="repaso":out.append("Una respuesta posible es: "+rephrase(s.split(":",1)[1]))
            counters["respuestas_de_repaso"]+=1
            continue
        if s.startswith("PAUSA."):
            if mode=="repaso":out.append("Piensa tu respuesta antes de continuar.")
            counters["pausas_de_preguntas"]+=1
            continue
        if s.startswith("Sección. "):
            heading=s[len("Sección. "):]
            if first_heading and heading.casefold()==current_title.casefold():
                first_heading=False
                counters["titulos_duplicados"]+=1
                continue
            first_heading=False
        for original,replacement in PREFIX.items():
            if s.startswith(original):
                s=replacement+s[len(original):]
                counters["etiquetas_naturalizadas"]+=1
                break
        s=re.sub(r"^UNIDAD (?:UNO|DOS|TRES|CUATRO)\. ","Lección. ",s)
        if s.startswith("PREGUNTA NUEVA."):s="Pregunta de práctica."+s[len("PREGUNTA NUEVA."):]
        if s.startswith("SOLUCIÓN."):s="Respuesta razonada."+s[len("SOLUCIÓN."):]
        s=rephrase(s)
        if s:
            out.append(s)
            counters["lineas_narradas"]+=1
    result="\n".join(out).strip()+"\n"
    numbering=[int(x) for x in re.findall(r"(?m)^Capítulo (\d+)\. ",result)]
    if numbering!=list(range(1,73))+[74]:
        raise RuntimeError("Capítulos inesperados en vista oral: "+repr(numbering))
    if re.search(r"(?mi)^\s*(?:Fuente:|FUENTE DOCUMENTAL:|SHA256:|Guía oficial: https?://)",result):
        raise RuntimeError("Metadatos en vista oral")
    report={
      "mode":mode,"raw_sha256":digest(raw),"oral_sha256":digest(result),
      "raw_lines":len(raw.splitlines()),"oral_lines":len(result.splitlines()),
      "counters":dict(counters),"skipped_metadata":skipped,
      "editorial_policy":"Capítulo 73, que es un índice de fuentes, solo queda en el PDF documental y en los originales exactos; el audio mantiene 72 capítulos y el suplemento 74.",
      "originals_preserved":"La prueba de integridad reside en integrity_gate.py."
    }
    return result,report
