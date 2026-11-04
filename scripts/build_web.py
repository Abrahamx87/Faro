"""Construye una edición estática sin duplicar las reglas de Faro."""
from __future__ import annotations

import argparse
from importlib.metadata import distribution
from pathlib import Path
from shutil import copy2
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILES = ('pyodide.mjs', 'pyodide.asm.js', 'pyodide.asm.wasm', 'python_stdlib.zip', 'pyodide-lock.json', 'package.json')
SAMPLES = ('legitimo.pdf', 'verificacion.html', 'contenido_disfrazado.pdf')


def build(output: Path, runtime: Path) -> None:
    pdf = distribution('pypdf')
    if pdf.version != '6.10.0':
        raise SystemExit('Instala la versión de pypdf indicada en requirements.txt.')
    for folder in (output, output / 'runtime', output / 'samples'):
        folder.mkdir(parents=True, exist_ok=True)
    for name in RUNTIME_FILES:
        copy2(runtime / name, output / 'runtime' / name)
    for name in ('app.js', 'icon.svg', 'styles.css'):
        copy2(ROOT / 'faro' / 'web' / name, output / name)
    for name in ('transport.js', 'worker.mjs'):
        copy2(ROOT / 'browser' / name, output / name)
    for name in SAMPLES:
        # Se sirven como bytes, sin renderizar el HTML de ejemplo.
        copy2(ROOT / 'faro' / 'samples' / name, output / 'samples' / f'{name}.bin')

    with ZipFile(output / 'faro-engine.zip', 'w', ZIP_DEFLATED) as bundle:
        bundle.write(ROOT / 'faro' / 'engine.py', 'faro_engine.py')
        for entry in pdf.files or ():
            if ('__pycache__' in entry.parts or entry.suffix == '.pyc'
                    or not (entry.parts[0] == 'pypdf' or '.dist-info' in entry.parts[0])):
                continue
            bundle.write(pdf.locate_file(entry), entry.as_posix())

    html = (ROOT / 'faro' / 'web' / 'index.html').read_text(encoding='utf-8')
    html = html.replace('href="/icon.svg"', 'href="./icon.svg"').replace('src="/icon.svg"', 'src="./icon.svg"')
    html = html.replace('href="/styles.css"', 'href="./styles.css"')
    html = html.replace('<script src="/app.js" defer></script>', '<script src="./transport.js" defer></script><script src="./app.js" defer></script>')
    html = html.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n  <meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'wasm-unsafe-eval\'; worker-src \'self\'; connect-src \'self\'; style-src \'self\'; img-src \'self\' data:; object-src \'none\'; base-uri \'none\'; form-action \'none\'; frame-src \'none\'">')
    html = html.replace('El archivo se analiza en el equipo que ejecuta Faro.', 'El archivo se analiza dentro de tu navegador.')
    html = html.replace('El motor los recibe en memoria y no contacta los enlaces que contienen.', 'Se revisan dentro del navegador, sin enviarlos a un servidor ni abrir sus enlaces.')
    html = html.replace('El contenido no se ejecuta. Límite de análisis: 15 segundos.', 'El primer inicio carga el motor. Después, cada análisis tiene un límite de 15 segundos.')
    html = html.replace('Los límites de memoria y CPU se aplican en Linux/macOS. El aislamiento de proceso no constituye una sandbox de malware.', 'La edición web usa un proceso de trabajo del navegador que se detiene al superar el límite de tiempo. No constituye una sandbox de malware.')
    html = html.replace('Código abierto</span></footer>', '<a href="https://github.com/Abrahamx87/Faro" aria-label="Código abierto en GitHub">Código abierto ↗</a></span></footer>')
    (output / 'index.html').write_text(html, encoding='utf-8')
    (output / '.nojekyll').touch()
    copy2(ROOT / 'LICENSE', output / 'LICENSE.txt')
    (output / 'AVISOS.txt').write_text(
        'Faro: licencia MIT, código fuente https://github.com/Abrahamx87/Faro\n'
        'Pyodide 0.27.7: MPL-2.0, código fuente https://github.com/pyodide/pyodide/tree/0.27.7\n'
        'pypdf 6.10.0: BSD-3-Clause, licencia incluida en faro-engine.zip.\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    build(args.output, args.runtime)
