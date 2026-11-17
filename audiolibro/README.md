# Edición SAA-C03 para audiolibro

La rama agrega un generador reproducible que **no cambia ni elimina** archivos del curso original.

## Resultado

Una ejecución exitosa de GitHub Actions deja los archivos descargables en Actions > Audiolibro SAA-C03 > Artifacts y, si el repositorio permite publicaciones, en Releases (etiqueta: audiolibro-saa-c03).

- SAA-C03-Audiolibro-Curso.pdf: todas las páginas del curso silver, en orden de estudio y formato legible por síntesis de voz, con repasos.
- SAA-C03-Audiolibro-COMPLETO.pdf: curso narrado y referencia textual de la biblioteca de documentación, incluidos Markdown, HTML, PDF, TXT, CSV y JSON.
- SAA-C03-Audiolibro-COMPLETO.txt: extracción completa para motores de voz o una IA.
- SAA-C03-Capitulos-TTS.zip: 73 capítulos separados más introducción, para alimentar a una IA lectora por partes.
- AUDITORIA.json: fuente de cada capítulo, fuente de cada transcripción, duplicados, advertencias y hashes SHA-256 de todos los archivos del repositorio.

La información reiterada se presenta como preguntas de recuerdo, repasos al cerrar cada capítulo y revisitas a capítulos previos, separados 1, 3 y 7 capítulos. Se preservan las preguntas con sus respuestas y se leen las tablas por filas.

## Reproducir la generación

En una copia del repositorio, con Python 3.11 o posterior, git y DejaVuSans instalados:

    pip install -r audiolibro/requirements.txt
    python audiolibro/build.py --out dist

## Límites importantes

El programa transforma texto, tablas y descripciones de diagramas en lectura lineal, pero una transformación automática no puede garantizar que todos los datos presentes exclusivamente dentro de imágenes sean narrables. Los activos gráficos y binarios quedan íntegros en la rama. Una fuente PDF escaneada podría producir una advertencia de texto no extraíble en AUDITORIA.json. El PDF completo transcribe la información textual extraíble, no contiene copias de archivos binarios.

No se afirma que este formato garantice aprobar; se recomienda sumar laboratorios, simulacros y revisión activa. El examen SAA-C03 tiene una guía oficial revisada el 29 de octubre de 2026: https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/saa-03-revisions.html. Esta edición conserva el snapshot del repositorio y no reemplaza una auditoría factual contra cada actualización de AWS.

## Contraste con el examen oficial (17-11-2026)

Ver [AUDITORIA-COBERTURA-EXAMEN-2026.md](AUDITORIA-COBERTURA-EXAMEN-2026.md). La guía vigente suma **14** task statements (3+2+5+4). La comparación con las diez preguntas oficiales públicas detectó dos brechas conceptuales en la narración Silver (CORS de S3 y ENI secundaria para failover). La edición nueva añade un suplemento narrado y lo publica como `074-Suplemento-Examen-2026.txt` dentro del ZIP de capítulos. La CI comprueba que el suplemento está íntegro y que sus dos ejercicios de respuesta múltiple tienen cinco alternativas. Las fuentes originales siguen byte a byte intactas; la equivalencia semántica exhaustiva con preguntas reales no es demostrable.
