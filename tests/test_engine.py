import io
import unittest
import zipfile
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject

from faro.engine import MAX_BYTES, analyze
from faro.service import isolated_analysis

SAMPLES = Path(__file__).parents[1] / "faro" / "samples"

def pdf_with_action(action=None, encrypted=False):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    if action:
        writer._root_object[NameObject("/OpenAction")] = DictionaryObject({NameObject("/S"):NameObject(action), NameObject("/JS"):TextStringObject("/* muestra inofensiva */")})
    if encrypted:
        writer.encrypt("solo-pruebas")
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()

def office(parts):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml", '<w:document xmlns:w="urn:test"><w:p>Documento normal</w:p></w:document>')
        for name, content in parts.items():
            z.writestr(name, content)
    return stream.getvalue()

class EngineTests(unittest.TestCase):
    def test_legitimate_pdf(self):
        r = analyze((SAMPLES / "legitimo.pdf").read_bytes(), "legitimo.pdf")
        self.assertEqual((r["status"],r["risk"],r["score"]), ("complete","low",0))

    def test_html_demo_explains_credential_risk(self):
        r = analyze((SAMPLES / "verificacion.html").read_bytes(), "verificacion.html")
        self.assertEqual(r["risk"],"high")
        self.assertEqual(r["score"],60)
        self.assertTrue(all(s["explanation"] and s["evidence"] for s in r["signals"]))
        self.assertTrue(all(link["host"].endswith(".invalid") for link in r["links"]))

    def test_disguised_content(self):
        r=analyze((SAMPLES / "contenido_disfrazado.pdf").read_bytes(),"contenido_disfrazado.pdf")
        self.assertEqual(r["file"]["type"],"html")
        self.assertIn("file.extension_mismatch",[s["id"] for s in r["signals"]])

    def test_repeated_signals_do_not_inflate_score(self):
        r=analyze(b"Urgente "*200+b"http://127.0.0.1/a "*100,"nota.txt")
        self.assertEqual(r["score"],25)
        self.assertEqual(len(r["links"]),1)

    def test_real_host_after_userinfo(self):
        r=analyze(b"https://banco.example@receptor.example.invalid/login","nota.txt")
        self.assertEqual(r["links"][0]["host"],"receptor.example.invalid")
        self.assertIn("url.userinfo",[s["id"] for s in r["signals"]])

    def test_unknown_binary_never_low_risk(self):
        r=analyze(b"MZ\x00\x00\xff\x00","reporte.pdf.exe")
        self.assertEqual(r["status"],"unsupported")
        self.assertNotEqual(r["risk"],"low")

    def test_invalid_pdf_is_incomplete(self):
        r=analyze(b"%PDF-1.7\nNo es un PDF real","roto.pdf")
        self.assertEqual((r["status"],r["risk"]),("partial","unknown"))

    def test_encrypted_pdf_is_not_safe(self):
        r=analyze(pdf_with_action(encrypted=True),"cifrado.pdf")
        self.assertEqual((r["status"],r["risk"]),("partial","unknown"))

    def test_pdf_objects(self):
        r=analyze(pdf_with_action("/JavaScript"),"acciones.pdf")
        self.assertIn("pdf.javascript",[s["id"] for s in r["signals"]])
        self.assertIn("pdf.auto_action",[s["id"] for s in r["signals"]])

    def test_office_relationships(self):
        r=analyze(office({"word/_rels/document.xml.rels":'<Relationships xmlns="urn:test"><Relationship Type="attachedTemplate" TargetMode="External" Target="https://destino.example.invalid/template.dotm"/></Relationships>'}),"clase.docx")
        self.assertEqual(r["file"]["type"],"docx")
        self.assertIn("office.remote_template",[s["id"] for s in r["signals"]])

    def test_macros_are_presence_only_and_partial(self):
        r=analyze(office({"word/vbaProject.bin":b"inofensivo"}),"clase.docm")
        self.assertEqual(r["status"],"partial")
        self.assertIn("office.macros",[s["id"] for s in r["signals"]])

    def test_xml_entities_rejected(self):
        r=analyze(office({"word/extra.xml":'<!DOCTYPE x [<!ENTITY a "b">]><x>&a;</x>'}),"clase.docx")
        self.assertEqual(r["status"],"partial")
        self.assertTrue(any("DTD" in w for w in r["warnings"]))

    def test_zip_expansion_rejected(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("word/data.xml","A"*300000)
        r=analyze(stream.getvalue(),"bomba.docx")
        self.assertEqual((r["status"],r["risk"]),("partial","unknown"))

    def test_link_limit_marks_partial(self):
        r=analyze(" ".join(f"https://destino{i}.example.invalid" for i in range(205)).encode(),"links.txt")
        self.assertEqual(len(r["links"]),200)
        self.assertEqual(r["status"],"partial")

    def test_empty_and_large_rejected(self):
        for data in (b"",b"x"*(MAX_BYTES+1)):
            with self.assertRaises(ValueError):
                analyze(data,"archivo.txt")

    def test_isolated_process(self):
        r=isolated_analysis(b"Hola, mundo.","hola.txt")
        self.assertEqual(r["status"],"complete")
        self.assertEqual(len(r["file"]["sha256"]),64)

if __name__=="__main__":
    unittest.main()
