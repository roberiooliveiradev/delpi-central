"""Adapter fail-honest — sem ``ENG_PRC_REPOSITORY`` configurado.

Nunca lista vazia falsa nem sucesso otimista: toda operação devolve
``PrcRepositoryError`` → ``unavailable`` honesto no edge.
"""

from __future__ import annotations

from typing import Any

from engineering_app.domain.product_registration.errors import (
    PrcRepositoryError,
)

_MSG = (
    "Product Registration indisponível: ENG_PRC_REPOSITORY não "
    "configurado (memory|postgres)."
)


def _unavailable(*_a: Any, **_kw: Any) -> Any:
    raise PrcRepositoryError(_MSG)


class UnavailableProductRegistrationRepository:
    find_idempotent = staticmethod(_unavailable)
    save_idempotent = staticmethod(_unavailable)
    create_request = staticmethod(_unavailable)
    get_request = staticmethod(_unavailable)
    get_request_by_external_ref = staticmethod(_unavailable)
    list_requests = staticmethod(_unavailable)
    apply_transition = staticmethod(_unavailable)
    update_draft = staticmethod(_unavailable)
    insert_verification = staticmethod(_unavailable)
    list_verifications = staticmethod(_unavailable)
    get_record = staticmethod(_unavailable)
    get_record_by_official_code = staticmethod(_unavailable)
    list_revisions = staticmethod(_unavailable)
    get_revision = staticmethod(_unavailable)
    complete_request = staticmethod(_unavailable)
    create_flag = staticmethod(_unavailable)
    get_flag = staticmethod(_unavailable)
    find_open_flag_by_target = staticmethod(_unavailable)
    list_flags = staticmethod(_unavailable)
    list_flags_cross_case = staticmethod(_unavailable)
    summarize_flags_cross_case = staticmethod(_unavailable)
    update_flag = staticmethod(_unavailable)
    transition_flag = staticmethod(_unavailable)
    soft_delete_flag = staticmethod(_unavailable)
    create_information_round = staticmethod(_unavailable)
    get_information_round = staticmethod(_unavailable)
    list_information_rounds = staticmethod(_unavailable)
    save_information_answers_draft = staticmethod(_unavailable)
    submit_information_answers = staticmethod(_unavailable)
    accept_information_question = staticmethod(_unavailable)
    create_information_follow_up = staticmethod(_unavailable)
    resolve_open_information_rounds = staticmethod(_unavailable)
    get_correction_return = staticmethod(_unavailable)
    get_open_correction_return = staticmethod(_unavailable)
    list_correction_returns = staticmethod(_unavailable)
    create_correction_return = staticmethod(_unavailable)
    update_returned_fields = staticmethod(_unavailable)
    resubmit_correction = staticmethod(_unavailable)
