from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.product_3d_model_service import (
    Product3DModelService,
)
from production_control_app.domain.errors import Product3DModelInvalid, Product3DModelNotFound
from production_control_app.domain.product_3d_model import Product3DModel
from production_control_app.interface.http.routes.product_3d_model_routes import router

_GLB = b"glTF" + b"\x02\x00\x00\x00" + b"x" * 20
_PDF = b"%PDF-1.4 not a model"


def _manager():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["production-control.product-3d-models.manage"],
        email="pcp.user@delpi.local",
    )


def _viewer():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["production-control.access"],
        email="viewer@delpi.local",
    )


class FakeRepo:
    def __init__(self) -> None:
        self.rows: dict[str, Product3DModel] = {}

    def get(self, *, product_code: str) -> Product3DModel | None:
        return self.rows.get(product_code)

    def list(self, *, search: str | None = None) -> list[Product3DModel]:
        items = list(self.rows.values())
        wanted = str(search or "").strip().upper()
        if wanted:
            items = [item for item in items if wanted in item.product_code]
        return items

    def existing_codes(self, codes: set[str]) -> set[str]:
        wanted = {code.upper() for code in codes}
        return {code for code in self.rows if code in wanted}

    def upsert(self, model: Product3DModel) -> Product3DModel:
        saved = Product3DModel(
            product_code=model.product_code,
            original_filename=model.original_filename,
            stored_filename=model.stored_filename,
            content_type=model.content_type,
            byte_size=model.byte_size,
            uploaded_by=model.uploaded_by,
            uploaded_at=model.uploaded_at or datetime.now(timezone.utc),
        )
        self.rows[model.product_code] = saved
        return saved

    def delete(self, *, product_code: str) -> Product3DModel | None:
        return self.rows.pop(product_code, None)


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def write_glb(self, *, product_code: str, payload: bytes) -> str:
        name = f"{product_code}.glb"
        self.files[name] = payload
        return name

    def resolve_glb(self, *, stored_filename: str) -> str:
        if stored_filename not in self.files:
            raise Product3DModelNotFound("missing")
        return f"/tmp/{stored_filename}"

    def delete_glb(self, *, stored_filename: str) -> None:
        self.files.pop(stored_filename, None)
        self.deleted.append(stored_filename)


def _service(max_bytes: int = 1024) -> tuple[Product3DModelService, FakeRepo, FakeStorage]:
    repo = FakeRepo()
    storage = FakeStorage()
    return Product3DModelService(models=repo, storage=storage, max_bytes=max_bytes), repo, storage


def test_upsert_pi_and_pa_share_same_rule() -> None:
    service, repo, storage = _service()

    pi = service.upsert(_manager(), product_code="50320064", original_filename="pi.glb", payload=_GLB)
    pa = service.upsert(_manager(), product_code="90262957", original_filename="pa.glb", payload=_GLB)

    assert pi["product_code"] == "50320064"
    assert pa["product_code"] == "90262957"
    assert set(repo.rows) == {"50320064", "90262957"}
    assert set(storage.files) == {"50320064.glb", "90262957.glb"}


def test_upsert_replaces_same_product_code() -> None:
    service, repo, storage = _service()
    service.upsert(_manager(), product_code="50320064", original_filename="old.glb", payload=_GLB)
    newer = _GLB + b"next"

    saved = service.upsert(_manager(), product_code="50320064", original_filename="new.glb", payload=newer)

    assert saved["original_filename"] == "new.glb"
    assert saved["byte_size"] == len(newer)
    assert list(repo.rows) == ["50320064"]
    assert storage.files["50320064.glb"] == newer


def test_upsert_rejects_viewer_without_permission() -> None:
    service, _, _ = _service()

    with pytest.raises(PermissionError):
        service.upsert(_viewer(), product_code="50320064", original_filename="pi.glb", payload=_GLB)


def test_upsert_rejects_non_glb_extension_and_magic() -> None:
    service, repo, _ = _service()

    with pytest.raises(Product3DModelInvalid, match="extensão"):
        service.upsert(_manager(), product_code="50320064", original_filename="peca.pdf", payload=_GLB)
    with pytest.raises(Product3DModelInvalid, match="formato"):
        service.upsert(_manager(), product_code="50320064", original_filename="peca.glb", payload=_PDF)

    assert repo.rows == {}


def test_upsert_rejects_payload_over_limit() -> None:
    service, _, _ = _service(max_bytes=8)

    with pytest.raises(Product3DModelInvalid, match="tamanho máximo"):
        service.upsert(_manager(), product_code="50320064", original_filename="pi.glb", payload=_GLB)


def test_delete_removes_metadata_and_file() -> None:
    service, repo, storage = _service()
    service.upsert(_manager(), product_code="50320064", original_filename="pi.glb", payload=_GLB)

    service.delete(_manager(), product_code="50320064")

    assert repo.rows == {}
    assert storage.deleted == ["50320064.glb"]


def _client(service: Product3DModelService, user) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = user
        return await call_next(request)

    app.include_router(router)

    import production_control_app.interface.http.routes.product_3d_model_routes as routes

    routes.build_product_3d_model_service = lambda: service  # type: ignore[method-assign]
    return TestClient(app)


def test_http_put_get_delete_roundtrip() -> None:
    service, _, _ = _service()
    client = _client(service, _manager())

    created = client.put(
        "/product-3d-models/50320064",
        files={"file": ("peca.glb", _GLB, "model/gltf-binary")},
    )
    assert created.status_code == 200
    assert created.json()["data"]["product_code"] == "50320064"

    listed = client.get("/product-3d-models")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    deleted = client.delete("/product-3d-models/50320064")
    assert deleted.status_code == 200
    assert client.get("/product-3d-models/50320064").status_code == 404


def test_http_put_forbidden_without_permission() -> None:
    service, _, _ = _service()
    client = _client(service, _viewer())

    response = client.put(
        "/product-3d-models/50320064",
        files={"file": ("peca.glb", _GLB, "model/gltf-binary")},
    )
    assert response.status_code == 403
