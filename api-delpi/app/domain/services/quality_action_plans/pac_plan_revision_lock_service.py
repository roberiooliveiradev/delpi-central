from __future__ import annotations

REVISION_CONFLICT_MESSAGE = (
    "Conflito de revisão: o plano foi alterado por outro usuário. Recarregue e tente novamente."
)


def assert_expected_revision_number(
    current_revision_number: int | None,
    expected_revision_number: int | None,
) -> None:
    if expected_revision_number is None:
        return
    if int(current_revision_number or 0) != int(expected_revision_number):
        raise ValueError(REVISION_CONFLICT_MESSAGE)
