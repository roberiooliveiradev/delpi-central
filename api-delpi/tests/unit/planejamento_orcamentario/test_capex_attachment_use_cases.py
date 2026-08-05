"""Testes Fase 2B.3 — anexos de investimentos CAPEX."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from app.application.services.planejamento_orcamentario.document_storage import (
    BudgetDocumentStorage,
)
from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.capex_attachment_use_cases import (
    CapexAttachmentUseCases,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetGuidanceAcknowledgementRequiredError,
    CapexAttachmentArchivedError,
    CapexAttachmentExtensionInvalidError,
    CapexAttachmentForbiddenError,
    CapexAttachmentInvestmentArchivedError,
    CapexAttachmentMimeInvalidError,
    CapexAttachmentNotFoundError,
    CapexAttachmentTooLargeError,
    CapexAttachmentTypeInvalidError,
    CapexInvestmentNotFoundError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from tests.unit.planejamento_orcamentario.fake_po_repository_helpers import (
    default_po_cc_seed,
    find_valid_responsibility_in_rows,
    get_capex_plan_by_exercise_cc_from_plans,
    get_org_cost_center_from_store,
    list_org_cost_centers_by_code_from_store,
)


class FakeRepo:
    def __init__(self) -> None:
        self.exercises: dict[str, dict] = {}
        self.active_exercise_id: str | None = None
        self.guidance: dict[str, dict] = {}
        self.acks: set[tuple[str, str]] = set()
        self.ccs: dict[tuple[str, str], dict] = default_po_cc_seed()
        self.responsibilities: list[dict] = []
        self.investments: dict[str, dict] = {}
        self.attachments: dict[str, dict] = {}
        self.audits: list[dict] = []
        self.plans: dict[str, dict] = {}

    def get_capex_plan_by_exercise_cc(
        self, *, exercise_id: str, cost_center_id: str, unit_id: str | None = None
    ):
        return get_capex_plan_by_exercise_cc_from_plans(
            self.plans,
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
        )

    def seed_exercise(self) -> str:
        eid = str(uuid4())
        self.exercises[eid] = {
            "id": eid,
            "year": 2027,
            "name": "PO 2027",
            "status": "open",
            "is_active": True,
        }
        self.active_exercise_id = eid
        return eid

    def seed_guidance(self, exercise_id: str) -> str:
        gid = str(uuid4())
        self.guidance[exercise_id] = {
            "id": gid,
            "exercise_id": exercise_id,
            "version_number": 1,
            "title": "Carta",
            "published_at": "2026-01-01T00:00:00Z",
        }
        return gid

    def seed_responsibility(self, *, user_sub: str, exercise_id: str, cost_center_id: str):
        self.responsibilities.append(
            {
                "id": str(uuid4()),
                "user_sub": user_sub,
                "exercise_id": exercise_id,
                "module": "capex",
                "cost_center_id": cost_center_id,
                "unit_id": "01",
                "area_id": "PROD",
                "is_active": True,
                "valid_from": None,
                "valid_until": None,
            }
        )

    def seed_investment(
        self,
        *,
        exercise_id: str,
        cost_center_id: str = "205",
        status: str = "draft",
        created_by: str = "u1",
    ) -> str:
        iid = str(uuid4())
        self.investments[iid] = {
            "id": iid,
            "exercise_id": exercise_id,
            "unit_id": "01",
            "area_id": "PROD",
            "cost_center_id": cost_center_id,
            "description": "Item",
            "status": status,
            "version": 1,
            "created_by": created_by,
        }
        return iid

    def get_exercise(self, exercise_id: str):
        return deepcopy(self.exercises.get(exercise_id))

    def get_active_exercise(self):
        if not self.active_exercise_id:
            return None
        return deepcopy(self.exercises.get(self.active_exercise_id))

    def get_current_published_guidance(self, exercise_id: str):
        return deepcopy(self.guidance.get(exercise_id))

    def get_acknowledgement(self, *, user_sub: str, guidance_version_id: str):
        if (user_sub, guidance_version_id) in self.acks:
            return {"user_sub": user_sub, "guidance_version_id": guidance_version_id}
        return None

    def get_org_cost_center(self, code: str, *, branch: str | None = None):
        return get_org_cost_center_from_store(self.ccs, code, branch=branch)

    def list_org_cost_centers_by_code(self, code: str):
        return list_org_cost_centers_by_code_from_store(self.ccs, code)

    def find_valid_responsibility(
        self,
        *,
        user_sub,
        exercise_id,
        module,
        cost_center_id,
        unit_id=None,
        on_date=None,
    ):
        return find_valid_responsibility_in_rows(
            self.responsibilities,
            user_sub=user_sub,
            exercise_id=exercise_id,
            module=module,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
            on_date=on_date,
        )

    def get_capex_investment(self, investment_id: str):
        return deepcopy(self.investments.get(investment_id))

    def create_capex_investment_attachment(self, payload: dict[str, Any]):
        if payload.get("idempotency_key"):
            for row in self.attachments.values():
                if (
                    row["investment_id"] == payload["investment_id"]
                    and row.get("idempotency_key") == payload["idempotency_key"]
                ):
                    raise PluginsRepositoryError("duplicate idempotency")
        aid = str(uuid4())
        row = {
            **payload,
            "id": aid,
            "created_at": "t",
            "archived_by": None,
            "archived_at": None,
            "is_active": True,
        }
        self.attachments[aid] = row
        return deepcopy(row)

    def get_capex_investment_attachment(self, attachment_id: str):
        return deepcopy(self.attachments.get(attachment_id))

    def get_capex_investment_attachment_by_idempotency(
        self, *, investment_id: str, idempotency_key: str
    ):
        for row in self.attachments.values():
            if (
                row["investment_id"] == investment_id
                and row.get("idempotency_key") == idempotency_key
            ):
                return deepcopy(row)
        return None

    def list_capex_investment_attachments(self, *, investment_id: str, active_only: bool = True):
        items = [a for a in self.attachments.values() if a["investment_id"] == investment_id]
        if active_only:
            items = [a for a in items if a.get("is_active")]
        # sem storage_key na listagem (como o SELECT real)
        out = []
        for a in items:
            pub = {k: v for k, v in a.items() if k != "storage_key"}
            out.append(deepcopy(pub))
        return out

    def archive_capex_investment_attachment(self, attachment_id: str, *, actor_id: str):
        row = self.attachments.get(attachment_id)
        if not row or not row.get("is_active"):
            raise PluginsRepositoryError("Anexo CAPEX ativo não encontrado.")
        row["is_active"] = False
        row["archived_by"] = actor_id
        row["archived_at"] = "t"
        return deepcopy(row)

    def append_audit(self, **kwargs):
        self.audits.append(kwargs)


def _actor(sub: str = "u1", *, admin: bool = False) -> BudgetActor:
    perms = {"planejamento-orcamentario.access"}
    if admin:
        perms.add("planejamento-orcamentario.admin")
    return BudgetActor(user_id=sub, user_name="User", permissions=frozenset(perms))


def _ready(repo: FakeRepo, *, user: str = "u1", cc: str = "205") -> tuple[str, str]:
    eid = repo.seed_exercise()
    gid = repo.seed_guidance(eid)
    repo.acks.add((user, gid))
    repo.seed_responsibility(user_sub=user, exercise_id=eid, cost_center_id=cc)
    iid = repo.seed_investment(exercise_id=eid, cost_center_id=cc, created_by=user)
    return eid, iid


@pytest.fixture
def ctx(tmp_path):
    repo = FakeRepo()
    storage = BudgetDocumentStorage(base_dir=str(tmp_path))
    uc = CapexAttachmentUseCases(repository=repo, storage=storage)
    return repo, storage, uc


def test_upload_valido(ctx):
    repo, storage, uc = ctx
    eid, iid = _ready(repo)
    out = uc.upload_attachment(
        _actor(),
        investment_id=iid,
        attachment_type="quotation",
        display_name="Orçamento fornecedor",
        description="PDF",
        original_filename="orcamento.pdf",
        content=b"%PDF-1.4 demo",
        mime_type="application/pdf",
    )
    assert out["attachment_type"] == "quotation"
    assert out["display_name"] == "Orçamento fornecedor"
    assert "storage_key" not in out
    assert out["is_active"] is True
    # arquivo no volume
    att = next(iter(repo.attachments.values()))
    path = storage.resolve_file(exercise_id=eid, storage_key=att["storage_key"])
    assert path.is_file()
    assert any(a["action"] == "attachment.uploaded" for a in repo.audits)
    assert all("storage_key" not in (a.get("after_state") or {}) for a in repo.audits)


def test_investimento_inexistente(ctx):
    repo, _storage, uc = ctx
    _ready(repo)
    with pytest.raises(CapexInvestmentNotFoundError):
        uc.upload_attachment(
            _actor(),
            investment_id=str(uuid4()),
            attachment_type="other",
            display_name="X",
            description=None,
            original_filename="a.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
        )


def test_outro_centro_de_custo_idor(ctx):
    repo, _storage, uc = ctx
    eid, iid = _ready(repo, user="u1", cc="205")
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("u2", gid))
    repo.seed_responsibility(user_sub="u2", exercise_id=eid, cost_center_id="210")
    with pytest.raises(CapexInvestmentNotFoundError) as exc:
        uc.upload_attachment(
            _actor("u2"),
            investment_id=iid,
            attachment_type="other",
            display_name="X",
            description=None,
            original_filename="a.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
        )
    assert exc.value.code == "budget_capex_investment_not_found"
    assert any(a["action"] == "attachment.access_denied" for a in repo.audits)


def test_investimento_arquivado_bloqueia_upload(ctx):
    repo, _storage, uc = ctx
    eid = repo.seed_exercise()
    gid = repo.seed_guidance(eid)
    repo.acks.add(("u1", gid))
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    iid = repo.seed_investment(exercise_id=eid, status="archived")
    with pytest.raises(CapexAttachmentInvestmentArchivedError) as exc:
        uc.upload_attachment(
            _actor(),
            investment_id=iid,
            attachment_type="other",
            display_name="X",
            description=None,
            original_filename="a.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
        )
    assert exc.value.code == "budget_capex_investment_archived"


def test_extensao_invalida(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    with pytest.raises(CapexAttachmentExtensionInvalidError) as exc:
        uc.upload_attachment(
            _actor(),
            investment_id=iid,
            attachment_type="other",
            display_name="Exe",
            description=None,
            original_filename="virus.exe",
            content=b"MZ",
            mime_type="application/pdf",
        )
    assert exc.value.code == "budget_capex_attachment_extension_invalid"
    assert any(a["action"] == "attachment.upload_rejected" for a in repo.audits)


def test_mime_invalido(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    with pytest.raises(CapexAttachmentMimeInvalidError) as exc:
        uc.upload_attachment(
            _actor(),
            investment_id=iid,
            attachment_type="other",
            display_name="Bin",
            description=None,
            original_filename="a.pdf",
            content=b"%PDF",
            mime_type="application/x-msdownload",
        )
    assert exc.value.code == "budget_capex_attachment_mime_invalid"


def test_tamanho_excedido(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    with pytest.raises(CapexAttachmentTooLargeError) as exc:
        uc.upload_attachment(
            _actor(),
            investment_id=iid,
            attachment_type="other",
            display_name="Grande",
            description=None,
            original_filename="big.pdf",
            content=b"x" * (26 * 1024 * 1024),
            mime_type="application/pdf",
        )
    assert exc.value.code == "budget_capex_attachment_too_large"


def test_path_traversal_no_nome(ctx, tmp_path):
    repo, storage, uc = ctx
    eid, iid = _ready(repo)
    out = uc.upload_attachment(
        _actor(),
        investment_id=iid,
        attachment_type="other",
        display_name="Safe",
        description=None,
        original_filename="../../etc/passwd.pdf",
        content=b"%PDF",
        mime_type="application/pdf",
    )
    assert out["original_filename"] == "passwd.pdf"
    att = next(iter(repo.attachments.values()))
    assert "/" not in att["storage_key"]
    assert ".." not in att["storage_key"]
    path = storage.resolve_file(exercise_id=eid, storage_key=att["storage_key"])
    assert path.is_file()
    assert str(path).startswith(str(tmp_path.resolve()))


def test_storage_path_traversal_bloqueado(ctx):
    _repo, storage, _uc = ctx
    with pytest.raises(Exception):
        storage.resolve_file(exercise_id="ex1", storage_key="../secret")


def test_tipo_anexo_invalido(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    with pytest.raises(CapexAttachmentTypeInvalidError):
        uc.upload_attachment(
            _actor(),
            investment_id=iid,
            attachment_type="invoice",
            display_name="X",
            description=None,
            original_filename="a.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
        )


def test_listagem_sem_storage_key_e_sem_arquivados(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    a1 = uc.upload_attachment(
        _actor(),
        investment_id=iid,
        attachment_type="image",
        display_name="Foto",
        description=None,
        original_filename="foto.png",
        content=b"\x89PNG\r\n",
        mime_type="image/png",
    )
    a2 = uc.upload_attachment(
        _actor(),
        investment_id=iid,
        attachment_type="other",
        display_name="Doc",
        description=None,
        original_filename="doc.pdf",
        content=b"%PDF",
        mime_type="application/pdf",
    )
    uc.archive_attachment(_actor(), a2["id"])
    listed = uc.list_attachments(_actor(), iid)
    ids = {i["id"] for i in listed["items"]}
    assert a1["id"] in ids
    assert a2["id"] not in ids
    assert all("storage_key" not in i for i in listed["items"])


def test_download_autorizado(ctx):
    repo, storage, uc = ctx
    eid, iid = _ready(repo)
    created = uc.upload_attachment(
        _actor(),
        investment_id=iid,
        attachment_type="technical_specification",
        display_name="Spec",
        description=None,
        original_filename="spec.pdf",
        content=b"%PDF-spec",
        mime_type="application/pdf",
    )
    result = uc.resolve_download(_actor(), created["id"])
    assert Path(result["path"]).read_bytes() == b"%PDF-spec"
    assert result["mime_type"] == "application/pdf"
    assert result["filename"] == "spec.pdf"
    assert "storage_key" not in result["attachment"]
    assert any(a["action"] == "attachment.downloaded" for a in repo.audits)
    # resolve usa o mesmo volume
    assert str(result["path"]).startswith(str(storage.base_dir.resolve()))
    assert eid in str(result["path"])


def test_download_sem_escopo_idor(ctx):
    repo, _storage, uc = ctx
    eid, iid = _ready(repo, user="u1", cc="205")
    created = uc.upload_attachment(
        _actor("u1"),
        investment_id=iid,
        attachment_type="other",
        display_name="X",
        description=None,
        original_filename="a.pdf",
        content=b"%PDF",
        mime_type="application/pdf",
    )
    repo.seed_responsibility(user_sub="u2", exercise_id=eid, cost_center_id="210")
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("u2", gid))
    with pytest.raises(CapexAttachmentNotFoundError) as exc:
        uc.resolve_download(_actor("u2"), created["id"])
    assert exc.value.code == "budget_capex_attachment_not_found"


def test_arquivamento_e_download_arquivado(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    created = uc.upload_attachment(
        _actor(),
        investment_id=iid,
        attachment_type="justification",
        display_name="Just",
        description=None,
        original_filename="j.pdf",
        content=b"%PDF",
        mime_type="application/pdf",
    )
    archived = uc.archive_attachment(_actor(), created["id"])
    assert archived["is_active"] is False
    assert any(a["action"] == "attachment.archived" for a in repo.audits)
    with pytest.raises(CapexAttachmentArchivedError) as exc:
        uc.resolve_download(_actor(), created["id"])
    assert exc.value.code == "budget_capex_attachment_archived"


def test_idempotencia_retry(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    kwargs = dict(
        investment_id=iid,
        attachment_type="commercial_proposal",
        display_name="Prop",
        description=None,
        original_filename="p.pdf",
        content=b"%PDF-1",
        mime_type="application/pdf",
        idempotency_key="upload-1",
    )
    first = uc.upload_attachment(_actor(), **kwargs)
    second = uc.upload_attachment(_actor(), **kwargs)
    assert first["id"] == second["id"]
    assert len(repo.attachments) == 1


def test_sem_confirmacao_orientacoes(ctx):
    repo, _storage, uc = ctx
    eid = repo.seed_exercise()
    repo.seed_guidance(eid)
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    iid = repo.seed_investment(exercise_id=eid)
    with pytest.raises(BudgetGuidanceAcknowledgementRequiredError):
        uc.upload_attachment(
            _actor(),
            investment_id=iid,
            attachment_type="other",
            display_name="X",
            description=None,
            original_filename="a.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
        )


def test_sem_responsabilidade(ctx):
    repo, _storage, uc = ctx
    eid = repo.seed_exercise()
    gid = repo.seed_guidance(eid)
    repo.acks.add(("u1", gid))
    iid = repo.seed_investment(exercise_id=eid, cost_center_id="205")
    with pytest.raises(CapexInvestmentNotFoundError):
        uc.list_attachments(_actor(), iid)


def test_sem_permissao_acesso(ctx):
    repo, _storage, uc = ctx
    _eid, iid = _ready(repo)
    actor = BudgetActor(user_id="u1", user_name="U", permissions=frozenset())
    with pytest.raises(CapexAttachmentForbiddenError) as exc:
        uc.list_attachments(actor, iid)
    assert exc.value.code == "budget_capex_attachment_forbidden"


def test_admin_acessa_outro_cc(ctx):
    repo, _storage, uc = ctx
    eid, iid = _ready(repo, user="u1", cc="205")
    created = uc.upload_attachment(
        _actor("u1"),
        investment_id=iid,
        attachment_type="other",
        display_name="X",
        description=None,
        original_filename="a.pdf",
        content=b"%PDF",
        mime_type="application/pdf",
    )
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("admin", gid))
    listed = uc.list_attachments(_actor("admin", admin=True), iid)
    assert listed["items"][0]["id"] == created["id"]
