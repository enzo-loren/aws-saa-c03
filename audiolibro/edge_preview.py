#!/usr/bin/env python3
"""Muestra verificable de TTS de Edge. Servicio no oficial: puede fallar."""
from __future__ import annotations
import asyncio, hashlib, json
from mutagen.mp3 import MP3
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"audiolibro/suplemento-examen-2026.txt"
OUT=ROOT/"dist-edge-preview"
VOICES=["es-CL-CatalinaNeural","es-CL-LorenzoNeural"]

def sample_text():
    original=SOURCE.read_text(encoding="utf-8")
    section=original.split("UNIDAD UNO. CORS EN AMAZON S3.",1)[1].split("UNIDAD DOS.",1)[0]
    paragraphs=[x.strip() for x in section.split("\n\n") if x.strip()]
    return "Unidad uno. CORS en Amazon S3.\n\n"+"\n\n".join(paragraphs[:3])

async def synthesize(voice,text,path):
    for i in range(3):
        try:
            await edge_tts.Communicate(text,voice=voice,rate="-5%",volume="+0%",pitch="+0Hz").save(str(path))
            return
        except Exception as exc:
            if i==2: raise RuntimeError(f"No fue posible sintetizar {voice}: {type(exc).__name__}: {exc}") from exc
            await asyncio.sleep(2*(i+1))

def ffprobe(path):
    duration=float(MP3(str(path)).info.length)
    if not path.is_file() or path.stat().st_size<4000 or duration<5:
        raise RuntimeError(f"Audio no válido: {path}")
    return duration

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    text=sample_text()
    manifest={"source":"audiolibro/suplemento-examen-2026.txt",
              "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "exact_spoken_sample":text,"spoken_sample_sha256":hashlib.sha256(text.encode()).hexdigest(),
              "engine":"edge-tts (cliente no oficial de Edge Read Aloud)",
              "edge_tts_version":"7.3.1",
              "samples":[]}
    for voice in VOICES:
        output=OUT/("SAA-C03-Preview-"+voice+".mp3")
        await synthesize(voice,text,output)
        manifest["samples"].append({"voice":voice,"file":output.name,
                "duration_s":round(ffprobe(output),2),
                "size_bytes":output.stat().st_size,
                "sha256":hashlib.sha256(output.read_bytes()).hexdigest()})
    (OUT/"MANIFIESTO-AUDIO.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":"PASS","samples":manifest["samples"]},ensure_ascii=False))

if __name__=="__main__":
    asyncio.run(main())
