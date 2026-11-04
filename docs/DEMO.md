# Guion de exposición · 3 a 5 minutos

## Preparación

Instala la dependencia antes de clase, inicia `python -m faro serve` y abre http://127.0.0.1:8765. Prueba las tres demostraciones. Una vez instalado, el funcionamiento habitual no necesita internet. Si vas a compartir la pantalla, revisa que el historial no muestre nombres privados.

## 1. Problema y propuesta · 30 segundos

“Nuestro proyecto se llama Faro. Ayuda a revisar archivos antes de abrirlos. Identifica su formato, busca señales de phishing y explica sus resultados. El análisis ocurre en el equipo que ejecuta la aplicación.”

## 2. Archivo sin indicadores preparados · 30 segundos

Abre **Documento de clase**. Muestra la puntuación y el tipo PDF.

“Este ejemplo no activa las reglas. Eso no significa que Faro garantice seguridad: el reporte solo describe lo que pudo revisar.”

## 3. Formulario simulado · 1 minuto

Pulsa **Nuevo análisis → Verificación de cuenta**.

“El motor encuentra un campo de contraseña, un destino de red para enviarla y palabras de urgencia. Cada señal incluye una explicación y evidencia. Sus pesos suman 60 puntos; no es un porcentaje de probabilidad.”

Abre **Enlaces**. Aclara que `.invalid` identifica un destino de demostración, que el botón de la muestra está inactivo y que Faro no abre ni renderiza su HTML.

## 4. Contenido disfrazado · 30 segundos

Pulsa **Nuevo análisis → Un archivo disfrazado**.

“Aunque el nombre dice PDF, el contenido es HTML. Este contraste genera una señal específica.”

## 5. Evidencias y límites · 1 minuto

Abre **Detalles técnicos**, exporta JSON y muestra **Cómo funciona**.

“Ya tenemos un prototipo funcional y pruebas automáticas con muestras inofensivas. Falta evaluar su eficacia con un conjunto representativo y comprobar si sus reportes ayudan a usuarios sin conocimientos técnicos. No es un antivirus ni una sandbox de malware.”

## Preguntas que puede hacer el profesor

| Pregunta | Respuesta breve |
| --- | --- |
| ¿Es inteligencia artificial? | No. Son reglas estáticas explicables. |
| ¿Detecta todo el phishing? | No. Tiene alcance y limitaciones explícitas. |
| ¿Cómo se calcula el puntaje? | Se suman pesos distintos, con un máximo de 100. Aún falta calibrarlos. |
| ¿Se suben los archivos a internet? | En el uso local predeterminado se reciben en el proceso del mismo equipo, sin servicios externos. |
| ¿Qué pasa con un archivo cifrado? | Se indica que el análisis es parcial; no se presenta como seguro. |
| ¿Ya demostraron la hipótesis? | No todavía: hace falta un estudio comparativo con usuarios. |
| ¿Qué aporta a sustentabilidad? | Acceso gratuito, educación y privacidad. El impacto ambiental aún no está medido. |
| ¿Por qué GitHub? | Control de versiones, colaboración, revisión y distribución del código abierto. |
