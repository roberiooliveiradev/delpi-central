"""Static/structural tests for the product-master ADVPL candidate source.

These tests DO NOT prove ADVPL compilation, ExecAuto semantics or ERP
persistence — they verify structure, contract and safety invariants only.

v2 (full-field CRUD): o catalogo de campos do .PRW deve bater com a
matriz canônica contracts/sb1-field-matrix.json (SX3 TST01==PROD).
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
SRC = MODULE / "src" / "DLP04I01.PRW"
MATRIX = MODULE / "contracts" / "sb1-field-matrix.json"
EXPECTED_FIELDS_V1 = [
    "B1_GRUPO", "B1_COD", "B1_DESC", "B1_REFEREN", "B1_REFCANT", "B1_CODDES",
    "B1_TIPO", "B1_YHOHS", "B1_POSIPI", "B1_LOCPAD", "B1_UM", "B1_SEGUM",
    "B1_TE", "B1_TS", "B1_PICMRET", "B1_CONV", "B1_TIPCONV", "B1_TPMAT",
    "B1_ESPECIE", "B1_EX_NCM", "B1_EX_NBM", "B1_ORIGEM",
]


def _matrix_fields():
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    return data["fields"]


def _write_eligible():
    return {
        f["field"]
        for f in _matrix_fields()
        if f["classification"] in ("READ_WRITE_ELIGIBLE", "CONDITIONAL")
        or f["field"] == "B1_COD"
    }


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
        self.assertIn("WSMETHOD DELETE EXCPROD", self.upper)
        self.assertIn("WSMETHOD GET METAPROD", self.upper)

    def test_endpoint_inventory(self):
        paths = re.findall(r"PATH\s+'([^']+)'", self.text, re.IGNORECASE)
        self.assertEqual(
            sorted(paths),
            [
                "/v1/IncProduto/alterar",
                "/v1/IncProduto/excluir",
                "/v1/IncProduto/incluir",
                "/v1/IncProduto/metadados",
            ],
        )

    def test_field_catalog_matches_matrix(self):
        """Cada entrada {CAMPO,especie} do .PRW bate com o conjunto elegível."""
        entries = re.findall(r'\{"(B1_[A-Z0-9_]+)","([CNDM])"\}', self.text)
        names = {name for name, _ in entries}
        self.assertEqual(len(entries), len(names), "campo duplicado na tabela")
        self.assertEqual(names, _write_eligible())

    def test_field_catalog_covers_v1(self):
        """Os 22 campos do contrato anterior continuam elegíveis (compat)."""
        names = set(re.findall(r'\{"(B1_[A-Z0-9_]+)","', self.text))
        self.assertTrue(set(EXPECTED_FIELDS_V1).issubset(names))

    def test_field_kind_matches_sx3_type(self):
        """Especie na tabela == tipo SX3 (M=memo mapeado como 'M')."""
        sx3 = {f["field"]: f["type"] for f in _matrix_fields()}
        for name, kind in re.findall(r'\{"(B1_[A-Z0-9_]+)","([CNDM])"\}', self.text):
            self.assertEqual(kind, sx3[name], f"tipo divergente: {name}")

    def test_immutable_and_system_fields_absent(self):
        names = set(re.findall(r'\{"(B1_[A-Z0-9_]+)","', self.text))
        for f in _matrix_fields():
            if f["classification"] in ("IMMUTABLE", "SYSTEM_MANAGED") \
                    and f["field"] != "B1_COD":
                self.assertNotIn(f["field"], names, f["field"])

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

    def test_dynamic_field_validation(self):
        # rejeição de campo fora do catálogo + validação por nome (GetNames)
        self.assertIn("GETNAMES", self.upper)
        self.assertIn("CFIELDKIND", self.upper)

    def test_full_representation_put(self):
        self.assertIn("REPRESENTACAO COMPLETA", self.upper)
        self.assertRegex(self.upper, r"NOP\s*==\s*4")

    def test_delete_blocked_not_executed(self):
        """DELETE existe mas não chama ExecAuto — bloco dedicado."""
        self.assertIn("LEXCBLOCKED", self.upper)
        block = self.upper[
            self.upper.index("LEXCBLOCKED(OSELF)"):self.upper.index("LMETAPROD(OSELF)")
        ]
        self.assertNotIn("MSEXECAUTO", block)
        self.assertNotIn("MATA010(X", block)
        self.assertIn("501", block)
        self.assertIn("NOT_HOMOLOGATED", block)

    def test_error_type_taxonomy(self):
        for t in ("client_error", "official_validation", "server_error",
                  "not_homologated"):
            self.assertIn(t, self.text)

    def test_no_errorstack_leak(self):
        # §8: ErrorStack nunca vai para a resposta HTTP
        self.assertNotIn("ERRORSTACK", self.upper)

    def test_autogrlog_sanitized(self):
        self.assertIn("CSANITLOG", self.upper)

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
        for key in ("'code'", "'message'", "'detailedMessage'", "'id'",
                    "'errorType'"):
            self.assertIn(key.upper(), self.upper)

    # --- hardening G2-A (RQ-01..RQ-03) ------------------------------------

    def test_numeric_strict_validation_exists(self):
        self.assertIn("LISNUMSTR", self.upper)
        self.assertRegex(self.upper, r"CCH\s*\$\s*\"\+-\"\s*\.AND\.\s*NI\s*==\s*1")
        self.assertRegex(self.upper, r"NDOTS\s*>\s*1")
        self.assertRegex(self.upper, r"RETURN\s*NDIGITS\s*>\s*0")
        self.assertRegex(self.upper, r'VALTYPE\(XVAL\)\s*==\s*"N"')
        self.assertIn("LISNUMSTR(XVAL)", self.upper)

    def test_numeric_zero_not_treated_as_absent(self):
        self.assertNotRegex(self.upper,
                            r'VALTYPE\(XVAL\)\s*==\s*"C"\s*\.AND\.\s*!EMPTY\(XVAL\)')

    def test_char_fields_require_character_type(self):
        self.assertRegex(self.upper, r'VALTYPE\(XVAL\)\s*==\s*"C"')

    def test_date_fields_validated(self):
        self.assertIn("LISDATESTR", self.upper)
        self.assertIn("AAAAMMDD", self.upper)

    def test_errorblock_restored_on_all_paths(self):
        self.assertGreaterEqual(self.upper.count("ERRORBLOCK(OEXCEPTION)"), 2)
        end_seq = self.upper.rindex("END SEQUENCE")
        tail = self.upper[end_seq:]
        self.assertIn("ERRORBLOCK(OEXCEPTION)", tail)
        self.assertNotIn("RETURN", tail.split("ERRORBLOCK(OEXCEPTION)")[0])

    def test_no_early_return_before_cleanup(self):
        self.assertEqual(self.upper.count("SETRESPONSE"), 3)  # exec + exc + meta
        self.assertEqual(self.upper.count("RESTAREA(AAREA)"), 3)


class ModuleConsistencyTests(unittest.TestCase):
    def test_module_yaml_declares_source(self):
        import yaml
        manifest = yaml.safe_load(
            (MODULE / "contracts" / "module.yaml").read_text())
        self.assertEqual(manifest["module_id"], "product-master")
        self.assertIn("DLP04I01.PRW", manifest["sources"])
        self.assertEqual(manifest["development_status"], "SOURCE_CANDIDATE")

    def test_manifest_candidate_consistency(self):
        import yaml
        manifest = yaml.safe_load(
            (MODULE / "contracts" / "module.yaml").read_text())
        cand = manifest["candidate_source"]
        self.assertEqual(cand["status"], "SOURCE_CANDIDATE")
        self.assertEqual(cand["name"], "DLP04I01.PRW")
        prov = cand["provenance"]
        for key in ("erp_repo", "erp_branch", "erp_path", "erp_blob_sha",
                    "mirror_path", "note"):
            self.assertIn(key, prov)
        self.assertIn("INCONCLUSIVE", prov["erp_head"])

    def test_matrix_completeness(self):
        """Nenhum campo some silenciosamente: 319 no dump, todos classificados."""
        fields = _matrix_fields()
        self.assertEqual(len(fields), 319)
        valid = {"READ_WRITE_ELIGIBLE", "SYSTEM_MANAGED", "CONDITIONAL",
                 "IMMUTABLE", "READ_ONLY", "CALCULATED", "TO_INVENTORY"}
        for f in fields:
            self.assertIn(f["classification"], valid, f["field"])
            self.assertTrue(f["field"].startswith("B1_"))

    def test_matrix_environment_parity(self):
        data = json.loads(MATRIX.read_text(encoding="utf-8"))
        self.assertIn("DELPI_TST01", str(data["dictionary_source"]))
        self.assertIn("IDENTICAL", str(data["dictionary_source"]["parity"]))

    def test_no_other_module_files_touched(self):
        suppliers = MODULE.parents[0] / "product-suppliers" / "src"
        unexpected = [
            p for p in suppliers.rglob("*")
            if p.suffix.upper() in (".PRW", ".TLPP")
            and p.name.upper() != "DLP04I02.PRW"
        ]
        self.assertFalse(
            unexpected,
            "SA5 module must not receive sources in this task")

    def test_provenance_header(self):
        text = SRC.read_text(encoding="utf-8")
        self.assertIn("SOURCE_CANDIDATE", text)
        self.assertIn("cdb68b0487222823a96162c0e493e442648e21f7", text)


class V21ReviewGuards(unittest.TestCase):
    """Guards da revisão independente (v2.1) — defeitos corrigidos."""

    @classmethod
    def setUpClass(cls):
        cls.text = SRC.read_text(encoding="utf-8")
        cls.upper = cls.text.upper()

    def test_empty_date_is_legitimate(self):
        # D vazio e legitimo na SB1; sem o aceite o PUT completo falharia
        # em todo produto com data em branco (defeito comprovado).
        self.assertRegex(
            self.upper, r'LISDATESTR\(XVAL\)\s*\.OR\.\s*EMPTY\(XVAL\)')

    def test_string_literals_are_ascii(self):
        # Respostas HTTP compiladas em CP1252: literal nao-ASCII = mojibake.
        in_block = False
        for n, line in enumerate(self.text.split("\n"), 1):
            s = line.strip()
            if s.startswith("/*") and "*/" not in s and not s.startswith("/*/"):
                in_block = True
            elif "*/" in s:
                in_block = False
                continue
            if in_block or s.startswith("//"):
                continue
            code = s.split("//")[0]
            for m in re.finditer(r'"([^"]*)"', code):
                self.assertTrue(m.group(1).isascii(), f"linha {n}: {m.group(1)}")

    def test_body_read_inside_sequence(self):
        # GetContent dentro do Begin Sequence (throw fora nao recupera).
        seq = self.upper.index("BEGIN SEQUENCE")
        self.assertLess(seq, self.upper.index("OSELF:GETCONTENT()"))
        self.assertLess(seq, self.upper.index("OSELF:SETCONTENTTYPE"))
        # GetContent SEMPRE antes de SetContentType: o HTTPREST consome o
        # buffer do request em SetContentType (regressao TST01 2026-11-19).
        self.assertLess(
            self.upper.index("OSELF:GETCONTENT()"),
            self.upper.index("OSELF:SETCONTENTTYPE"),
        )
        # FromJson retorna .F. mesmo populando o objeto neste build —
        # o legado ignora o retorno (DLP04I01/DLP05W01 no espelho).
        # O parse e validado pelo conteudo, nunca pelo retorno.
        self.assertNotIn("!ODADOS:FROMJSON", self.upper)
        self.assertIn("LEN(ODADOS:GETNAMES())", self.upper)

    def test_sanitlog_no_trailing_separator(self):
        block = self.upper[
            self.upper.index("CSANITLOG(ALOGAUTO)"):self.upper.index("LEXECSB1(OSELF")
        ]
        self.assertIn("LJOIN(ALIN", block)
        self.assertIn("AADD(ALIN", block)

    def test_no_dead_locals(self):
        self.assertNotRegex(self.upper, r"LOCAL\s+NY\s*:=")

    def test_catalog_lookup_without_rebuild(self):
        # cFieldKind recebe o catalogo materializado — sem rebuild por campo.
        self.assertRegex(self.upper, r"CFIELDKIND\(CFIELD,\s*AFIELDS\)")
        self.assertNotRegex(
            self.upper, r"STATIC\s+FUNCTION\s+CFIELDKIND\(CFIELD\)")


if __name__ == "__main__":
    unittest.main()
