"""Static/documentation consistency checks for product-suppliers (G2-B)."""
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]


class DocsConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml
        cls.manifest = yaml.safe_load(
            (MODULE / "contracts" / "module.yaml").read_text())

    def test_candidate_source_is_only_dlp04i02(self):
        src = MODULE / "src"
        sources = [p.name for p in src.rglob("*")
                   if p.suffix.upper() in (".PRW", ".TLPP")]
        self.assertEqual(sources, ["DLP04I02.PRW"])

    def test_inventory_docs_exist(self):
        for doc in ("official-model-inventory.md", "sa5-field-matrix.md",
                    "crud-contract-candidate.md",
                    "mvc-lifecycle-investigation.md",
                    "architecture-decision-candidate.md"):
            self.assertTrue((MODULE / "contracts" / doc).exists(), doc)

    def test_sa5_identity_seven_fields(self):
        self.assertEqual(
            self.manifest["sa5_identity"],
            ["A5_FILIAL", "A5_FORNECE", "A5_LOJA", "A5_PRODUTO",
             "A5_FABR", "A5_FALOJA", "A5_REFGRD"])

    def test_decision_and_candidate_state(self):
        self.assertEqual(self.manifest["architecture"]["decision"],
                         "DECISION_REQUIRED")
        self.assertEqual(self.manifest["sources"], ["DLP04I02.PRW"])
        self.assertEqual(self.manifest["development_status"],
                         "SOURCE_CANDIDATE")

    def test_delete_blocked_pending_semantics(self):
        ops = {o["op"]: o for o in self.manifest["operations"]["pending"]}
        self.assertEqual(ops["SA5_REMOVE"]["status"], "BLOCKED")
        self.assertIn("a060VldGrv", ops["SA5_REMOVE"]["note"])

    def test_docs_reference_official_model(self):
        inv = (MODULE / "contracts" / "official-model-inventory.md").read_text()
        for key in ("DMATA061", "MPFormModel", "SetPrimaryKey",
                    "a060VldGrv", "a060LinOk", "MA061MldStruct"):
            self.assertIn(key, inv)

    def test_decision_matrix_documents_alternatives(self):
        dec = (MODULE / "contracts" / "architecture-decision-candidate.md").read_text()
        for alt in ("DMATA061", "Model061", "MATI060", "EXTEND"):
            self.assertIn(alt, dec)


if __name__ == "__main__":
    unittest.main()
