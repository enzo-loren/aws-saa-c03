#!/usr/bin/env python3
"""Genera una edición lineal narrable y una referencia textual auditable."""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re, subprocess, zipfile, shutil
from listening import listening_text
from urllib.parse import unquote
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent.parent
TEXT={".md",".html",".htm",".txt",".csv",".json",".jsonl",".pdf"}
SKIP=("audiolibro/",".github/","silver/assets/")
WS=re.compile(r"\s+")

def tidy(s):
    return WS.sub(" ",html.unescape(s or "")).strip()

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while block:=f.read(1024*1024): h.update(block)
    return h.hexdigest()

def tracked():
    names=subprocess.check_output(["git","ls-files","-z"],cwd=ROOT)
    return [ROOT/n.decode("utf8","surrogateescape") for n in names.split(b"\0") if n]

def html_parts(content,course=False):
    soup=BeautifulSoup(content,"html.parser")
    root=(soup.select_one("main.content") if course else None) or soup.select_one("main") or soup.select_one("article") or soup.body or soup
    for bad in root.select("script,style,noscript,nav,aside,footer,form,.sidebar,.feedback,.mermaid"):
        bad.decompose()
    result=[]
    kinds=["h1","h2","h3","h4","p","summary","li","table","figcaption","img","pre","div"]
    skip_parents={"p","li","summary","table","figcaption","pre"}
    for t in root.find_all(kinds):
        if t.name=="div":
            cls=set(t.get("class",[]))
            if "q-answer" in cls:
                txt=tidy(t.get_text(" ",strip=True))
                if txt: result.append(("respuesta",txt))
                continue
            if t.find_parent(class_="q-answer"): continue
            direct=tidy(" ".join(str(x) for x in t.contents if isinstance(x,NavigableString)))
            if len(direct)>25:
                title=t.select_one(".co-title")
                if title: direct=tidy(title.get_text(" ",strip=True))+". "+direct
                result.append(("clave" if cls.intersection({"exam","warn","tip"}) else "texto",direct))
            continue
        if t.name in {"p","li","summary","figcaption","pre"} and any(t.find_parent(x) for x in skip_parents): continue
        if t.name=="table":
            rows=t.find_all("tr")
            headers=[tidy(x.get_text(" ",strip=True)) for x in rows[0].find_all(["th","td"])] if rows else []
            for pos,row in enumerate(rows):
                if pos==0 and row.find("th"): continue
                cells=[tidy(x.get_text(" ",strip=True)) for x in row.find_all(["th","td"],recursive=False)]
                if not cells: continue
                text=". ".join((a+": "+b) for a,b in zip(headers,cells)) if len(headers)==len(cells) and len(cells)>1 else ". ".join(cells)
                result.append(("tabla",text))
            continue
        if t.name=="img":
            if t.find_parent("figure") and t.find_parent("figure").find("figcaption"): continue
            alt=tidy(t.get("alt",""))
            if alt: result.append(("diagrama","Descripción de imagen: "+alt))
            continue
        if t.name=="pre" and "mermaid" in t.get("class",[]): continue
        if t.name.startswith("h") and t.find_parent("table"): continue
        value=tidy(t.get_text(" ",strip=True))
        if not value: continue
        if t.name=="li" and t.find("li"):
            value=tidy(" ".join(str(x) for x in t.contents if isinstance(x,NavigableString)))
        if not value: continue
        if t.name=="li" and t.parent and t.parent.name=="ol":
            ix=len(t.find_previous_siblings("li"))
            question_page=course and "banco de preguntas" in (soup.title.get_text(" ",strip=True).lower() if soup.title else "")
            option_list="q-options" in t.parent.get("class",[]) or (question_page and len(t.parent.find_all("li",recursive=False)) in (4,5))
            if option_list and ix<26:
                value="Alternativa "+chr(65+ix)+". "+value
            else:
                value="Punto "+str(ix+1)+". "+value
        typ=("titulo" if t.name.startswith("h") else "pregunta" if t.name=="summary" else "diagrama" if t.name=="figcaption" else "codigo" if t.name=="pre" else "texto")
        if t.name=="p" and t.find_parent(class_="callout"):
            wrapper=t.find_parent(class_="callout")
            if set(wrapper.get("class",[])).intersection({"exam","warn","tip"}): typ="clave"
        result.append((typ,value))
    out=[]
    for item in result:
        if not out or out[-1]!=item: out.append(item)
    return out

