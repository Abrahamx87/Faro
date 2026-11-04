# Contribuir a Faro

1. Crea una rama para una mejora concreta.
2. Instala el proyecto en un entorno virtual con `python -m pip install -e .`.
3. Añade una prueba si cambias una regla, parser, límite o contrato de reporte.
4. Ejecuta `python -m unittest discover -s tests -v`.
5. Si cambias la interfaz, revisa escritorio, móvil, teclado y reporte impreso.
6. Describe qué problema resuelves, el comportamiento resultante y cómo lo comprobaste.

Mantén mensajes de interfaz en español, explicaciones accesibles e identificadores de reglas estables. Declara el contenido no revisado. Evita dependencias remotas en la interfaz.

No subas muestras de malware, archivos privados, correos reales, credenciales ni reportes con información sensible. Utiliza muestras sintéticas e inofensivas y dominios `.invalid`.
