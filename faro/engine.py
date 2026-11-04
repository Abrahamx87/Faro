"""Detección heurística. Nunca abre enlaces ni ejecuta contenido analizado."""
from __future__ import annotations

import hashlib
import io
import ipaddress
import re
import time
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import PurePath
from urllib.parse import urlsplit
from xml.etree import ElementTree

MAX_BYTES = 10 * 1024 * 1024
MAX_EXPANDED = 20 * 1024 * 1024
MAX_MEMBERS = 500
MAX_URLS = 200
MAX_PAGES = 100
VERSION = "0.1.0"
URL_RE = re.compile(r"https?://[^\s<>\"'\x00-\x20]+", re.I)
EXTENSIONS = {"pdf": {".pdf"}, "html": {".html", ".htm"}, "text": {".txt"},
              "docx": {".docx", ".docm"}, "xlsx": {".xlsx", ".xlsm"}, "pptx": {".pptx", ".pptm"}}
LABELS = {"pdf": "Documento PDF", "html": "Documento HTML", "text": "Texto UTF-8",
          "docx": "Documento de Word", "xlsx": "Libro de Excel", "pptx": "Presentación PowerPoint",
          "zip": "Archivo ZIP", "unknown": "Formato no compatible"}


class LimitReached(ValueError):
    pass


class Findings:
    def __init__(self):
        self.signals = {}
        self.links = []
        self._seen_links = set()
        self.warnings = []

    def add(self, ident, title, severity, weight, explanation, evidence):
        if ident not in self.signals:
            self.signals[ident] = {"id": ident, "title": title, "severity": severity,
                                   "weight": weight, "explanation": explanation, "evidence": []}
        evidence = str(evidence)[:300]
        if evidence not in self.signals[ident]["evidence"] and len(self.signals[ident]["evidence"]) < 6:
            self.signals[ident]["evidence"].append(evidence)

    def warn(self, message):
        if message not in self.warnings:
            self.warnings.append(message)

    def link(self, raw, source):
        raw = str(raw).strip()[:2048]
        if not raw.lower().startswith(("http://", "https://")) or raw in self._seen_links:
            return
        if len(self.links) >= MAX_URLS:
            self.warn("Se alcanzó el límite de 200 enlaces; el análisis es parcial.")
            return
        self._seen_links.add(raw)
        try:
            parts = urlsplit(raw)
            host = parts.hostname or ""
            port = parts.port
            host.encode("idna")
        except (ValueError, UnicodeError):
            self.warn("Se encontró un enlace con sintaxis no interpretable.")
            return
        flags = []
        if parts.scheme.lower() == "http":
            flags.append("Sin HTTPS")
            self.add("url.http", "Enlace sin cifrado HTTPS", "low", 5,
                     "HTTP no cifra el transporte. Esta señal por sí sola no demuestra phishing.", raw)
        try:
            ipaddress.ip_address(host)
            flags.append("Dirección IP")
            self.add("url.ip", "Dirección IP como destino", "medium", 15,
                     "Una IP puede ocultar la identidad del servicio; también aparece en usos legítimos.", raw)
        except ValueError:
            pass
        if parts.username is not None:
            flags.append("Usuario en URL")
            self.add("url.userinfo", "Identidad engañosa en el enlace", "high", 25,
                     "El texto anterior a @ no es el dominio de destino. Revisa el host real del enlace.", raw)
        if any(p.startswith("xn--") for p in host.lower().split(".")):
            flags.append("Dominio internacionalizado")
            self.add("url.idn", "Dominio internacionalizado", "low", 5,
                     "Puede ser legítimo; conviene revisar si sus caracteres imitan a otra marca.", raw)
        if port and port not in (80, 443):
            flags.append("Puerto inusual")
            self.add("url.port", "Enlace con puerto poco habitual", "low", 5,
                     "El puerto requiere una revisión contextual; no confirma una amenaza.", raw)
        self.links.append({"url": raw, "host": host, "source": source, "flags": flags})


