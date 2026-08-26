from unittest.mock import patch

from app.infrastructure.persistence.totvs.protheus_users.protheus_users_repository import (
    ProtheusUsersRepository,
)


def test_find_by_email_opens_totvs_connection() -> None:
    repo = ProtheusUsersRepository()
    with patch.object(ProtheusUsersRepository, "__enter__", return_value=repo) as enter:
        with patch.object(ProtheusUsersRepository, "__exit__", return_value=None):
            with patch.object(repo, "execute_query", return_value=[]) as execute_query:
                result = repo.find_by_email("compras@delpi.com.br")

    enter.assert_called_once()
    execute_query.assert_called_once()
    assert result == []
