from __future__ import annotations

from typing import Callable, Mapping
from uuid import uuid4

from requests_app.domain.entities import RequestType
from requests_app.domain.exceptions import RequestTypeNotFoundError
from requests_app.domain.services.content_loader import load_workflow_definition


class RequestTypeRegistry:
    """In-memory / injected catalog of request types (no type-specific imports)."""

    def __init__(
        self,
        types: Mapping[str, RequestType] | None = None,
        *,
        loader: Callable[[str], RequestType | None] | None = None,
    ) -> None:
        self._types = {code: value for code, value in (types or {}).items()}
        self._loader = loader

    def register(self, request_type: RequestType) -> None:
        self._types[request_type.code] = request_type

    def get(self, code: str) -> RequestType:
        key = (code or "").strip()
        if key in self._types:
            return self._types[key]
        if self._loader is not None:
            loaded = self._loader(key)
            if loaded is not None:
                self._types[key] = loaded
                return loaded
        raise RequestTypeNotFoundError(key)

    def list_active(self) -> list[RequestType]:
        return [item for item in self._types.values() if item.active]

    @staticmethod
    def from_workflow_content(
        *,
        code: str,
        name: str,
        workflow_name: str,
        permission_prefix: str,
        presentation_mode: str = "specialized",
        branch_scope: str = "optional",
        active: bool = True,
        form_schema: dict | None = None,
        ui_schema: dict | None = None,
    ) -> RequestType:
        return RequestType(
            id=uuid4(),
            code=code,
            name=name,
            permission_prefix=permission_prefix,
            workflow_definition=load_workflow_definition(workflow_name),
            presentation_mode=presentation_mode,
            branch_scope=branch_scope,
            active=active,
            form_schema=form_schema or {},
            ui_schema=ui_schema or {},
        )
