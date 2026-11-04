# Validación del prototipo

## Evidencia disponible

La suite automatizada usa `unittest`, sin una dependencia de pruebas adicional. Los archivos son sintéticos y se crean en memoria o se toman de las tres muestras inofensivas incluidas.

Se verifica: PDF legible, detección de formularios y destinos, discrepancia de extensión, reglas sin duplicación, host real con usuario en URL, binarios fuera de alcance, PDF dañado/cifrado/con acciones, relaciones externas de Office, macros como presencia, rechazo de entidades XML, expansión ZIP limitada, límite de enlaces, tamaños vacíos/excesivos, proceso independiente, API de carga real, demostraciones, cabeceras, origen, Host y rutas de lectura restringidas.

La revisión visual debe incluir carga, señales, enlaces, detalles, historial y navegación. La exportación PDF utiliza la función de impresión del navegador, por lo que el usuario elige sus ajustes de página.

## Resultado de esta entrega

- 24 pruebas automatizadas aprobadas en Linux con Python 3.12 y pypdf 6.10.0.
- Interfaz revisada en navegador de escritorio: análisis de HTML y PDF, carga de archivo, enlaces desactivados, historial voluntario y descarga JSON.
- Paquete wheel construido correctamente. La matriz Windows/Python 3.10 se configura para GitHub Actions, pero no se ha ejecutado en este entorno.
- La impresión y el diseño móvil están implementados; no se verificaron visualmente en un dispositivo móvil ni en todos los diálogos de impresión.

## Qué no demuestra esta validación

No se ha medido precisión, sensibilidad, tasa de falsos positivos, eficacia en campañas actuales ni mejora de la confianza de los usuarios. No se debe anunciar una “efectividad” a partir del porcentaje de pruebas que pasan: una prueba comprueba una condición definida, no la cobertura de amenazas reales.

## Plan para contrastar la hipótesis del proyecto

1. Definir un conjunto de archivos legítimos y archivos con indicadores, con etiquetas y procedencia documentadas. Las muestras sintéticas deben reportarse por separado de las reales.
2. Separar datos de ajuste de reglas y datos de evaluación; evitar usar el mismo archivo en ambos grupos.
3. Fijar los umbrales antes de evaluar. Medir verdaderos/falsos positivos y negativos, precisión y sensibilidad, tiempo y porcentaje de archivos incompletos.
4. En una prueba de usabilidad con consentimiento, comparar decisiones de usuarios mediante revisión manual y con Faro. Usar una distribución contrabalanceada de muestras para reducir aprendizaje y sesgo.
5. Registrar aciertos, tiempo, comprensión y confianza; comprobar que la confianza no aumente sin mejorar los aciertos. No pedir abrir contenido peligroso.
6. Documentar tamaño de muestra, limitaciones y resultados sin extrapolar fuera del alcance observado.
