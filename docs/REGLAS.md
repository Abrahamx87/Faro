# Catálogo de reglas

Fuente única: `faro/engine.py`. Cada regla suma sus puntos **una sola vez** por archivo, sin importar cuántas veces aparezca el indicador. La puntuación total se limita a 100. Los pesos son heurísticos y **no están calibrados** con un conjunto representativo de phishing real (consulta [VALIDATION.md](VALIDATION.md)).

Umbrales de lectura: 0–19 pocas señales · 20–49 revisión recomendada · 50–100 precaución alta. Si el análisis es parcial o el formato no es compatible y hay menos de 20 puntos, el resultado es **riesgo no determinado**.

| Regla | Qué indica | Severidad | Puntos | Falsos positivos frecuentes |
| --- | --- | --- | --- | --- |
| `file.extension_mismatch` | El nombre sugiere un formato distinto al identificado por el contenido | Alta | 30 | Archivos renombrados por error; extensiones poco habituales |
| `file.double_extension` | Nombre como `factura.pdf.exe`: la extensión final cambia el tipo aparente. Se evalúa solo con el nombre, también en binarios no compatibles | Alta | 40 | Nombres descuidados de archivos legítimos |
| `html.password` | El HTML incluye un campo de contraseña | Media | 20 | Formularios de inicio de sesión legítimos guardados como archivo |
| `html.credential_destination` | Un formulario con contraseña envía a un destino de red (`http://`, `https://` o `//`) | Alta | 35 | Páginas de inicio de sesión guardadas desde un sitio real |
| `html.link_mismatch` | El texto del enlace muestra una dirección y el destino es otro dominio | Alta | 25 | Enlaces de seguimiento o acortadores de correo legítimo |
| `html.hidden_frame` | `iframe` oculto (ancho 0, `display:none` o `hidden`) | Media | 15 | Marcos de analítica o de integración |
| `html.redirect` | `meta refresh`: el documento cambia de página automáticamente | Media | 10 | Páginas de migración o de cortesía |
| `pdf.javascript` | Acción `/JavaScript` o clave `/JS` en el PDF | Media | 20 | Formularios PDF con validación |
| `pdf.launch` | Acción `/Launch` que intenta abrir un recurso externo | Alta | 45 | Poco frecuente en documentos legítimos |
| `pdf.embedded` | Archivos internos dentro del PDF (no se analizan) | Media | 15 | Portafolios PDF y adjuntos legítimos |
| `pdf.auto_action` | `/OpenAction` o `/AA`: acción al abrir o interactuar | Baja | 5 | Navegación y vistas iniciales normales |
| `office.macros` | Existe `vbaProject.bin` (solo presencia; no se descompila) | Alta | 30 | Libros y documentos corporativos con macros legítimas |
| `office.remote_template` | Relación externa de tipo plantilla adjunta | Alta | 30 | Plantillas corporativas alojadas en un servidor |
| `office.embedded` | Objetos en `/embeddings/` (no se analizan) | Media | 15 | Hojas o imágenes OLE incrustadas |
| `url.userinfo` | URL con `usuario@host`: el texto anterior a `@` no es el destino | Alta | 25 | Muy poco frecuente en uso legítimo |
| `url.ip` | El destino es una dirección IP | Media | 15 | Equipos de red y servicios internos |
| `url.http` | Enlace sin cifrado HTTPS | Baja | 5 | Sitios antiguos o internos |
| `url.idn` | Dominio internacionalizado (`xn--`) | Baja | 5 | Dominios legítimos con caracteres no ASCII |
| `url.port` | Puerto distinto de 80 y 443 | Baja | 5 | Servicios de desarrollo y paneles de administración |
| `text.urgency` | Frases como “urgente”, “verifica tu cuenta” o “cuenta suspendida” | Baja | 5 | Avisos legítimos de seguridad |

## Cómo agregar una regla

1. Añade la llamada `add()` en `faro/engine.py` con un identificador estable, explicación en español, peso y evidencia acotada.
2. Agrega la regla a `ruleCatalog` en `faro/web/app.js` y a esta tabla. La prueba `test_rules_catalog.py` falla si falta alguna o si los pesos no coinciden.
3. Escribe una prueba del comportamiento y descríbela en tu pull request.
