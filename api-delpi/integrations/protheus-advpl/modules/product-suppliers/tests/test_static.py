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
        # MATA061 primario (headless comprovado) + fallback DMATA061
        self.assertIn('FWLOADMODEL("MATA061")', self.upper)
        self.assertIn('FWLOADMODEL("DMATA061")', self.upper)
        self.assertIn("MdFieldSA5", self.text)
        self.assertIn("MdGridSA5", self.text)
        self.assertIn("MODEL_OPERATION_INSERT", self.upper)

    def test_crud_all_ops_via_model(self):
        # CRUD completo: INSERT (POST) + UPDATE (PUT/DELETE) + VIEW (GET)
        for op in ("MODEL_OPERATION_INSERT", "MODEL_OPERATION_UPDATE",
                   "MODEL_OPERATION_VIEW"):
            self.assertIn(op, self.code)
        # CommitData nos fluxos de escrita (CREATE, PUT, DELETE)
        self.assertGreaterEqual(self.code.count("COMMITDATA()"), 3)
        # helpers compartilhados do ciclo
        for fn in ("LLOADSA5MODEL", "LFINDSA5LINE", "LEXECSA5OP"):
            self.assertIn(fn, self.upper)

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

    def test_model_error_not_forwarded_to_consumer(self):
        # detalhe oficial do modelo vai ao log, nao ao body HTTP
        self.assertIn("LMODELERR(OMODEL, CERROLOG)", self.code)
        self.assertIn('CONOUT("DLP04I02 MODEL:', self.code)
        self.assertIn("DETALHE TECNICO NO LOG DO APPSERVER", self.code)
        # respostas usam mensagens estaveis — nenhum RETOBJ recebe o log
        for m in re.finditer(r"RETOBJ\(([^)]*)\)", self.code, re.S):
            self.assertNotIn("CERROLOG", m.group(1))

    def test_json_read_uses_proven_accessor(self):
        # leitura do payload pelo acessor do sibling compilado (DLP04I01)
        self.assertNotIn('ODADOS["', self.code)
        self.assertIn('ODADOS:GETJSONOBJECT("A5_PRODUTO")', self.code)

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

    def test_delete_via_model_deleteline(self):
        # DELETE via modelo oficial — DeleteLine na linha localizada;
        # limite a060VldGrv (ultimo vinculo nao-removivel) documentado
        self.assertIn("DELETELINE()", self.upper)
        self.assertIn("A060VLDGRV", self.upper)
        self.assertNotIn('"501"', self.code)

    def test_read_via_model_view(self):
        # GET via modelo oficial — operacao VIEW + navegacao da grade
        self.assertIn("MODEL_OPERATION_VIEW", self.upper)
        self.assertIn("LEXECSA5OP(SELF", self.upper)
        self.assertNotIn("501", self.code)

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


    def test_body_read_inside_sequence(self):
        # GetContent dentro do Begin Sequence e SEMPRE antes de
        # SetContentType: o HTTPREST consome o buffer do request em
        # SetContentType (regressao TST01 2026-11-19).
        seq = self.upper.index("BEGIN SEQUENCE")
        self.assertLess(seq, self.upper.index("CJSON := OSELF:GETCONTENT()"))
        self.assertLess(
            self.upper.index("CJSON := OSELF:GETCONTENT()"),
            self.upper.index("OSELF:SETCONTENTTYPE"),
        )
        # FromJson retorna .F. mesmo populando o objeto neste build —
        # o legado ignora o retorno (DLP04I01/DLP05W01 no espelho).
        # O parse e validado pelo conteudo, nunca pelo retorno.
        self.assertNotIn("!ODADOS:FROMJSON", self.upper)
        self.assertIn("LEN(ODADOS:GETNAMES())", self.upper)

class ModuleConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml
        cls.manifest = yaml.safe_load(
            (MODULE / "contracts" / "module.yaml").read_text())

    def test_sources_and_status(self):
        self.assertIn("DLP04I02.PRW", self.manifest["sources"])
        self.assertEqual(
            self.manifest["development_status"],
            "PROVEN_RUNTIME / TST01_VALIDATED")

    def test_operation_classification(self):
        ops = self.manifest["candidate_source"]["operations"]
        for op in ("CREATE", "UPDATE", "READ_ADVPL", "DELETE"):
            self.assertIn("PROVEN_RUNTIME", ops[op], op)
        self.assertIn("PROVEN_CODE", ops["READ_API_DELPI"])
        # limite oficial do delete (ultimo vinculo) documentado
        self.assertIn("a060VldGrv", ops["DELETE"])

    def test_pending_operations_consistency(self):
        ops = {o["op"]: o["status"] for o in
               self.manifest["operations"]["pending"]}
        self.assertIn("PROVEN_RUNTIME", ops["SA5_ADD"])
        self.assertIn("PROVEN_RUNTIME", ops["SA5_UPDATE"])
        self.assertIn("PROVEN_RUNTIME", ops["SA5_READ_ADVPL"])
        self.assertIn("PROVEN_RUNTIME", ops["SA5_REMOVE"])

    @unittest.skipUnless(
        (MODULE.parents[0] / "product-master" / "src").exists(),
        "sibling product-master ausente neste layout (ex.: handoff)")
    def test_other_module_untouched(self):
        other = MODULE.parents[0] / "product-master" / "src"
        # product-master source exists from G2-A — must be unchanged file
        self.assertTrue((other / "DLP04I01.PRW").exists())


if __name__ == "__main__":
    unittest.main()
