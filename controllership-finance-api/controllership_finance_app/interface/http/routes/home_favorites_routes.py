"""Favoritos do hub Início — GET/PUT /me/home-favorites (padrão Comercial)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.infrastructure.persistence.home_favorites_repository import (
    MAX_HOME_FAVORITES,
    HomeFavoritesRepository,
    normalize_favorite_items,
)
from controllership_finance_app.interface.http.authz import (
    actor_sub_for_favorites,
    authorized_home_hub_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/me", tags=["Me / home favorites"])


class FavoriteItemBody(BaseModel):
    viewId: str = Field(min_length=1)
    search: str | None = None


class PutHomeFavoritesBody(BaseModel):
    items: list[FavoriteItemBody] = Field(
        default_factory=list, max_length=MAX_HOME_FAVORITES
    )


def _repo() -> HomeFavoritesRepository:
    return HomeFavoritesRepository()


@router.get("/home-favorites", operation_id="get_home_favorites")
def get_home_favorites(request: Request):
    user = authorized_home_hub_user(request)
    user_id = actor_sub_for_favorites(user)
    if not user_id:
        return fail("Não autenticado.", 401, operation_id="get_home_favorites")
    try:
        items = _repo().get_items(user_id=user_id)
        return ok(
            {"items": items},
            message="Favoritos carregados.",
            operation_id="get_home_favorites",
        )
    except RuntimeError:
        return fail(
            "Persistência indisponível.",
            503,
            operation_id="get_home_favorites",
        )
    except Exception:
        logger.exception("get_home_favorites_failed")
        return fail(
            "Erro ao carregar favoritos.",
            500,
            operation_id="get_home_favorites",
        )


@router.put("/home-favorites", operation_id="put_home_favorites")
def put_home_favorites(request: Request, body: PutHomeFavoritesBody):
    user = authorized_home_hub_user(request)
    user_id = actor_sub_for_favorites(user)
    if not user_id:
        return fail("Não autenticado.", 401, operation_id="put_home_favorites")
    try:
        payload = [item.model_dump(exclude_none=True) for item in body.items]
        normalize_favorite_items(payload)
        items = _repo().put_items(user_id=user_id, items=payload)
        return ok(
            {"items": items},
            message="Favoritos salvos.",
            operation_id="put_home_favorites",
        )
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="put_home_favorites")
    except RuntimeError:
        return fail(
            "Persistência indisponível.",
            503,
            operation_id="put_home_favorites",
        )
    except Exception:
        logger.exception("put_home_favorites_failed")
        return fail(
            "Erro ao salvar favoritos.",
            500,
            operation_id="put_home_favorites",
        )
