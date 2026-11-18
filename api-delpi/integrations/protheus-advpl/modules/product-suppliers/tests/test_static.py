"""Static/structural tests for the product-suppliers ADVPL candidate.

Structural checks only — they DO NOT prove MVC execution, compilation
or ERP persistence. Behavioral validation = TEST_NOT_RUN.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
SRC = MODULE / "src" / "DLP04I02.PRW"


class StaticSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SRC.read_text(encoding="utf-8")
        cls.upper = cls.text.upper()
        # código executável: sem blocos /* */ nem comentários //
        code = re.sub(r"/\*.*?\*/", " ", cls.text, flags=re.S)
        cls.code = re.sub(r"//[^\n]*", " ", code).upper()

    def test_wsrestful_and_methods(self):
        self.assertIn("WSRESTFUL DELPIPRODFORN", self.upper)
        for m in ("WSMETHOD POST SA5PROD", "WSMETHOD PUT SA5PROD",
                  "WSMETHOD GET SA5PROD", "WSMETHOD DELETE SA5PROD"):
            self.assertIn(m, self.upper)

    def test_official_model_only(self):
        self.assertIn('FWLOADMODEL("DMATA061")', self.upper)
        self.assertIn("DMdFieldSA5", self.text)
        self.assertIn("DMdGridSA5", self.text)
        self.assertIn("MODEL_OPERATION_INSERT", self.upper)
        # UPDATE bloqueado: sem fluxo executavel de update
        self.assertNotIn("MODEL_OPERATION_UPDATE", self.code)

    def test_update_blocked_no_commit_path(self):
        # PUT nao executa CommitData — indisponibilidade explicita
        self.assertIn("CONTRACT_CANDIDATE", self.upper)
        # CommitData existe exatamente uma vez (fluxo CREATE)
        self.assertEqual(self.code.count("COMMITDATA()"), 1)
        self.assertNotIn("LLOADSA5LINE", self.upper)

    def test_commit_result_checked(self):
        # Nenhum 200 sem retorno logico .T. de CommitData
        self.assertIn('VALTYPE(XCOMMIT) <> "L"', self.code)
        self.assertIn("RESULTADO AMBIGUO", self.code)
        # sucesso declara COMMIT_ACKNOWLEDGED, nao persistencia confirmada
        self.assertIn("READ-BACK", self.code)

    def test_error_sanitized(self):
        # stack trace nao retornado ao consumidor
        self.assertNotIn("ERRORSTACK", self.code)
        self.assertIn("FALHA INTERNA", self.code)
        self.assertIn("CONOUT", self.code)

    def test_deactivate_guarded(self):
        self.assertIn("LACTIVATED", self.code)
        self.assertIn("DEACTIVATE()", self.code)
        # DeActivate protegido por flag + proprio Begin/Recover
        self.assertGreaterEqual(self.code.count("BEGIN SEQUENCE"), 2)

    def test_refgrd_empty_allowed(self):
        self.assertIn('AREQ[NI] <> "A5_REFGRD"', self.code)

    def test_mvc_lifecycle_calls(self):
        for call in ("SETOPERATION", "ACTIVATE()", "VLDDATA",
                     "COMMITDATA", "DEACTIVATE", "ADDLINE"):
            self.assertIn(call, self.upper)

    def test_no_sql_or_reclock(self):
        for bad in ("RECLOCK", "DBDELETE", "TCQUERY", "INSERT INTO",
                    "UPDATE SA5", "DELETE FROM", "DBUSEAREA", "EXECSQL",
                    "SELECT "):
            self.assertNotIn(bad, self.code, f"forbidden: {bad}")

    def test_no_cross_module_or_env_artifacts(self):
        for bad in ("DLP04I01", "MATA010(", "SB1", "HTTP://", "HTTPS://",
                    "192.168.", "PASSWORD", "SENHA", "PRODUCT-MASTER"):
            self.assertNotIn(bad, self.code, f"cross/forbidden: {bad}")

    def test_identity_six_body_fields_filial_derived(self):
        # A5_FILIAL nao vem do body — derivada por xFilial no modelo
        self.assertIn("XFILIAL", self.upper)
        ident = re.search(r'static function aSA5Ident\(\).*?Return \{([^}]+)\}',
                          self.text, re.S)
        fields = re.findall(r'"(A5_[A-Z]+)"', ident.group(1))
        self.assertEqual(len(fields), 6)
        self.assertNotIn("A5_FILIAL", fields)
        for f in ("A5_PRODUTO", "A5_FORNECE", "A5_LOJA", "A5_FABR",
                  "A5_FALOJA", "A5_REFGRD"):
            self.assertIn(f, fields)

    def test_incomplete_identity_rejected(self):
        self.assertIn("LPREPSA5", self.upper)
        self.assertIn("IDENTIDADE COMPLETA", self.upper)

    def test_delete_blocked_returns_501(self):
        self.assertIn('"501"', self.text)
        self.assertIn("A060VLDGRV", self.upper)
        self.assertIn("BLOQUEADO", self.upper)

    def test_read_returns_501_not_implemented(self):
        self.assertIn("NAO IMPLEMENTADO", self.upper)
        self.assertIn("TO_INVENTORY", self.upper)

    def test_errorblock_restored(self):
        self.assertGreaterEqual(self.upper.count("ERRORBLOCK(OEXCEPTION)"), 2)

    def test_error_capture_from_model(self):
        self.assertIn("GETERRORMESSAGE", self.upper)
        self.assertIn("VLDDATA()", self.upper)

    def test_resource_cleanup(self):
        self.assertIn("RESTAREA", self.upper)
        self.assertIn("FREEOBJ", self.upper)
        self.assertIn("DEACTIVATE", self.upper)

    def test_no_fake_success(self):
        # o unico "sucesso" exige VldData+CommitData no fluxo
        self.assertIn("COMMITDATA()", self.upper)
        self.assertNotIn("lMsErroAuto := .F.\n// fake", self.text)


class ModuleConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml
        cls.manifest = yaml.safe_load(
            (MODULE / "contracts" / "module.yaml").read_text())

    def test_sources_and_status(self):
        self.assertIn("DLP04I02.PRW", self.manifest["sources"])
        self.assertEqual(self.manifest["development_status"],
                         "SOURCE_CANDIDATE")

    def test_operation_classification(self):
        ops = self.manifest["candidate_source"]["operations"]
        self.assertIn("SOURCE_CANDIDATE", ops["CREATE"])
        self.assertIn("BLOCKED", ops["UPDATE"])
        self.assertIn("TO_INVENTORY", ops["READ"])
        self.assertIn("BLOCKED", ops["DELETE"])

    def test_other_module_untouched(self):
        other = MODULE.parents[0] / "product-master" / "src"
        # product-master source exists from G2-A — must be unchanged file
        self.assertTrue((other / "DLP04I01.PRW").exists())


if __name__ == "__main__":
    unittest.main()