class HTMLIndicators(HTMLParser):
    def __init__(self, findings):
        super().__init__(convert_charrefs=True)
        self.f = findings
        self.forms = []
        self.form = None
        self.passwords = 0
        self.text = []
        self.skip = 0
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "form":
            self.form = {"action": a.get("action", ""), "password": False}
            self.forms.append(self.form)
        if tag == "input" and a.get("type", "").lower() == "password":
            self.passwords += 1
            if self.form is not None:
                self.form["password"] = True
        for attr in ("href", "src", "action"):
            if a.get(attr):
                self.f.link(a[attr], f"HTML: {tag}/{attr}")
        if tag == "a":
            self.anchor = [a.get("href", ""), ""]
        if tag == "iframe" and (a.get("width") == "0" or "display:none" in a.get("style", "").replace(" ", "").lower() or "hidden" in a):
            self.f.add("html.hidden_frame", "Marco de contenido oculto", "medium", 15,
                       "Un iframe oculto puede cargar contenido que el usuario no ve.", str(a))
        if tag == "meta" and a.get("http-equiv", "").lower() == "refresh":
            self.f.add("html.redirect", "Redirección automática", "medium", 10,
                       "El documento solicita cambiar de página automáticamente.", a.get("content", ""))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        if tag == "form":
            self.form = None
        if tag == "a" and self.anchor:
            target, label = self.anchor
            try:
                shown = URL_RE.search(label)
                if shown and urlsplit(shown[0]).hostname != urlsplit(target).hostname:
                    self.f.add("html.link_mismatch", "El texto y el destino del enlace no coinciden", "high", 25,
                               "El enlace muestra una dirección, pero conduce a otro dominio.", f"Muestra {shown[0]} → destino {target}")
            except ValueError:
                pass
            self.anchor = None

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)
            if self.anchor:
                self.anchor[1] += data


def _scan_text(text, f, source):
    for match in URL_RE.finditer(text):
        f.link(match[0].rstrip(".,;)}]"), source)
    terms = re.findall(r"\b(?:urgente|urgent|verifica tu cuenta|verify your account|cuenta suspendida|account suspended|en las próximas 24 horas)\b", text.lower())
    if terms:
        f.add("text.urgency", "Lenguaje de urgencia o presión", "low", 5,
              "La presión para actuar puede acompañar un engaño. También existe en mensajes legítimos.", ", ".join(sorted(set(terms))))


def _html(data, f):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("windows-1252", errors="replace")
        f.warn("El HTML no está codificado en UTF-8; se usó una interpretación alternativa.")
    parser = HTMLIndicators(f)
    parser.feed(text)
    parser.close()
    if parser.passwords:
        f.add("html.password", "Formulario que solicita una contraseña", "medium", 20,
              "Un archivo adjunto que pide credenciales merece revisión antes de utilizarse.", f"{parser.passwords} campo(s) de contraseña")
    for form in parser.forms:
        if form["password"] and form["action"].strip().startswith(("http://", "https://", "//")):
            f.add("html.credential_destination", "Contraseña enviada a un destino de red", "high", 35,
                  "El formulario del archivo puede enviar credenciales fuera del documento. Confirma su legitimidad por otro medio.", form["action"])
    _scan_text(" ".join(parser.text), f, "Texto visible HTML")
    return {"forms": len(parser.forms), "password_fields": parser.passwords}


