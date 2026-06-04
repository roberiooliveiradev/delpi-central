from app.application.services.chat_knowledge_candidate_service import (
    ChatKnowledgeCandidateService,
)


class FakeCandidateRepo:
    def __init__(self):
        self.rows: dict[int, dict] = {}
        self._seq = 0

    def find_active_duplicate(self, *, candidate_type, term, scope, project_id=None):
        for row in self.rows.values():
            if (
                row["candidateType"] == candidate_type
                and row["term"] == term
                and row["scope"] == scope
                and row["status"] in {"pending", "auto_approved"}
            ):
                return row
        return None

    def create(self, **kwargs):
        self._seq += 1
        row = {
            "id": self._seq,
            "candidateType": kwargs["candidate_type"],
            "inputText": kwargs["input_text"],
            "term": kwargs.get("term"),
            "proposedRule": kwargs.get("proposed_rule"),
            "proposedMeaning": kwargs.get("proposed_meaning"),
            "confidence": kwargs.get("confidence"),
            "evidenceCount": kwargs.get("evidence_count", 1),
            "riskLevel": kwargs.get("risk_level", "low"),
            "scope": kwargs.get("scope", "global"),
            "projectId": str(kwargs["project_id"]) if kwargs.get("project_id") else None,
            "status": kwargs.get("status", "pending"),
            "source": kwargs.get("source", "auto"),
            "evidence": kwargs.get("evidence"),
        }
        self.rows[row["id"]] = row
        return row

    def bump_evidence(self, candidate_id, *, confidence=None, example=None):
        row = self.rows[candidate_id]
        row["evidenceCount"] += 1
        if confidence is not None:
            row["confidence"] = confidence
        return row

    def get(self, candidate_id):
        return self.rows.get(candidate_id)

    def update_status(self, candidate_id, *, status, reviewer_id=None, promoted_term_id=None):
        row = self.rows.get(candidate_id)
        if not row:
            return None
        row["status"] = status
        if promoted_term_id is not None:
            row["promotedTermId"] = promoted_term_id
        return row

    def list_candidates(self, *, status=None, candidate_type=None, limit=50, offset=0):
        items = list(self.rows.values())
        return items, len(items)


class FakeVocabRepo:
    def __init__(self):
        self.terms: list[dict] = []

    def upsert_term(self, **kwargs):
        row = {"id": len(self.terms) + 1, **kwargs}
        self.terms.append(row)
        return row


def _service():
    return ChatKnowledgeCandidateService(
        candidate_repository=FakeCandidateRepo(),
        vocabulary_repository=FakeVocabRepo(),
    )


def test_register_creates_pending_candidate():
    service = _service()
    result = service.register_candidate(
        {
            "candidateType": "term_definition",
            "term": "lousa",
            "inputText": "lousa significa canvas",
            "proposedMeaning": "canvas do chat",
            "confidence": 0.9,
            "scope": "project",
        }
    )

    assert result["status"] == "pending"
    assert result["term"] == "lousa"
    assert result["confidence"] == 0.9


def test_register_blocks_unsafe_candidate():
    service = _service()
    result = service.register_candidate(
        {
            "candidateType": "term_definition",
            "term": "senha",
            "inputText": "minha senha é 123456",
            "confidence": 0.9,
        }
    )

    assert result == {"blocked": True, "reason": "secret_detected", "riskLevel": "high"} or result["blocked"]


def test_register_accumulates_evidence_on_duplicate():
    service = _service()
    payload = {
        "candidateType": "normalization_rule",
        "term": "como vc s chama",
        "inputText": "como vc s chama",
        "confidence": 0.4,
        "scope": "global",
        "evidence": {"examples": ["como vc s chama"]},
    }

    first = service.register_candidate(payload)
    second = service.register_candidate(payload)

    assert first["id"] == second["id"]
    assert second["evidenceCount"] == 2
    assert second["confidence"] > 0.4


def test_promote_creates_vocabulary_term_and_marks_promoted():
    service = _service()
    created = service.register_candidate(
        {
            "candidateType": "term_definition",
            "term": "transforma",
            "inputText": "transforma significa modulo de engenharia",
            "proposedMeaning": "modulo de engenharia",
            "confidence": 0.9,
            "scope": "project",
        }
    )

    result = service.promote_candidate(created["id"], reviewer_id=None)

    assert result["candidate"]["status"] == "promoted"
    assert result["term"]["approved"] is True
    assert result["term"]["type"] == "term_definition"


def test_promote_with_override_sets_correction():
    service = _service()
    created = service.register_candidate(
        {
            "candidateType": "normalization_rule",
            "term": "como vc s chama",
            "inputText": "como vc s chama",
            "confidence": 0.4,
        }
    )

    result = service.promote_candidate(
        created["id"],
        reviewer_id=None,
        normalized_override="como voce se chama",
    )

    assert result["term"]["normalized_term"] == "como voce se chama"
    assert result["term"]["approved"] is True
