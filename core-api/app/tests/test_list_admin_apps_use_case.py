# app/tests/test_list_admin_apps_use_case.py

from unittest.mock import MagicMock

from app.application.use_cases.list_admin_apps_use_case import ListAdminAppsUseCase


def test_execute_forwards_app_type_to_repository():
    uow = MagicMock()
    uow.admin_apps.list_paginated.return_value = ([], 0)

    use_case = ListAdminAppsUseCase(uow)
    use_case.execute(
        page=1,
        page_size=10,
        q=None,
        sort="name",
        direction="asc",
        app_type="iframe",
    )

    uow.admin_apps.list_paginated.assert_called_once_with(
        page=1,
        page_size=10,
        q=None,
        sort="name",
        direction="asc",
        created_from=None,
        created_to=None,
        updated_from=None,
        updated_to=None,
        app_type="iframe",
    )
