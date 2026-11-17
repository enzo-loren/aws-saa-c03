# Auditoría curricular frente al AWS SAA-C03 (2026-11-17)

Este informe se incorpora **solo a la rama `audiolibro-completo`**. El commit original `093e19905d940507ed152c5bdeb5249ceb17f0d9` y sus 1.898 archivos permanecen intactos. La auditoría criptográfica y visual de los originales se ejecuta mediante `audiolibro/integrity_gate.py`. Esta auditoría nueva evalúa **preparación teórica**, un objetivo distinto de la mera preservación exacta de archivos.

## Veredicto

El audiocurso Silver ofrece una **base amplia** para los cuatro dominios SAA-C03, pero **no puede certificarse como exhaustivo ni suficiente por sí solo para aprobar**. AWS advierte que su guía de examen no es exhaustiva; los exámenes reales son confidenciales.

El temario oficial actual tiene **14 task statements**, no 13: D1:3, D2:2, D3:5, D4:4. El curso incluye material de la tarea 3.5, por lo que el problema original de «13 tareas» es principalmente un error de recuento introductorio.

## Fuentes oficiales

- [Guía AWS SAA-C03](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/solutions-architect-associate-03.html)
- [Seguridad, D1](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/solutions-architect-associate-03-domain1.html)
- [Resiliencia, D2](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/solutions-architect-associate-03-domain2.html)
- [Rendimiento, D3](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/solutions-architect-associate-03-domain3.html)
- [Costos, D4](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/solutions-architect-associate-03-domain4.html)
- [Servicios en alcance](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/saa-03-in-scope-services.html)
- [Revisiones: v1.1 de 2026-10-29](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03/saa-03-revisions.html)
- [Diez preguntas oficiales públicas de 2022 (PDF)](https://d1.awsstatic.com/training-and-certification/docs-sa-assoc/AWS-Certified-Solutions-Architect-Associate_Sample-Questions.pdf)
- [Preparación oficial de AWS Certification](https://aws.amazon.com/certification/certification-prep/)

## Comparación de alcance

La página oficial consultada contiene 119 entradas por categoría y **118 servicios distintos**, porque Redshift se repite en Analytics y Database. De esos 118 nombres, **107** tienen al menos una coincidencia léxica por nombre o alias en el cuerpo de las 73 páginas Silver y **11** no se detectan explícitamente: AWS Data Exchange, AWS Data Pipeline, VMware Cloud on AWS, Amazon EKS Distro, AWS Device Farm, Amazon Comprehend, Amazon Lex, Amazon Polly, Amazon Rekognition, Amazon Textract y Amazon Translate. Esto es un indicador de **mención**, no una certificación de conocimiento. Bronze puede contener fuentes complementarias; eso no demuestra que hayan sido narradas.

La guía D2.2 menciona explícitamente Amazon Comprehend y Amazon Polly como ejemplos de servicios administrados pertinentes. Este contraste vuelve importante su inclusión en el suplemento narrado.

## Contraste con las diez preguntas oficiales públicas

| Nº | Concepto decisivo | Estado en Silver |
|---:|---|---|
| 1 | NAT Gateway + ruta privada | Explicado |
| 2 | Hibernación EC2 y RAM en EBS | Explicado |
| 3 | Mover una ENI secundaria a standby | **Laguna** |
| 4 | CORS configurado en un bucket S3 | **Laguna** |
| 5 | SSE-C y client-side encryption | Explicado |
| 6 | On-Demand frente a Spot no interrumpible | Explicado |
| 7 | SQS para desacoplar productores y escritura BD | Explicado |
| 8 | ALB/ASG y RDS Multi-AZ | Explicado |
| 9 | Step scaling y warmup | Explicado |
| 10 | Aurora replicas y reader endpoint | Explicado |

**8/10** es únicamente el número de conceptos reconocibles entre estas **diez muestras públicas, no representativas**. No es una estimación de la nota de examen.

## Corrección del formato de ejercicios

AWS define preguntas de respuesta múltiple con **cinco o más alternativas** y varias correctas. El banco I de Silver tiene 60 preguntas de una respuesta y cuatro opciones. El banco II añade 24 preguntas; cuatro son «Select TWO», pero cada una solo ofrece cuatro opciones. Esto diverge del formato oficial.

## Mejora aditiva y auditable

El archivo `audiolibro/suplemento-examen-2026.txt` se incorpora **después de los 73 capítulos originales**, al PDF de estudio y como un TXT separado dentro del ZIP para TTS. Añade explicaciones verificadas de **S3 CORS** y **ENI de failover**, corrige las **14 tareas**, explica los nombres **AWS Quick / AWS Quick Sight** anunciados el 9 de noviembre de 2026, menciona brevemente los 11 servicios sin detección y agrega **dos ejercicios originales «Select TWO» con cinco alternativas** y una pregunta de failover. No modifica ni sustituye los originales. La prueba `audiolibro/validate_exam_addendum.py` bloquea la publicación si ese suplemento no aparece intacto o si fallan las comprobaciones de formato.

La protección criptográfica de los originales y la prueba de equivalencia de bytes siguen ejecutándose antes y después de la generación.

**Límite explícito:** esto mejora la correspondencia teórica pública, no demuestra cobertura semántica de cada posible pregunta real ni reemplaza práctica hands-on, el set oficial de AWS Skill Builder o un simulacro independiente.
