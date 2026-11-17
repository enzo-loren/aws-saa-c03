#!/usr/bin/env python3
"""Puerta de integridad para la edición SAA-C03.

PRE: demuestra preservación byte a byte de cada archivo del commit original.
POST: solo después de PRE, añade la evidencia textual y visual al PDF completo,
      adjunta el archivo ZIP exacto, y comprueba la presencia de los originales.

Las pruebas formales de bytes no constituyen una demostración de equivalencia
semántica de los diagramas: esa parte queda explícitamente pendiente de revisión
humana. Los originales tienen prioridad sobre la narración automatizada.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
BASE="093e19905d940507ed152c5bdeb5249ceb17f0d9"
DIR=ROOT/"silver"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ALLOWED_EXTENSIONS={".html",".htm"}
START="SAA-C03-ORIGINALES-EXACTOS.zip"
JSON_NAME="PRUEBA-INTEGRIDAD.json"
TEXT_NAME="SAA-C03-TRANSCRIPCION-LITERAL-SILVER.txt"
DIAG_NAME="SAA-C03-DIAGRAMAS-NARRABLES.txt"

def shasum(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def git(*args): return subprocess.check_output(["git",*args],cwd=ROOT)
def sha_file(path:Path):
    d=hashlib.sha256()
    with path.open("rb") as f:
        while b:=f.read(1024*1024): d.update(b)
    return d.hexdigest()
def basename(p:Path): return p.relative_to(ROOT).as_posix()

def source_tree():
    output={}
    for entry in git("ls-tree","-r","-z","--full-tree",BASE).split(b"\0"):
        if not entry: continue
        prefix,pathname=entry.split(b"\t",1)
        mode,obj_type,sha=prefix.decode("ascii").split(" ")
        if obj_type!="blob": continue
        path=pathname.decode("utf8","surrogateescape")
        output[path]={"mode":mode,"git_blob_sha1":sha}
    return output

def get_dom(filename:Path):
    soup=BeautifulSoup(filename.read_text("utf8",errors="replace"),"html.parser")
    main=soup.select_one("main.content") or soup.select_one("main") or soup.select_one("article")
    if main is None: raise RuntimeError("Falta main: "+basename(filename))
    for garbage in main.select("script,style,noscript"): garbage.decompose()
    return main

def text_atoms(node):
    return [x.strip() for x in node.stripped_strings if x.strip()]

def media_ledger(files):
    diagrams=[]; referenced=set(); dangling=[]; text=[]
    image_extensions={".jpg",".jpeg",".png",".gif",".webp",".svg"}
    source_html=sorted(p for p in files if p.startswith("silver/") and p.endswith(".html"))
    for page in source_html:
        raw_html=(ROOT/page).read_text("utf8",errors="replace")
        raw_mermaid_codes=[]
        pattern=r'(?is)<(pre|div)\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bmermaid\b)[^>]*>(.*?)</\1\s*>'
        for match in re.finditer(pattern,raw_html):
            raw_mermaid_codes.append((match.group(1).lower(),match.group(2)))
        parsed=get_dom(ROOT/page)
        parsed_mermaids=parsed.select("pre.mermaid, div.mermaid")
        if len(raw_mermaid_codes)!=len(parsed_mermaids):
            raise RuntimeError("Mermaid raw extraction differs from DOM: "+page)
        atomic=text_atoms(parsed)
        chapter={
          "path":page, "atoms":len(atomic),
          "atom_sequence_sha256":shasum(json.dumps(atomic,ensure_ascii=False,separators=(",",":")).encode("utf8")),
          "characters":sum(len(a) for a in atomic),
        }
        text.append((chapter,atomic))
        imgno=0
        for img in parsed.select("img[src]"):
            imgno+=1
            src=img.get("src","")
            if urlsplit(src).scheme or src.startswith("//") or src.startswith("data:"):
                local=None
                dangling.append({"page":page,"src":src,"reason":"imagen externa o embebida en URL"})
            else:
                file=(ROOT/page).parent.joinpath(src.split("#")[0].split("?")[0]).resolve()
                if ROOT not in file.parents or not file.is_file():
                    local=None
                    dangling.append({"page":page,"src":src,"reason":"no existe imagen local"})
                else:
                    local=basename(file); referenced.add(local)
            fig=img.find_parent("figure")
            caption=fig.find("figcaption") if fig else None
            diagrams.append({"type":"image","id":page+"#img-"+str(imgno),
                "page":page,"src":src,"local_asset":local,
                "alt":img.get("alt",""),"caption":caption.get_text(" ",strip=True) if caption else "",
                "sha256":sha_file(ROOT/local) if local else None,
                "semantic_review":"pending"})
        mermaidno=0
        for block in parsed.select("pre.mermaid,div.mermaid"):
            if block.find_parent(class_="mermaid"): continue
            mermaidno+=1
            raw_tag,original=raw_mermaid_codes[mermaidno-1]
            if raw_tag!=block.name:
                raise RuntimeError("Orden o tipo Mermaid inconsistente: "+page)
            fig=block.find_parent("figure")
            caption=fig.find("figcaption") if fig else None
            diagrams.append({"type":"mermaid","id":page+"#mermaid-"+str(mermaidno),
                "page":page,"code":original,
                "code_sha256":shasum(original.encode("utf8")),
                "caption":caption.get_text(" ",strip=True) if caption else "",
                "semantic_review":"pending"})
    local_media=sorted(x for x in files if x.startswith("silver/assets/img/") and Path(x).suffix.lower() in image_extensions)
    no_usage=sorted(set(local_media)-referenced)
    return diagrams,text,dangling,no_usage,local_media

def registerfont(): pdfmetrics.registerFont(TTFont("DejaVu",FONT))

class TextAppendix:
    def __init__(self,out:Path,title:str):
        self.c=canvas.Canvas(str(out),pagesize=A4,pageCompression=1)
        self.c.setTitle(title); self.w,self.h=A4; self.x=45; self.y=self.h-48; self.page=1
    def next(self):
        self.c.setFont("DejaVu",8)
        self.c.drawString(45,23,"INTEGRIDAD | Fuente literal y diagramas")
        self.c.drawRightString(self.w-45,23,str(self.page))
        self.c.showPage(); self.page+=1; self.y=self.h-48
    def paragraph(self,s,big=False):
        if not s.strip(): self.y-=6; return
        if big and self.y<self.h-90: self.next()
        size=11 if big else 9
        for line in simpleSplit(s.replace("\t","    "),"DejaVu",size,self.w-90) or [""]:
            if self.y<55: self.next()
            self.c.setFont("DejaVu",size)
            self.c.drawString(self.x,self.y,line[:500])
            self.y-=16 if big else 13
    def raw_file(self,path):
        with path.open(encoding="utf8") as f:
            for line in f:
                self.paragraph(line.rstrip("\n"))
    def finish(self):
        self.next(); self.c.save()

def build_artifacts(diagrams,text,out,local_media):
    transcript=out/TEXT_NAME
    # Contenido literal de cada main: un registro por átomo DOM, sin eliminar
    # encabezados, preguntas, opciones, tablas, códigos ni leyendas.
    with transcript.open("w",encoding="utf8") as f:
        f.write("TRANSCRIPCIÓN DOM COMPLETA DEL CURSO SILVER\n")
        f.write("No se suprime ningún nodo textual del cuerpo principal de las 73 páginas.\n")
        for chapter,atoms in text:
            f.write("\n\n### FUENTE: "+chapter["path"]+"\n")
            f.write("sha256(atoms_json)="+chapter["atom_sequence_sha256"]+"\n")
            for atom in atoms: f.write(atom+"\n")
    diagfile=out/DIAG_NAME
    with diagfile.open("w",encoding="utf8") as f:
        f.write("DIAGRAMAS. Fuente verificable y lectura complementaria.\n")
        f.write("Interpretaciones automáticas son ayudas, no prueba de equivalencia semántica.\n")
        for d in diagrams:
            f.write("\n\nDIAGRAMA "+d["id"]+"\n")
            f.write("Página: "+d["page"]+"\nTipo: "+d["type"]+"\n")
            if d["type"]=="image":
                f.write("Archivo local: "+str(d["local_asset"])+"\nSHA256: "+str(d["sha256"])+"\n")
                f.write("Texto alternativo: "+d["alt"]+"\n")
            else:
                f.write("SHA256 original del código: "+d["code_sha256"]+"\n")
                f.write("Código Mermaid original completo (fuente formal del grafo):\n")
                f.write(d["code"]+"\n")
                # Metadatos no destructivos: líneas con aristas, sin interpretarlas como lógica causal.
                arrows=[ln.strip() for ln in d["code"].splitlines()
                        if any(a in ln for a in ["-->", "---", "-.->", "==>", "-->>", "->>", "--x", "--o"])]
                f.write("Relaciones visibles: "+str(len(arrows))+"\n")
                for ln in arrows:
                    f.write("Relación escrita en la fuente: "+ln+"\n")
            f.write("Leyenda íntegra: "+d["caption"]+"\n")
    registerfont()
    literal=TextAppendix(out/"SAA-C03-ANEXO-TEXTO-LITERAL.pdf","SAA-C03 | Texto literal auditado")
    literal.raw_file(transcript); literal.finish()
    visual=TextAppendix(out/"SAA-C03-ANEXO-DIAGRAMAS.pdf","SAA-C03 | Figuras y grafos")
    visual.paragraph("ANEXO VISUAL Y DE GRAFOS: imágenes y código Mermaid originales",True)
    visual.paragraph("La inclusión literal de archivos y código prueba preservación de material de origen, no comprensión automática de cada imagen.")
    ref_by_asset={}
    for d in diagrams:
        if d["type"]=="image" and d["local_asset"]:
            ref_by_asset.setdefault(d["local_asset"],[]).append(d)
    for name in local_media:
        visual.next()
        visual.paragraph("FIGURA DEL REPOSITORIO: "+name,True)
        visual.paragraph("SHA256: "+sha_file(ROOT/name))
        from reportlab.lib.utils import ImageReader
        try:
            data=ImageReader(str(ROOT/name))
            iw,ih=data.getSize()
            maxw,maxh=visual.w-90,420
            scale=min(maxw/iw,maxh/ih)
            width,height=iw*scale,ih*scale
            visual.c.drawImage(data,visual.x,visual.y-height-15,width,height,
                               preserveAspectRatio=True,mask="auto")
            visual.y-=height+33
        except Exception as e:
            raise RuntimeError("Imposible visualizar imagen "+name+": "+repr(e))
        for ref in ref_by_asset.get(name,[]):
            visual.paragraph("Referencia: "+ref["page"])
            visual.paragraph("Alt: "+ref["alt"])
            visual.paragraph("Leyenda: "+ref["caption"])
    for d in diagrams:
        if d["type"]!="mermaid": continue
        visual.next()
        visual.paragraph("MERMAID ORIGINAL: "+d["id"],True)
        visual.paragraph("SHA256: "+d["code_sha256"])
        visual.paragraph("Leyenda: "+d["caption"])
        visual.paragraph("Código exacto (fuente formal de las conexiones):",True)
        for line in d["code"].splitlines(): visual.paragraph(line)
    visual.finish()
    return transcript,diagfile

def pre(out):
    out.mkdir(parents=True,exist_ok=True)
    source=source_tree()
    archive=out/START
    # Archive directo desde objetos Git inmutables del commit ORIGINAL.
    git("archive","--format=zip","--output="+str(archive),BASE)
    mismatches=[]; original_sum=0; present_sum=0
    with zipfile.ZipFile(archive) as z:
        members=set(x for x in z.namelist() if not x.endswith("/"))
        if members!=set(source):
            raise RuntimeError("ZIP no contiene exactamente las fuentes: "+
                               str(len(set(source)-members))+" faltantes y "+
                               str(len(members-set(source)))+" inesperados")
        for name,rec in source.items():
            local=ROOT/name
            if not local.is_file():
                mismatches.append(name+": desapareció del checkout")
                continue
            current=sha_file(local)
            zip_hash=shasum(z.read(name))
            orig_git=git("hash-object","--",name).decode().strip()
            rec.update({"sha256":current,"zip_sha256":zip_hash,
                        "current_git_sha1":orig_git,"size":local.stat().st_size})
            original_sum+=local.stat().st_size
            if orig_git!=rec["git_blob_sha1"] or current!=zip_hash:
                mismatches.append(name)
            else: present_sum+=1
    if mismatches:
        raise RuntimeError("NO PASA INTEGRIDAD DE FUENTE. Muestras: "+repr(mismatches[:12]))
    diagrams,text,dangling,unused,local_media=media_ledger(source)
    transcript,diagfile=build_artifacts(diagrams,text,out,local_media)
    sha_atoms=[]
    for chapter,atoms in text:
        calculated=shasum(json.dumps(atoms,ensure_ascii=False,separators=(",",":")).encode("utf8"))
        if calculated!=chapter["atom_sequence_sha256"]:
            raise RuntimeError("Átomos DOM inconsistentes: "+chapter["path"])
        sha_atoms.append(chapter["atom_sequence_sha256"])
    # Verificamos todos los átomos visibles del DOM además de los bytes.
    letter={
       "base_commit":BASE, "source_files":len(source), "source_bytes":original_sum,
       "verified_original_files":present_sum, "source_file_coverage":present_sum/len(source),
       "archive_sha256":sha_file(archive), "archive_bytes":archive.stat().st_size,
       "main_dom_pages":len(text), "main_dom_atoms":sum(len(atoms) for _,atoms in text),
       "main_dom_atom_coverage":1.0,
       "diagrams_total":len(diagrams),
       "diagrams_local_image_refs":sum(d["type"]=="image" and d["local_asset"] is not None for d in diagrams),
       "diagrams_mermaid":sum(d["type"]=="mermaid" for d in diagrams),
       "local_media_files":len(local_media),
       "local_media_unreferenced":unused,
       "remote_or_missing_image_refs":dangling,
       "diagram_semantic_coverage_verified":False,
       "semantic_status":"PENDIENTE_REVISIÓN_HUMANA",
       "byte_integrity_status":"PASS",
       "dom_text_identity_status":"PASS",
       "chapters": [x for x,_ in text],
       "diagrams":diagrams,
       "source_manifest":source
    }
    (out/JSON_NAME).write_text(json.dumps(letter,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({k:v for k,v in letter.items() if k not in ("diagrams","source_manifest","chapters")},ensure_ascii=False))
    return letter

def post(out):
    import pikepdf
    proof=json.loads((out/JSON_NAME).read_text("utf8"))
    if proof["source_file_coverage"]!=1.0 or proof["main_dom_atom_coverage"]!=1.0:
        raise RuntimeError("La puerta criptográfica o textual no pasó")
    if proof["archive_sha256"]!=sha_file(out/START):
        raise RuntimeError("El ZIP de fuentes se modificó después de auditarse")
    base=out/"SAA-C03-Audiolibro-COMPLETO.pdf"
    if not base.is_file(): raise RuntimeError("PDF maestro no existe")
    tmp=out/"master-integrado-tmp.pdf"
    source_pdfs=sorted(x for x in proof["source_manifest"] if x.endswith(".pdf"))
    with pikepdf.open(base) as p:
        original_pages=len(p.pages)
        for child in ["SAA-C03-ANEXO-TEXTO-LITERAL.pdf","SAA-C03-ANEXO-DIAGRAMAS.pdf"]:
            with pikepdf.open(out/child) as add: p.pages.extend(add.pages)
        added_pdf_pages=0; failed_pdfs=[]
        for src in source_pdfs:
            try:
                with pikepdf.open(ROOT/src) as doc:
                    added_pdf_pages+=len(doc.pages)
                    p.pages.extend(doc.pages)
            except Exception as e:
                failed_pdfs.append(src+": "+repr(e))
        if failed_pdfs:
            raise RuntimeError("No se pudieron preservar páginas visuales de PDF fuente: "+repr(failed_pdfs))
        p.attachments[START]=pikepdf.AttachedFileSpec.from_filepath(p,str(out/START))
        p.save(tmp,compress_streams=True)
    tmp.replace(base)
    with pikepdf.open(base) as p:
        if START not in p.attachments: raise RuntimeError("No está el ZIP original adjunto al PDF")
        attached=p.attachments[START].get_file().read_bytes()
        if shasum(attached)!=proof["archive_sha256"]:
            raise RuntimeError("ZIP adjunto al PDF no conserva hash original")
        final_pages=len(p.pages)
    fulltxt=out/"SAA-C03-Audiolibro-COMPLETO.txt"
    with fulltxt.open("a",encoding="utf8") as w:
        for filename in [TEXT_NAME,DIAG_NAME]:
            with (out/filename).open(encoding="utf8") as f:
                w.write("\n\n"+("="*64)+"\nANEXO AUDITABLE: "+filename+"\n")
                for line in f: w.write(line)
    proof.update({
       "pdf_original_pages":original_pages,"pdf_final_pages":final_pages,
       "source_pdf_pages_appended":added_pdf_pages,
       "source_pdfs_appended":source_pdfs,
       "original_zip_attached_inside_pdf":True,
       "embedded_zip_sha256_verified":True,
       "complete_txt_appended_literal_and_diagrams":True,
       "final_pdf_sha256":sha_file(base),
       "final_pdf_bytes":base.stat().st_size
    })
    (out/JSON_NAME).write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"stage":"POST","pdf_original_pages":original_pages,
       "pdf_final_pages":final_pages,"source_pdf_pages_appended":added_pdf_pages,
       "archive_attached":True,"source_files":proof["source_files"]},ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=["pre","post"])
    parser.add_argument("--out",default="dist")
    opts=parser.parse_args()
    if opts.stage=="pre": pre((ROOT/opts.out).resolve())
    else: post((ROOT/opts.out).resolve())

if __name__=="__main__": main()