def read_source(p):
    ext=p.suffix.lower()
    if ext in {".html",".htm"}:
        raw=p.read_text("utf8",errors="replace")
        content="\n\n".join(s for _,s in html_parts(raw))
        if content.strip(): return content
        soup=BeautifulSoup(raw,"html.parser")
        encoded=soup.select_one("#landing-page-xml")
        if encoded and encoded.get("value"):
            decoded=unquote(encoded.get("value"))
            return "\n".join(tidy(t.get_text(" ",strip=True)) for t in BeautifulSoup(decoded,"html.parser").find_all(["title","abstract","list-card-item"]) if tidy(t.get_text(" ",strip=True)))
        return content
    if ext==".pdf":
        reader=PdfReader(str(p),strict=False)
        return "\n\n".join("Página "+str(i+1)+".\n"+(page.extract_text() or "") for i,page in enumerate(reader.pages))
    if ext==".csv":
        with p.open(encoding="utf-8-sig",errors="replace",newline="") as f:
            return "\n".join("Fila "+str(i+1)+": "+" | ".join(row) for i,row in enumerate(csv.reader(f)))
    return p.read_text("utf8",errors="replace")

def all_chapters():
    basedir=ROOT/"silver"
    index=basedir/"index.html"
    soup=BeautifulSoup(index.read_text("utf8"),"html.parser")
    ordered=[index]
    for a in soup.select("nav.sidebar-nav a[href]"):
        href=a.get("href","").split("#")[0].split("?")[0]
        if not href or "://" in href: continue
        candidate=(basedir/href).resolve()
        if candidate.is_file() and candidate.suffix==".html" and basedir.resolve() in candidate.parents and candidate not in ordered:
            ordered.append(candidate)
    for file in sorted(basedir.rglob("*.html")):
        if file not in ordered: ordered.append(file)
    return ordered

def first_sentence(text,max_len=460):
    text=tidy(text)
    if len(text)<=max_len: return text
    sentences=re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ¿¡0-9])",text)
    acc=""
    for sentence in sentences:
        if acc and len(acc)+len(sentence)>max_len: break
        acc=(acc+" "+sentence).strip()
        if len(acc)>=95: break
    return acc or text