def _pdf(data, f):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise LimitReached("La dependencia pypdf no está disponible en este entorno. Instala Faro con sus dependencias para analizar PDF.") from None
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted:
        f.warn("PDF cifrado: no se inspeccionó su contenido. No se intentó obtener la contraseña.")
        return {"encrypted": True}
    root = reader.trailer["/Root"]
    visited = set()
    counter = [0]

    def walk(obj, depth=0):
        from pypdf.generic import DictionaryObject, ArrayObject, IndirectObject
        if depth > 35:
            f.warn("Se alcanzó el límite de profundidad de objetos PDF.")
            return
        if isinstance(obj, IndirectObject):
            key = (obj.idnum, obj.generation)
            if key in visited:
                return
            visited.add(key)
            obj = obj.get_object()
        counter[0] += 1
        if counter[0] > 12000:
            raise LimitReached("Demasiados objetos PDF para el prototipo.")
        if isinstance(obj, DictionaryObject):
            action = str(obj.get("/S", ""))
            if action == "/JavaScript" or "/JS" in obj:
                f.add("pdf.javascript", "JavaScript incorporado en el PDF", "medium", 20,
                      "El PDF contiene una acción de script. No se ejecutó y puede tener usos legítimos.", "Objeto PDF: /JavaScript o /JS")
            if action == "/Launch":
                f.add("pdf.launch", "Acción para abrir un recurso externo", "high", 45,
                      "El documento incluye una acción Launch, que requiere revisar el recurso que intenta abrir.", "Objeto PDF: /S /Launch")
            if "/OpenAction" in obj or "/AA" in obj:
                f.add("pdf.auto_action", "Acciones automáticas en el PDF", "low", 5,
                      "Se detectó una acción al abrir o interactuar. Puede ser navegación legítima.", "/OpenAction o /AA")
            if "/EmbeddedFiles" in obj or str(obj.get("/Type", "")) == "/EmbeddedFile":
                f.add("pdf.embedded", "Archivo adjunto dentro del PDF", "medium", 15,
                      "El PDF contiene archivos internos. El prototipo no analiza su contenido.", "/EmbeddedFiles o /EmbeddedFile")
                f.warn("No se inspeccionaron los archivos embebidos dentro del PDF.")
            if "/URI" in obj:
                f.link(str(obj["/URI"]), "Acción URI del PDF")
            for key, value in obj.items():
                if key not in ("/Parent", "/P"):
                    walk(value, depth + 1)
        elif isinstance(obj, ArrayObject):
            for value in obj:
                walk(value, depth + 1)

    walk(root)
    count = len(reader.pages)
    if count > MAX_PAGES:
        f.warn(f"Solo se inspeccionó texto de las primeras {MAX_PAGES} páginas.")
    budget = 0
    for page in reader.pages[:MAX_PAGES]:
        content = page.get_contents()
        if content and len(content.get_data()) > MAX_EXPANDED:
            raise LimitReached("Contenido PDF expandido superior al límite del prototipo.")
        text = page.extract_text() or ""
        budget += len(text)
        if budget > MAX_EXPANDED:
            raise LimitReached("Texto PDF superior al límite de extracción.")
        _scan_text(text, f, "Texto del PDF")
    return {"pages": count, "encrypted": False, "objects_checked": counter[0]}


