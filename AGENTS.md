# Guía de trabajo para Faro

- **Antes de empezar, lee [docs/CONTEXTO.md](docs/CONTEXTO.md)** (contexto, invariantes, flujo de trabajo y estado). Al terminar tu sesión, añade una fila a su registro de traspaso.
- `faro/engine.py` es la única fuente de reglas y puntuación. La aplicación local y la edición web comparten ese motor.
- La web se construye con `npm ci` y `npm run build:web` después de instalar `requirements.txt`. Su código de conexión está en `browser/`; `dist/` es salida generada y no se versiona.
- Ejecuta `python -m unittest discover -s tests -v` antes de proponer cambios. Para cambios web, prueba los tres ejemplos y un archivo seleccionado en el navegador.
- Conserva la privacidad: no envíes archivos a servicios externos, no visites enlaces extraídos y no guardes el contenido de entrada. Los ejemplos deben ser inofensivos y usar `.invalid` para destinos ficticios.
- Explica las señales en español. Si no se puede revisar un archivo, muestra el límite; nunca presentes un puntaje bajo como garantía de seguridad.
- Mantén pequeños los cambios. Describe cómo verificaste el comportamiento y deja las contribuciones listas para revisión mediante un pull request.
