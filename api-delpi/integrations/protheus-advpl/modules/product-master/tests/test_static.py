"""Static/structural tests for the product-master ADVPL candidate source.

These tests DO NOT prove ADVPL compilation, ExecAuto semantics or ERP
persistence — they verify structure, contract and safety invariants only.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
SRC = MODULE / "src" / "DLP04I01.PRW"
EXPECTED_FIELDS = [
    "B1_GRUPO", "B1_COD", "B1_DESC", "B1_REFEREN", "B1_REFCANT", "B1_CODDES",
    "B1_TIPO", "B1_YHOHS", "B1_POSIPI", "B1_LOCPAD", "B1_UM", "B1_SEGUM",
    "B1_TE", "B1_TS", "B1_PICMRET", "B1_CONV", "B1_TIPCONV", "B1_TPMAT",
    "B1_ESPECIE", "B1_EX_NCM", "B1_EX_NBM", "B1_ORIGEM",
]


class StaticSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SRC.read_text(encoding="utf-8")
        cls.upper = cls.text.upper()

    def test_wsrestful_declaration(self):
        self.assertIn("WSRESTFUL DELPIPRODUTO", self.upper)
        self.assertIn("END WSRESTFUL", self.upper)

    def test_published_paths_preserved(self):
        self.assertIn("/v1/IncProduto/incluir".upper(), self.upper)
        self.assertIn("/v1/IncProduto/alterar".upper(), self.upper)

    def test_official_routine_and_operations(self):
        self.assertIn("MATA010", self.upper)
        self.assertIn("MSEXECAUTO", self.upper)
        self.assertRegex(self.text, r"lExecSB1\(self,\s*3\)")
        self.assertRegex(self.text, r"lExecSB1\(self,\s*4\)")

    def test_http_methods(self):
        self.assertIn("WSMETHOD POST INCPROD", self.upper)
        self.assertIn("WSMETHOD PUT INCPROD", self.upper)

    def test_no_unapproved_endpoints(self):
        paths = re.findall(r"PATH\s+'([^']+)'", self.text, re.IGNORECASE)
        self.assertEqual(sorted(paths),
                         ["/v1/IncProduto/alterar", "/v1/IncProduto/incluir"])

    def test_field_contract_22_fields(self):
        fields = re.findall(r'\{"(B1_[A-Z0-9_]+)"', self.text)
        self.assertEqual(len(fields), 22)
        self.assertEqual(sorted(fields), sorted(EXPECTED_FIELDS))

    def test_execauto_private_flags(self):
        self.assertRegex(self.upper, r"PRIVATE\s+LMSERROAUTO")
        self.assertRegex(self.upper, r"PRIVATE\s+LMSHELPAUTO")
        self.assertNotRegex(self.upper, r"LOCAL\s+LMSERROAUTO")

    def test_error_handling_official(self):
        self.assertIn("GETAUTOGRLOG", self.upper)
        self.assertIn("ERRORBLOCK", self.upper)
        self.assertIn("BEGIN SEQUENCE", self.upper)
        self.assertIn("RECOVER", self.upper)

    def test_resource_cleanup(self):
        self.assertIn("RESTAREA", self.upper)
        self.assertIn("FREEOBJ", self.upper)

    def test_json_validation_present(self):
        self.assertRegex(self.upper, r"FROMJSON")
        self.assertIn("JSON VALIDO", self.upper)

    def test_incomplete_payload_policy(self):
        self.assertIn("REPRESENTACAO COMPLETA", self.upper)

    def test_no_direct_sql_or_reclock(self):
        for bad in ("RECLOCK", "TCQUERY", "INSERT INTO", "UPDATE SB1",
                    "DELETE FROM", "DBUSEAREA", "EXECSQL"):
            self.assertNotIn(bad, self.upper, f"forbidden: {bad}")

    def test_no_delpi_api_or_env_artifacts(self):
        for bad in ("HTTP://", "HTTPS://", "192.168.", "10.0.",
                    "F:\\", "C:\\", "PASSWORD", "SENHA", "TOKEN=",
                    "FGRAVALOG", "FJSONTEXT", "ALFXLOG"):
            self.assertNotIn(bad, self.upper, f"forbidden artifact: {bad}")

    def test_no_cross_module_references(self):
        for bad in ("MATA061", "SA5", "DLP04I02", "PRODUCT-SUPPLIERS"):
            self.assertNotIn(bad, self.upper, f"cross-module ref: {bad}")

    def test_response_contract_retob(self):
        for key in ("'code'", "'message'", "'detailedMessage'", "'id'"):
            self.assertIn(key.upper(), self.upper)


class ModuleConsistencyTests(unittest.TestCase):
    def test_module_yaml_declares_source(self):
        import yaml
        manifest = yaml.safe_load(
            (MODULE / "contracts" / "module.yaml").read_text())
        self.assertEqual(manifest["module_id"], "product-master")
        self.assertIn("DLP04I01.PRW", manifest["sources"])
        self.assertEqual(manifest["development_status"], "SOURCE_CANDIDATE")

    def test_no_other_module_files_touched(self):
        suppliers = MODULE.parents[0] / "product-suppliers" / "src"
        self.assertFalse(
            any(p.suffix.upper() in (".PRW", ".TLPP") for p in suppliers.rglob("*")),
            "SA5 module must not receive sources in this task")

    def test_provenance_header(self):
        text = SRC.read_text(encoding="utf-8")
        self.assertIn("SOURCE_CANDIDATE", text)
        self.assertIn("cdb68b0487222823a96162c0e493e442648e21f7", text)


if __name__ == "__main__":
    unittest.main()