def _open_zip(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    members = z.infolist()
    if len(members) > MAX_MEMBERS:
        z.close()
        raise LimitReached("El contenedor supera el límite de 500 entradas.")
    if sum(m.file_size for m in members) > MAX_EXPANDED or any(m.file_size > MAX_EXPANDED or (m.compress_size and m.file_size / m.compress_size > 150) for m in members):
        z.close()
        raise LimitReached("El contenedor supera el límite de expansión o compresión.")
    if any(m.flag_bits & 1 for m in members):
        z.close()
        raise LimitReached("El contenedor está cifrado; no se inspeccionó su contenido.")
    return z


def _office(z, f):
    parts = 0
    for member in z.infolist():
        name = member.filename
        if name.lower().endswith("vbaproject.bin"):
            f.add("office.macros", "Proyecto de macros incorporado", "high", 30,
                  "El documento contiene macros. Se detectó su presencia; no se ejecutaron ni descompilaron.", name)
            f.warn("El código de las macros no fue inspeccionado.")
        if "/embeddings/" in name.lower():
            f.add("office.embedded", "Objeto embebido en el documento", "medium", 15,
                  "Hay un archivo interno que requiere revisión independiente.", name)
            f.warn("No se inspeccionó el contenido de los objetos embebidos de Office.")
        if not name.endswith((".xml", ".rels")):
            continue
        raw = z.read(member)
        if re.search(br"<!\s*(?:DOCTYPE|ENTITY)", raw, re.I):
            raise LimitReached("XML con declaraciones DTD o entidades: análisis detenido.")
        root = ElementTree.fromstring(raw)
        parts += 1
        texts = []
        for item in root.iter():
            if item.tag.endswith("}Relationship") and item.get("TargetMode", "").lower() == "external":
                target = item.get("Target", "")
                f.link(target, f"Relación externa: {name}")
                if "attachedtemplate" in item.get("Type", "").lower():
                    f.add("office.remote_template", "Plantilla externa de Office", "high", 30,
                          "El archivo solicita una plantilla externa. Este recurso no se descargó.", target)
            if item.text:
                texts.append(item.text)
        _scan_text(" ".join(texts), f, f"Texto Office: {name}")
    return {"xml_parts": parts, "container_entries": len(z.infolist())}


def analyze(data: bytes, filename: str):
    started = time.perf_counter()
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Selecciona un archivo no vacío de hasta 10 MiB.")
    filename = str(filename).replace("\\", "/").rsplit("/", 1)[-1][:180] or "archivo"
    f = Findings()
    kind, status, details = "unknown", "complete", {}
    z = None
    try:
        if data.startswith(b"%PDF-"):
            kind = "pdf"
        elif data.startswith((b"PK\x03\x04", b"PK\x05\x06")):
            kind = "zip"
            z = _open_zip(data)
            names = set(z.namelist())
            if "[Content_Types].xml" in names:
                for prefix, candidate in (("word/", "docx"), ("xl/", "xlsx"), ("ppt/", "pptx")):
                    if any(n.startswith(prefix) for n in names):
                        kind = candidate
                        break
        else:
            text = data.decode("utf-8-sig", errors="strict")
            if "\x00" not in text and sum(c.isprintable() or c in "\r\n\t" for c in text) / len(text) > .90:
                kind = "html" if re.search(r"<(?:!doctype\s+html|html\b|head\b|body\b|form\b)", text[:65536], re.I) else "text"
        suffix = PurePath(filename).suffix.lower()
        if kind in EXTENSIONS and suffix not in EXTENSIONS[kind]:
            f.add("file.extension_mismatch", "La extensión no coincide con el contenido", "high", 30,
                  "El nombre sugiere un formato diferente al identificado. Puede ser un error o un intento de disfrazar el archivo.", f"Extensión: {suffix or '(sin extensión)'} · contenido: {LABELS[kind]}")
        if re.search(r"\.(?:pdf|docx?|xlsx?|jpg|png)\.(?:exe|scr|com|lnk|hta|js|vbs)$", filename, re.I):
            f.add("file.double_extension", "Nombre con doble extensión engañosa", "high", 40,
                  "La extensión final cambia el tipo aparente del archivo.", filename)
        if kind == "pdf":
            details = _pdf(data, f)
        elif kind == "html":
            details = _html(data, f)
        elif kind == "text":
            _scan_text(text, f, "Texto del archivo")
            details = {"characters": len(text)}
        elif kind in ("docx", "xlsx", "pptx"):
            details = _office(z, f)
        else:
            status = "unsupported"
            f.warn("Formato fuera del alcance: no se evaluó su contenido. Se admiten PDF, HTML, TXT y Office Open XML; no ZIP genérico, Office antiguo, imágenes, ejecutables ni accesos directos.")
    except UnicodeDecodeError:
        status = "unsupported"
        f.warn("Formato binario o codificación fuera del alcance del prototipo.")
    except Exception as exc:
        status = "partial"
        f.warn(str(exc)[:250] if isinstance(exc, LimitReached) else "No se pudo completar la lectura de la estructura. El archivo podría estar dañado o usar características no compatibles.")
    finally:
        if z:
            z.close()
    if f.warnings and status == "complete":
        status = "partial"
    score = min(100, sum(s["weight"] for s in f.signals.values()))
    risk = "high" if score >= 50 else "medium" if score >= 20 else "low"
    if status != "complete" and score < 20:
        risk = "unknown"
    return {"schema_version": 1, "engine_version": VERSION,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "file": {"name": filename, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "type": kind, "type_label": LABELS[kind]},
            "status": status, "score": score, "risk": risk,
            "signals": list(f.signals.values()), "links": f.links, "details": details,
            "warnings": f.warnings, "duration_ms": round((time.perf_counter() - started) * 1000),
            "limitations": ["La puntuación es una suma heurística; no es una probabilidad de phishing.",
                            "La ausencia de señales no garantiza que un archivo sea seguro.",
                            "No incluye antivirus, reputación de dominios, OCR ni análisis dinámico.",
                            "No abre enlaces, descarga recursos ni ejecuta macros o scripts."]}
