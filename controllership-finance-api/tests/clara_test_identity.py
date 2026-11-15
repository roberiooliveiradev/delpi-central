"""Identidade de teste no formato de ``tool_bridge._identity_flags``.

Um único construtor. Os perfis abaixo só escolhem as flags; não
duplicam o dicionário.
"""

from __future__ import annotations


def clara_test_identity(
    subject: str,
    name: str,
    *,
    has_cf_access: bool = False,
    has_lnf_any: bool = False,
    is_manage: bool = False,
    is_dre: bool = False,
    lnf_read: bool = False,
    lnf_create: bool = False,
    lnf_write: bool = False,
    lnf_process: bool = False,
    lnf_manage: bool = False,
    lnf_review_unmapped: bool = False,
) -> dict:
    domains: list[str] = []
    if has_cf_access:
        domains.append("controllership")
    if has_lnf_any:
        domains.append("lancamento-notas-fiscais")
    return {
        "subject": subject,
        "name": name,
        "has_cf_access": has_cf_access,
        "has_lnf_any": has_lnf_any,
        "is_manage": is_manage,
        "is_dre": is_dre,
        "lnf_read": lnf_read,
        "lnf_create": lnf_create,
        "lnf_write": lnf_write,
        "lnf_process": lnf_process,
        "lnf_manage": lnf_manage,
        "lnf_review_unmapped": lnf_review_unmapped,
        "knowledge_domains": domains,
    }


def cf_closing_writer(subject: str, name: str = "cf-admin-test") -> dict:
    """Usuário da controladoria que escreve no fechamento."""
    return clara_test_identity(
        subject, name, has_cf_access=True, is_manage=True, is_dre=True,
    )


def cf_closing_member(subject: str, name: str = "reviewer") -> dict:
    """Usuário da controladoria sem manage e sem DRE."""
    return clara_test_identity(subject, name, has_cf_access=True)


def lnf_only_writer(subject: str, name: str = "lnf-only") -> dict:
    """Entrada só no Lançamento de Notas Fiscais. Não escreve no fechamento."""
    return clara_test_identity(
        subject,
        name,
        has_lnf_any=True,
        lnf_read=True,
        lnf_create=True,
        lnf_write=True,
        lnf_process=True,
    )
