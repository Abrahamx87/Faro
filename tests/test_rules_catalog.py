"""El catálogo visible (web y documentación) debe coincidir con las reglas del motor."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
ENGINE = (ROOT / "faro" / "engine.py").read_text(encoding="utf-8")
WEB = (ROOT / "faro" / "web" / "app.js").read_text(encoding="utf-8")
DOCS = (ROOT / "docs" / "REGLAS.md").read_text(encoding="utf-8")

# Reglas registradas con add("id", "título", "severidad", peso, ...)
ENGINE_RULES = {m[0]: int(m[1]) for m in re.findall(r'\.add\(\s*"([a-z_]+\.[a-z_]+)",\s*"[^"]+",\s*"[a-z]+",\s*(\d+)', ENGINE)}
WEB_RULES = {m[0]: int(m[1]) for m in re.findall(r"\['([a-z_]+\.[a-z_]+)','[^']*',(\d+)\]", WEB)}


class RulesCatalogTests(unittest.TestCase):
    def test_engine_rules_were_found(self):
        self.assertGreaterEqual(len(ENGINE_RULES), 20)

    def test_web_catalog_matches_engine(self):
        self.assertEqual(WEB_RULES, ENGINE_RULES)

    def test_documentation_lists_every_rule_with_its_weight(self):
        for ident, weight in ENGINE_RULES.items():
            row = next((line for line in DOCS.splitlines() if f"`{ident}`" in line), None)
            self.assertIsNotNone(row, f"{ident} no aparece en docs/REGLAS.md")
            self.assertIn(f"| {weight} |", row, f"El peso de {ident} no coincide en docs/REGLAS.md")


if __name__ == "__main__":
    unittest.main()
