# Edición SAA-C03 para audiolibro

La rama agrega un generador reproducible que **no cambia ni elimina** archivos del curso original.

## Qué archivo escuchar (importante)

**Usa `SAA-C03-SOLO-ESCUCHAR.pdf` o `SAA-C03-SOLO-ESCUCHAR.txt` para la IA lectora.** Son la edición principal, naturalizada, sin rutas, títulos de procedencia ni hashes. Incluye las explicaciones, tablas narradas, preguntas, alternativas y respuestas del curso y el suplemento oficial 2026.

- `SAA-C03-Capitulos-TTS.zip`: 72 capítulos teóricos en TXT más introducción y suplemento, sin las interrupciones de memoria repetitivas.
- `SAA-C03-Repaso-Espaciado.pdf` y `SAA-C03-Capitulos-REPASO-TTS.zip`: versión opcional con recordatorios y repasos espaciados; la teoría y las alternativas son las mismas.
- `SAA-C03-Audiolibro-COMPLETO.pdf`: **solo archivo documental y auditoría, no para escuchar**. Contiene miles de páginas de fuentes, 1.898 archivos originales adjuntos, material visual y textos de procedencia.
- `SAA-C03-Audiolibro-BASE-TEXTUAL.txt` y `AUDITORIA-ESCUCHA.json`: base sin editar y registro de la transformación oral, para comprobar qué etiquetas quedaron fuera.

El capítulo 73 era exclusivamente la **tabla de trazabilidad bibliográfica de 155 fuentes**. Su contenido sigue íntegro en los originales auditados y en el PDF documental, pero se omite del audiolibro para no leer docenas de rutas y URL. La edición oral recorre los capítulos **1–72 y el nuevo suplemento 74**. Ningún capítulo teórico ni alternativa de pregunta se descarta.

El generador reemplaza «Fuente: silver/...», «Comparación.» y «Sección.» por silencio o lectura más fluida, e impide repetir 444 interrupciones automáticas cada doce bloques. La conservación total de datos se verifica sobre el archivo original, no se confunde con la selección editorial destinada a la voz. Se comprueba que las alternativas de las preguntas son idénticas entre la base original y la edición oral.

## Resultado

Una ejecución exitosa de GitHub Actions deja los archivos descargables en Actions > Audiolibro SAA-C03 > Artifacts y, si el repositorio permite publicaciones, en Releases (etiqueta: audiolibro-saa-c03).

- SAA-C03-Audiolibro-Curso.pdf: edición principal fluida (misma narración que SOLO-ESCUCHAR.pdf), sin etiquetas ni interrupciones automáticas.
- SAA-C03-Audiolibro-COMPLETO.pdf: edición **documental** (no escuchar) con el curso base original, fuentes extraídas, imágenes, PDFs originales y ZIP exacto adjunto.
- SAA-C03-Audiolibro-COMPLETO.txt: extracción exhaustiva para auditorías y búsquedas, no para reproducir en voz.
- SAA-C03-Capitulos-TTS.zip: 72 lecciones narrables más introducción y suplemento (la lección 73 es el índice de fuentes archivado).
- AUDITORIA.json: fuente de cada capítulo, fuente de cada transcripción, duplicados, advertencias y hashes SHA-256 de todos los archivos del repositorio.

En la edición de lectura fluida se preservan preguntas, opciones, soluciones y tablas, pero no se interrumpe cada 12 bloques para hacer repasos. Esos recordatorios y las revisitas a capítulos 1, 3 y 7 atrás se encuentran en la edición separada de repaso espaciado.

## Reproducir la generación

En una copia del repositorio, con Python 3.11 o posterior, git y DejaVuSans instalados:

    pip install -r audiolibro/requirements.txt
    python audiolibro/build.py --out dist

## Límites importantes

El programa transforma texto, tablas y descripciones de diagramas en lectura lineal, pero una transformación automática no puede garantizar que todos los datos presentes exclusivamente dentro de imágenes sean narrables. Los activos gráficos y binarios quedan íntegros en la rama. Una fuente PDF escaneada podría producir una advertencia de texto no extraíble en AUDITORIA.json. El PDF completo ahora adjunta el ZIP exacto de los archivos originales e incorpora las figuras y páginas PDF originales, sujeto a la verificación de integridad de la CI.

No se afirma que este formato garantice aprobar; se recomienda sumar laboratorios, simulacros y revisión activa. El examen SAA-C03 tiene una guía oficial revisada el 29 de octubre de 2026: https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/saa-03-revisions.html. Esta edición conserva el snapshot del repositorio y no reemplaza una auditoría factual contra cada actualización de AWS.

## Contraste con el examen oficial (17-11-2026)

Ver [AUDITORIA-COBERTURA-EXAMEN-2026.md](AUDITORIA-COBERTURA-EXAMEN-2026.md). La guía vigente suma **14** task statements (3+2+5+4). La comparación con las diez preguntas oficiales públicas detectó dos brechas conceptuales en la narración Silver (CORS de S3 y ENI secundaria para failover). La edición nueva añade un suplemento narrado y lo publica como `074-Suplemento-Examen-2026.txt` dentro del ZIP de capítulos. La CI comprueba que el suplemento está íntegro y que sus dos ejercicios de respuesta múltiple tienen cinco alternativas. Las fuentes originales siguen byte a byte intactas; la equivalencia semántica exhaustiva con preguntas reales no es demostrable.
