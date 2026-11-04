<div align="center">

<img src="faro/web/icon.svg" alt="Faro" width="72">

# Faro

**Claridad antes de abrir.**

Analizador local de señales de phishing en archivos. Un prototipo funcional con reportes explicables, interfaz en español y código abierto.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-347a91?style=flat-square)
![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-0e766e?style=flat-square)
![Estado: prototipo](https://img.shields.io/badge/Estado-Prototipo_acad%C3%A9mico-d5a24c?style=flat-square)

</div>

## Lo que ya funciona

- Carga por selección o arrastre, con límite de 10 MiB.
- Identificación inicial del formato por contenido y estructura.
- Analizadores de PDF, HTML, TXT y Office Open XML (DOCX/XLSX/PPTX y variantes con macros).
- Reglas con puntaje, explicación y evidencia. Cada regla suma una sola vez.
- Huella SHA-256, enlaces desactivados y reporte descargable en JSON.
- Reporte imprimible mediante el diálogo del navegador: **Imprimir / PDF → Guardar como PDF**.
- Historial opcional de resúmenes, guardado exclusivamente en el navegador.
- Tres demostraciones inofensivas procesadas por el mismo motor real.
- Interfaz adaptable, navegación con teclado y compatibilidad con movimiento reducido.
- Análisis en un proceso separado con tiempo y concurrencia limitados.

**Faro detecta indicadores; no certifica que un archivo sea seguro.** La puntuación no es una probabilidad. Un resultado parcial o no compatible aparece de forma explícita. Los pesos todavía no están calibrados con un conjunto representativo de phishing real.

## Inicio rápido

Requisitos: **Python 3.10 o posterior** y un navegador moderno. Node.js no es necesario para utilizar Faro. La primera instalación requiere internet para obtener pypdf; después, la aplicación puede funcionar sin conexión.

Descarga este repositorio como ZIP y descomprímelo, o clónalo. Abre una terminal dentro de la carpeta que contiene `pyproject.toml`.

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m faro serve
```

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m faro serve
```

Abre **http://127.0.0.1:8765**. Para detener la aplicación, pulsa `Ctrl+C` en la terminal. El servidor escucha únicamente en la interfaz local por defecto. Si el puerto está ocupado, añade `--port 8766`.

Faro es una aplicación local de Python con interfaz web: **GitHub almacena el código; GitHub Pages no ejecuta este backend**. El servidor incluido es para demostraciones locales, no para exposición pública.

## Demostración en tres minutos

1. Pulsa **Documento de clase**: observa el formato PDF y la ausencia de las señales evaluadas.
2. Pulsa **Nuevo análisis → Verificación de cuenta**: muestra el formulario de contraseña, el destino de red y el lenguaje de presión. El ejemplo obtiene **60 puntos**, sin que ello represente una probabilidad del 60 %.
3. En **Enlaces**, explica por qué la dirección aparece desactivada. El destino de demostración usa `.invalid`.
4. Revisa **Detalles técnicos** y descarga el reporte JSON.
5. Analiza **Un archivo disfrazado**: el nombre termina en `.pdf`, pero el motor identifica HTML.
6. Si deseas, activa **Guardar un resumen** y abre **Historial**.

Consulta [la guía para exponer](docs/DEMO.md) y [la arquitectura](docs/ARCHITECTURE.md).

## Línea de comandos

Con el entorno virtual activo:

```bash
python -m faro analyze documento.pdf
python -m faro analyze documento.pdf > reporte.json
```

Sin activar el entorno, sustituye `python` por `.venv/bin/python` en Linux/macOS o `.venv\Scripts\python` en Windows. La salida es JSON; los errores de entrada y de recursos terminan con código 2.

## Alcance y límites

| Formato | Análisis disponible | Limitaciones principales |
| --- | --- | --- |
| PDF | Objetos, acciones, enlaces URI y texto | Hasta 100 páginas de texto; sin OCR; no inspecciona adjuntos internos ni PDF cifrado |
| HTML | Formularios, contraseñas, enlaces, redirecciones y marcos ocultos | Revisión estática; no ejecuta JavaScript; HTML malformado u ofuscado puede evadir reglas |
| TXT | Enlaces y lenguaje de urgencia | Texto UTF-8, sin OCR |
| DOCX / XLSX / PPTX | XML, relaciones externas, presencia de macros y objetos embebidos | Sin descompilar macros ni inspeccionar objetos internos; no interpreta todos los campos, fórmulas o funciones de Office |
| ZIP genérico, Office antiguo, ejecutables, imágenes, LNK | Identificación inicial y nombre | Contenido no evaluado |

Límites: 10 MiB de entrada; contenedores Office de hasta 500 entradas y 20 MiB declarados de expansión; relación de compresión máxima 150:1; 200 enlaces; 12 000 objetos PDF; profundidad PDF 35; hasta dos análisis concurrentes y 15 segundos de tiempo de pared por proceso. Linux/macOS añaden límites de 512 MiB de memoria virtual y 12 segundos de CPU. En Windows esos límites de recursos del sistema operativo no se aplican; se conserva el tiempo máximo y el proceso separado.

No incluye antivirus, inteligencia de amenazas, reputación en línea, análisis dinámico ni detección completa de malware. Un archivo legítimo puede activar reglas. Un archivo malicioso puede no activarlas. **Los límites y el proceso separado no constituyen una sandbox de malware.**

## Privacidad

Los archivos se envían desde el navegador al proceso de Faro que tú ejecutas. En el uso local predeterminado, ese proceso está en tu propio equipo. El contenido se procesa en memoria, sin una carpeta de cargas, sin registros de contenido y sin envío a servicios externos. No se visitan los enlaces extraídos.

El historial está desactivado por defecto. Si lo activas, conserva nombre, tamaño, formato, huella, fecha, estado, puntaje y número de señales en `localStorage`; **no conserva el archivo, su contenido ni sus enlaces**. El nombre de un archivo puede contener información privada: usa el historial solo si deseas conservarlo. Los reportes JSON que descargues sí incluyen nombres, enlaces y evidencias; trátalos conforme a su contenido.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas usan archivos sintéticos e inofensivos. Comprueban parsers, detección, duplicación de reglas, estados incompletos, contenedores acotados, cifrado, carga HTTP, cabeceras y restricciones de origen. **No equivalen a una medición de eficacia frente a campañas reales.** Consulta [VALIDATION.md](docs/VALIDATION.md).

## Estructura

```text
faro/
  engine.py          Identificación, extracción y reglas explicables
  service.py         Tiempo máximo y procesos de análisis
  worker.py          Límites del proceso y protocolo en memoria
  server.py          API local e interfaz web
  web/               HTML, CSS y JavaScript sin dependencias externas
  samples/           Tres archivos inofensivos de demostración
tests/               Pruebas del motor y la API
docs/                Arquitectura, validación, reglas y guía de exposición
```

## Equipo y contexto académico

Instituto Tecnológico de Morelia · Campus II · Ingeniería en Ciberseguridad · Desarrollo Sustentable.

- Abraham Alonso García Heredia
- Cristopher Razo Vega
- Hugo Yepez Serrano
- José Abraham Rodríguez Orozco
- Emiliano Nava Mier

El proyecto busca ampliar el acceso a la revisión de archivos y apoyar la educación digital. Su relación con los ODS 4, 8, 9 y 16 es una contribución propuesta, no un impacto cuantitativo ya demostrado.

## Contribuir

Revisa [CONTRIBUTING.md](CONTRIBUTING.md). Para reportar problemas de seguridad, consulta [SECURITY.md](SECURITY.md). Software publicado bajo [licencia MIT](LICENSE).
