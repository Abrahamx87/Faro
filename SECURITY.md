# Seguridad y alcance

Faro es un prototipo académico de análisis estático. No es una sandbox ni una herramienta validada para manipular malware real. Usa muestras inofensivas para la exposición. El servidor predeterminado solo escucha en 127.0.0.1; no lo expongas como servicio público.

Los límites de proceso reducen errores de disponibilidad, pero no aíslan completamente el acceso al sistema. En Windows no se aplican los límites POSIX de memoria/CPU. Los analizadores dependen también de la seguridad de sus bibliotecas y del entorno Python.

Para comunicar un posible problema, utiliza el canal privado de reporte de vulnerabilidades del repositorio si está habilitado. Si no lo está, contacta al responsable del repositorio por un canal privado previamente acordado. No publiques archivos confidenciales, muestras activas o detalles explotables en una incidencia pública.
