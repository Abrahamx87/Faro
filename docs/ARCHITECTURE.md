# Arquitectura de Faro

La interfaz en español se comunica con una API Python en el mismo origen. El flujo de un análisis es:

1. El navegador verifica el tamaño y envía bytes a `POST /api/analyze`.
2. El servidor comprueba origen, tipo de contenido, tamaño y recepción completa.
3. `service.py` limita a dos análisis concurrentes y crea un proceso independiente.
4. `worker.py` recibe JSON con bytes en base64 mediante stdin; aplica límites POSIX y llama al motor.
5. `engine.py` identifica el formato, ejecuta su analizador, registra reglas sin duplicar y devuelve un reporte JSON.
6. El proceso termina. La interfaz muestra el reporte y permite exportarlo, imprimirlo o guardar un resumen opcional.

No hay una base de datos en el servidor, carpeta de cargas, llamadas a servicios externos o ejecución de contenido del archivo. El historial usa almacenamiento local del navegador. Los archivos de demostración incluidos son la única lectura de muestras desde disco.

## Contrato del reporte (versión 1)

| Campo | Contenido |
| --- | --- |
| `schema_version` / `engine_version` | Versiones del contrato y motor |
| `file` | Nombre normalizado, bytes, SHA-256, tipo y etiqueta |
| `status` | `complete`, `partial` o `unsupported` |
| `risk` | `low`, `medium`, `high` o `unknown` |
| `score` | Suma de pesos distintos, limitada a 100 |
| `signals` | ID de regla, título, severidad, peso, explicación y evidencias |
| `links` | URL, host real, origen del hallazgo y alertas de estructura |
| `details` | Datos específicos del parser |
| `warnings` / `limitations` | Límites observados y límites generales |
| `duration_ms` | Tiempo del motor; no incluye transferencia o creación del proceso |

Un error HTTP o un límite de proceso no produce un reporte favorable: se muestra el error y se explica que el contenido no fue evaluado completamente. Los errores de parseo dentro del motor producen estado parcial y conservan los hallazgos anteriores.

## Extender el motor

Cada nueva regla debe tener un identificador estable, una explicación comprensible, un peso, evidencia limitada y una prueba que cubra el comportamiento relevante. `Findings.add()` evita que repetir un indicador infle el puntaje. Los nuevos analizadores deben registrar cualquier contenido que no hayan podido revisar mediante `warn()`.

## Decisiones de implementación

- Python 3.10+; pypdf fijado en 6.10.0 para reproducibilidad.
- Interfaz HTML/CSS/JS sin CDN, fuentes remotas, telemetría o frameworks.
- Enlaces extraídos como texto desactivado. Todo dato de archivo insertado en HTML se escapa.
- Política CSP, `nosniff`, `no-store`, bloqueo de marcos y verificación de origen en escritura.
- En modo loopback, se restringe Host a localhost/127.0.0.1 para reducir DNS rebinding.
- El servidor de la biblioteca estándar es suficiente para una demostración local, pero no proporciona autenticación, TLS o protección integral para un servicio público.

## Próximas etapas

Calibración de pesos con etiquetas verificadas; pruebas de usabilidad para contrastar la hipótesis; cobertura adicional de campos y fórmulas Office; OCR opcional; análisis de adjuntos internos con presupuesto acumulado; empaquetado de escritorio y revisión de seguridad del servicio.
