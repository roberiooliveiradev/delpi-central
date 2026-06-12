from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.application.services.external_action_import_job_service import (
    ExternalActionImportJobService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)


def test_import_job_phase_labels_from_content():
    assert (
        ExternalActionResponseContentService.get(
            "importJob",
            "phaseLabels",
            "fetch_schema",
        )
        == "Baixando OpenAPI"
    )
    assert (
        ExternalActionResponseContentService.get(
            "importJob",
            "phaseLabels",
            "embed_actions",
        )
        == "Indexando busca semântica"
    )


def test_to_dict_exposes_progress_and_phase_label():
    job_id = uuid4()
    provider_key = "api-delpi"
    now = datetime.now(timezone.utc)

    job = SimpleNamespace(
        id=job_id,
        provider_key=provider_key,
        status="running",
        phase="import_actions",
        progress_done=12,
        progress_total=40,
        result={"actionsImported": 40},
        error=None,
        started_at=now,
        updated_at=now,
    )

    payload = ExternalActionImportJobService.to_dict(job)

    assert payload["jobId"] == str(job_id)
    assert payload["providerKey"] == provider_key
    assert payload["phase"] == "import_actions"
    assert payload["phaseLabel"] == "Cadastrando rotas"
    assert payload["progress"] == {"done": 12, "total": 40, "unit": "actions"}
    assert payload["pollUrl"] == f"/chat/providers/{provider_key}/import/jobs/{job_id}"