def narrate(chapters):
    lines=[
        "AWS SAA-C03. AUDIOCURSO INTEGRAL. EDICIÓN PARA LEER EN VOZ ALTA.",
        "El audiocurso mantiene el contenido del curso web de origen, incluyendo tablas, preguntas, sus opciones y las soluciones razonadas.",
        "Cuando oigas PAUSA, intenta recuperar la respuesta sin leer. La repetición no es accidental; se distribuye para consolidar el aprendizaje.",
        "La referencia documental exhaustiva empieza después de los capítulos de estudio.",
        "Guía oficial: https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03.html",
        ""]
    register=[]
    for number,p in enumerate(chapters,1):
        parts=html_parts(p.read_text("utf8",errors="replace"),True)
        title=next((s for k,s in parts if k=="titulo"),p.stem)
        anchors=[first_sentence(s) for k,s in parts if k=="clave" and len(s)>40 and not s.startswith(("Página integrada","Edición unificada"))][:5]
        if len(anchors)<3:
            anchors.extend(first_sentence(s) for k,s in parts if k=="texto" and len(s)>75 and first_sentence(s) not in anchors)
        anchors=anchors[:5]
        lines+=["", "="*60,"CAPÍTULO "+str(number)+". "+title, "Fuente: "+p.relative_to(ROOT).as_posix(),
                "Pregunta anticipatoria: ¿qué decisión arquitectónica te ayuda a tomar este capítulo?",""]
        n=0
        for typ,value in parts:
            prefix={"titulo":"Sección. ","pregunta":"Pregunta de práctica. ","respuesta":"Respuesta razonada. ",
                    "tabla":"Comparación. ","diagrama":"Descripción visual. ","codigo":"Fragmento técnico. "}.get(typ,"")
            lines += [prefix+value,""]
            n+=1
            if n%12==0 and anchors:
                lines+=["PAUSA DE RECUPERACIÓN ACTIVA.",
                        "Explica sin mirar el principio más importante de "+title+".",
                        "Recordatorio fiel al texto: "+anchors[(n//12-1)%len(anchors)],""]
        lines+=["REPASO DE CIERRE. Intenta recordar antes de escuchar las respuestas."]
        for i,a in enumerate(anchors,1): lines.append("Recordatorio "+str(i)+": "+a)
        lines.append("")
        for distance in [1,3,7]:
            if number>distance:
                prev=register[-distance]
                if prev["anchors"]:
                    lines+=["REPASO ESPACIADO. Vuelve mentalmente al capítulo "+str(prev["number"])+": "+prev["title"]+".",
                            "Pausa y explica su regla central.",
                            "Respuesta de verificación: "+prev["anchors"][0],""]
        register.append({"number":number,"title":title,"source":p.relative_to(ROOT).as_posix(),
                         "blocks":len(parts),"anchors":anchors})
    lines+=["FIN DEL CURSO PRINCIPAL.",
            "A continuación se incluye la documentación textual complementaria íntegra y un registro de procedencia."]
    return "\n".join(lines)+"\n",register

def references(paths,chapters,dest):
    seen={}; entries=[]; warnings=[]
    with dest.open("w",encoding="utf8") as f:
        f.write("REFERENCIA EXHAUSTIVA DEL REPOSITORIO.\nLos activos binarios permanecen intactos en la branch.\n\n")
        for p in paths:
            name=p.relative_to(ROOT).as_posix()
            if p in chapters or name.startswith(SKIP) or p.suffix.lower() not in TEXT: continue
            try: content=read_source(p)
            except Exception as e:
                content=""
                warnings.append(name+": "+repr(e))
            cleaned=tidy(content)
            if not cleaned: warnings.append(name+": sin texto extraíble")
            hashkey=hashlib.sha256(cleaned.encode("utf8")).hexdigest()
            previous=seen.get(hashkey) if cleaned else None
            f.write("\n\n"+"="*60+"\nFUENTE DOCUMENTAL: "+name+"\nSHA256: "+digest(p)+"\n")
            if previous:
                f.write("Texto idéntico a la fuente ya incluida: "+previous+"\n")
            else:
                f.write(content+"\n")
                if cleaned: seen[hashkey]=name
            entries.append({"file":name,"characters":len(content),"duplicate_of":previous})
    return entries,warnings

class PdfWriter:
    def __init__(self,path,title):
        self.c=canvas.Canvas(str(path),pagesize=A4,pageCompression=1)
        self.c.setTitle(title)
        self.c.setAuthor("Enzo Loren: adaptación automática del repositorio AWS SAA-C03")
        self.w,self.h=A4
        self.x=48; self.y=self.h-50; self.page=1
    def newline(self):
        self.c.setFont("DejaVu",8)
        self.c.drawString(48,23,"AWS SAA-C03 | Audiolibro narrable y referencia")
        self.c.drawRightString(self.w-48,23,str(self.page))
        self.c.showPage()
        self.page+=1
        self.y=self.h-50
    def line(self,text):
        if not text.strip():
            self.y-=6
            return
        if set(text.strip())=={"="}:
            self.y-=6
            return
        big=text.startswith("CAPÍTULO ") or text.startswith("REFERENCIA EXHAUSTIVA")
        medium=text.startswith("FUENTE DOCUMENTAL:")
        if big and self.y<self.h-90: self.newline()
        size=12 if big else 9.2 if medium else 9
        height=17 if big else 14
        for chunk in simpleSplit(text,"DejaVu",size,self.w-96) or [""]:
            if self.y<50: self.newline()
            # Dividir identificadores muy largos, que no caben en una línea.
            while pdfmetrics.stringWidth(chunk,"DejaVu",size)>self.w-96 and len(chunk)>1:
                half=max(1,len(chunk)//2)
                self.c.setFont("DejaVu",size)
                self.c.drawString(self.x,self.y,chunk[:half])
                self.y-=height
                chunk=chunk[half:]
                if self.y<50: self.newline()
            self.c.setFont("DejaVu",size)
            self.c.drawString(self.x,self.y,chunk)
            self.y-=height
        if big: self.y-=5
    def append(self,p):
        with p.open(encoding="utf8") as f:
            for line in f: self.line(line.rstrip("\n"))
    def save(self):
        self.newline()
        self.c.save()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="dist")
    a=parser.parse_args()
    out=(ROOT/a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    paths=tracked(); chapters=all_chapters()
    core,register=narrate(chapters)
    base_course=core
    supplement_path=ROOT/"audiolibro"/"suplemento-examen-2026.txt"
    supplement=supplement_path.read_text(encoding="utf8")
    if not supplement.startswith("SUPLEMENTO DE COBERTURA EXAMEN SAA-C03"):
        raise RuntimeError("Suplemento de examen no reconocido")
    raw_course=base_course+"\n\n"+supplement+"\n"
    fluent,fluent_report=listening_text(raw_course,"fluido")
    recalled,recall_report=listening_text(raw_course,"repaso")
    coretxt=out/"SAA-C03-Audiolibro-Curso.txt"
    listen_txt=out/"SAA-C03-SOLO-ESCUCHAR.txt"
    recall_txt=out/"SAA-C03-Repaso-Espaciado.txt"
    unedited=out/"SAA-C03-Audiolibro-BASE-TEXTUAL.txt"
    fulltxt=out/"SAA-C03-Audiolibro-COMPLETO.txt"
    reftxt=out/"SAA-C03-Fuentes-Completas.txt"
    coretxt.write_text(fluent,encoding="utf8")
    listen_txt.write_text(fluent,encoding="utf8")
    recall_txt.write_text(recalled,encoding="utf8")
    unedited.write_text(raw_course,encoding="utf8")
    (out/"AUDITORIA-ESCUCHA.json").write_text(json.dumps({
        "fluido":fluent_report,"repaso":recall_report,
        "audiocurso_original_bytes_preserved_in":unedited.name,
        "referencias_preservadas_en":"SAA-C03-Audiolibro-COMPLETO.pdf"
    },ensure_ascii=False,indent=2),encoding="utf8")
    # 72 capítulos teóricos; el capítulo 73 es un catálogo bibliográfico.
    # Este último permanece íntegro en el PDF técnico, pero no se pronuncia.
    for output_name,narration in [
        ("SAA-C03-Capitulos-TTS.zip",fluent),
        ("SAA-C03-Capitulos-REPASO-TTS.zip",recalled)]:
        markers=list(re.finditer(r"(?m)^Capítulo (\d+)\. ",narration))
        if [int(m.group(1)) for m in markers]!=list(range(1,73))+[74]:
            raise RuntimeError("Error en partición del audiocurso: "+output_name)
        with zipfile.ZipFile(out/output_name,"w",zipfile.ZIP_DEFLATED,compresslevel=8) as bundle:
            bundle.writestr("000-Introduccion.txt",narration[:markers[0].start()])
            for j,m in enumerate(markers):
                end=markers[j+1].start() if j+1<len(markers) else len(narration)
                file=("074-Suplemento-Examen-2026.txt" if int(m.group(1))==74
                      else "Capitulo-"+m.group(1).zfill(2)+".txt")
                bundle.writestr(file,narration[m.start():end])
    references_meta,warnings=references(paths,set(chapters),reftxt)
    with fulltxt.open("w",encoding="utf8") as stream:
        stream.write(raw_course+"\n\n")
        with reftxt.open(encoding="utf8") as source:
            for line in source: stream.write(line)
    audit={
        "source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT).decode().strip(),
        "official_exam_2026_addendum":supplement_path.relative_to(ROOT).as_posix(),
        "addendum_sha256":digest(supplement_path),
        "listening_edition":listen_txt.name,
        "listening_sha256":digest(listen_txt),
        "listening_audit":"AUDITORIA-ESCUCHA.json",
        "tracked_count":len(paths),"chapters":len(chapters),"reference_sources":len(references_meta),
        "warnings":warnings,"chapters_detail":register,"references_detail":references_meta,
        "all_tracked_files":[{"file":p.relative_to(ROOT).as_posix(),"size":p.stat().st_size,"sha256":digest(p)} for p in paths]
    }
    (out/"AUDITORIA.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf8")
    if len(chapters)<70 or any(not r["blocks"] for r in register):
        raise RuntimeError("Cobertura insuficiente de los capítulos silver.")
    font=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not font.exists(): raise RuntimeError("Falta fuente Unicode DejaVuSans")
    pdfmetrics.registerFont(TTFont("DejaVu",str(font)))
    short=PdfWriter(out/"SAA-C03-Audiolibro-Curso.pdf","SAA-C03 | Edición fluida para escuchar")
    short.append(coretxt); short.save()
    shutil.copyfile(out/"SAA-C03-Audiolibro-Curso.pdf",out/"SAA-C03-SOLO-ESCUCHAR.pdf")
    review=PdfWriter(out/"SAA-C03-Repaso-Espaciado.pdf","SAA-C03 | Estudio con repetición espaciada")
    review.append(recall_txt); review.save()
    full=PdfWriter(out/"SAA-C03-Audiolibro-COMPLETO.pdf","SAA-C03 | Archivo documental auditado")
    full.append(fulltxt); full.save()
    print(json.dumps({"chapters":len(chapters),"reference_sources":len(references_meta),
        "warnings":len(warnings),"pdf_bytes":(out/"SAA-C03-Audiolibro-COMPLETO.pdf").stat().st_size}))

if __name__=="__main__": main()
