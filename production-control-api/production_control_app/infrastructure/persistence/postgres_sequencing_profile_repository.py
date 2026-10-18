"""Repositório Postgres — perfis de sequenciamento e vínculos por filial/CT.

Catálogo administrativo do PCP (V018). Cada mutação grava a linha principal e
o evento de auditoria na MESMA transação (`with get_connection()` commita no
sucesso e faz rollback na exceção) — nunca há write parcial nem evento órfão.
"""

from __future__ import annotations

import json
from typing import Any

import psycopg

from uuid import UUID

from production_control_app.domain.errors import (
    SequencingProfileConflict,
    SequencingProfileNotFound,
)
from production_control_app.domain.ports.sequencing_profile_repository import (
    SequencingProfileRepositoryPort,
)
from production_control_app.domain.sequencing_profile import (
    SequencingProfile,
    SequencingProfileBinding,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_PROFILES = f"{PC_SCHEMA_NAME}.sequencing_profiles"
_REVISIONS = f"{PC_SCHEMA_NAME}.sequencing_profile_revisions"
_BINDINGS = f"{PC_SCHEMA_NAME}.sequencing_profile_bindings"
_BINDING_EVENTS = f"{PC_SCHEMA_NAME}.sequencing_profile_binding_events"

_PROFILE_COLUMNS = """
    id, name, description, status, revision, criteria, origin_branch,
    created_at, created_by, updated_at, updated_by
"""


def _profile_from_row(row: dict) -> SequencingProfile:
    criteria = row.get("criteria")
    if isinstance(criteria, str):
        criteria = json.loads(criteria)
    return SequencingProfile(
        id=row["id"],
        name=str(row.get("name") or ""),
        description=row.get("description"),
        status=str(row.get("status") or ""),
        revision=int(row.get("revision") or 0),
        criteria=list(criteria or []),
        origin_branch=row.get("origin_branch"),
        created_at=row.get("created_at"),
        created_by=row.get("created_by"),
        updated_at=row.get("updated_at"),
        updated_by=row.get("updated_by"),
    )


def _binding_from_row(row: dict) -> SequencingProfileBinding:
    return SequencingProfileBinding(
        branch=str(row.get("branch") or ""),
        work_center=str(row.get("work_center") or ""),
        profile_id=row["profile_id"],
        assigned_by=row.get("assigned_by"),
        assigned_at=row.get("assigned_at"),
    )


def _profile_snapshot(profile: SequencingProfile) -> dict[str, Any]:
    return {
        "name": profile.name,
        "description": profile.description,
        "status": profile.status,
        "revision": profile.revision,
        "criteria": profile.criteria,
    }


class PostgresSequencingProfileRepository(SequencingProfileRepositoryPort):
    def list_profiles(self) -> list[SequencingProfile]:
        query = f"""
            SELECT {_PROFILE_COLUMNS}
            FROM {_PROFILES}
            ORDER BY name ASC, created_at ASC
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return [_profile_from_row(row) for row in cursor.fetchall()]

    def get_profile(self, *, profile_id: UUID) -> SequencingProfile | None:
        query = f"""
            SELECT {_PROFILE_COLUMNS}
            FROM {_PROFILES}
            WHERE id = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (profile_id,))
                row = cursor.fetchone()
        return _profile_from_row(row) if row else None

    def list_bound_branches(self, *, profile_id: UUID) -> list[str]:
        query = f"""
            SELECT DISTINCT branch
            FROM {_BINDINGS}
            WHERE profile_id = %s
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (profile_id,))
                return [str(row["branch"]) for row in cursor.fetchall()]

    def create_profile(
        self,
        *,
        name: str,
        description: str | None,
        status: str,
        criteria: list[dict],
        origin_branch: str,
        actor: str | None,
    ) -> SequencingProfile:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {_PROFILES}
                        (name, description, status, criteria, origin_branch,
                         created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING {_PROFILE_COLUMNS}
                    """,
                    (
                        name, description, status, json.dumps(criteria),
                        origin_branch, actor, actor,
                    ),
                )
                profile = _profile_from_row(cursor.fetchone())
                cursor.execute(
                    f"""
                    INSERT INTO {_REVISIONS}
                        (profile_id, revision, action, snapshot, actor)
                    VALUES (%s, %s, 'created', %s, %s)
                    """,
                    (
                        profile.id,
                        profile.revision,
                        json.dumps(_profile_snapshot(profile)),
                        actor,
                    ),
                )
        return profile

    def update_profile(
        self,
        *,
        profile_id: UUID,
        expected_revision: int,
        managed_branches: frozenset[str],
        name: str,
        description: str | None,
        status: str,
        criteria: list[dict],
        actor: str | None,
    ) -> SequencingProfile | None:
        """Concorrência otimista + escopo de filial na mesma transação.

        A linha do perfil é travada (FOR UPDATE) antes da verificação:
        `set_binding` trava a mesma linha, então um vínculo concorrente ou
        comita antes (e é visto aqui, podendo negar a edição) ou espera o
        commit desta transação — nunca há edição autorizada por um vínculo
        fantasma. Retorna None quando o perfil não existe ou a revisão
        divergiu; PermissionError quando o chamador não administra TODAS as
        filiais afetadas (origem ∪ vínculos).
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT revision, origin_branch
                    FROM {_PROFILES}
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (profile_id,),
                )
                locked = cursor.fetchone()
                if locked is not None:
                    cursor.execute(
                        f"""
                        SELECT DISTINCT branch
                        FROM {_BINDINGS}
                        WHERE profile_id = %s
                        """,
                        (profile_id,),
                    )
                    affected = {str(r["branch"]) for r in cursor.fetchall()}
                    if locked.get("origin_branch"):
                        affected.add(str(locked["origin_branch"]))
                    # Política estrita: TODAS as filiais afetadas precisam
                    # estar no escopo administrado pelo chamador. Conjunto
                    # vazio (perfil legado sem origem e sem vínculo) nega —
                    # não inventa proprietário.
                    if not affected or not affected <= set(managed_branches):
                        raise PermissionError(
                            "Edição exige administração em todas as filiais "
                            "afetadas pelo perfil (origem e vínculos)."
                        )
                cursor.execute(
                    f"""
                    UPDATE {_PROFILES}
                    SET name = %s,
                        description = %s,
                        status = %s,
                        criteria = %s,
                        revision = revision + 1,
                        updated_at = NOW(),
                        updated_by = %s
                    WHERE id = %s AND revision = %s
                    RETURNING {_PROFILE_COLUMNS}
                    """,
                    (
                        name,
                        description,
                        status,
                        json.dumps(criteria),
                        actor,
                        profile_id,
                        expected_revision,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                profile = _profile_from_row(row)
                cursor.execute(
                    f"""
                    INSERT INTO {_REVISIONS}
                        (profile_id, revision, action, snapshot, actor)
                    VALUES (%s, %s, 'updated', %s, %s)
                    """,
                    (
                        profile.id,
                        profile.revision,
                        json.dumps(_profile_snapshot(profile)),
                        actor,
                    ),
                )
        return profile

    def get_binding(
        self, *, branch: str, work_center: str
    ) -> SequencingProfileBinding | None:
        query = f"""
            SELECT branch, work_center, profile_id, assigned_by, assigned_at
            FROM {_BINDINGS}
            WHERE branch = %s AND work_center = %s
            LIMIT 1
        """
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (branch, work_center))
                row = cursor.fetchone()
        return _binding_from_row(row) if row else None

    def list_bindings(
        self, *, branch: str, work_center: str | None = None
    ) -> list[SequencingProfileBinding]:
        query = f"""
            SELECT branch, work_center, profile_id, assigned_by, assigned_at
            FROM {_BINDINGS}
            WHERE branch = %s
        """
        params: list[Any] = [branch]
        if work_center is not None:
            query += " AND work_center = %s"
            params.append(work_center)
        query += " ORDER BY work_center ASC"
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, tuple(params))
                return [_binding_from_row(row) for row in cursor.fetchall()]

    def set_binding(
        self,
        *,
        branch: str,
        work_center: str,
        profile_id: UUID | None,
        managed_branches: frozenset[str],
        actor: str | None,
    ) -> SequencingProfileBinding | None:
        # SELECT FOR UPDATE não trava uma linha que ainda não existe: duas
        # transações simultâneas no mesmo (branch, work_center) podem correr
        # para o INSERT e a perdedora recebe UniqueViolation. Em vez de um
        # 500, reexecuta uma vez — a segunda tentativa já enxerga a linha
        # comitada e segue pelo caminho de UPDATE serializado pela trava.
        for attempt in range(2):
            try:
                return self._set_binding_once(
                    branch=branch,
                    work_center=work_center,
                    profile_id=profile_id,
                    managed_branches=managed_branches,
                    actor=actor,
                )
            except psycopg.errors.UniqueViolation:
                if attempt == 1:
                    raise SequencingProfileConflict(
                        "Concorrência no vínculo do centro de trabalho. "
                        "Tente novamente."
                    )
        return None  # unreachable

    def _set_binding_once(
        self,
        *,
        branch: str,
        work_center: str,
        profile_id: UUID | None,
        managed_branches: frozenset[str],
        actor: str | None,
    ) -> SequencingProfileBinding | None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                # Serializa contra update_profile: vincular este perfil muda
                # o conjunto de filiais afetadas que a edição verifica sob
                # a mesma trava.
                if profile_id is not None:
                    cursor.execute(
                        f"""
                        SELECT origin_branch FROM {_PROFILES}
                        WHERE id = %s
                        FOR UPDATE
                        """,
                        (profile_id,),
                    )
                    locked_profile = cursor.fetchone()
                    if locked_profile is None:
                        raise SequencingProfileNotFound(
                            "Perfil de sequenciamento não encontrado."
                        )
                    cursor.execute(
                        f"""
                        SELECT DISTINCT branch
                        FROM {_BINDINGS}
                        WHERE profile_id = %s
                        """,
                        (profile_id,),
                    )
                    bound = {str(r["branch"]) for r in cursor.fetchall()}
                    origin = locked_profile.get("origin_branch")
                    if origin is None and branch not in bound:
                        raise PermissionError(
                            "Perfil sem filial de origem não pode ser "
                            "reivindicado por um novo vínculo."
                        )
                    # Expandir o perfil a uma filial nova exige gerenciar
                    # TODAS as afetadas (origem ∪ vínculos ∪ nova) — senão
                    # um admin de outra filial travaria a edição do dono.
                    required = set(bound) | {branch}
                    if origin:
                        required.add(str(origin))
                    if not required <= set(managed_branches):
                        raise PermissionError(
                            "Vincular este perfil a uma nova filial exige "
                            "administração em todas as filiais afetadas."
                        )
                cursor.execute(
                    f"""
                    SELECT branch, work_center, profile_id, assigned_by, assigned_at
                    FROM {_BINDINGS}
                    WHERE branch = %s AND work_center = %s
                    FOR UPDATE
                    """,
                    (branch, work_center),
                )
                existing = cursor.fetchone()
                previous_profile_id = existing["profile_id"] if existing else None

                if profile_id is None:
                    if previous_profile_id is None:
                        return None
                    cursor.execute(
                        f"""
                        DELETE FROM {_BINDINGS}
                        WHERE branch = %s AND work_center = %s
                        """,
                        (branch, work_center),
                    )
                    action = "unbound"
                elif previous_profile_id is None:
                    cursor.execute(
                        f"""
                        INSERT INTO {_BINDINGS}
                            (branch, work_center, profile_id, assigned_by)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (branch, work_center, profile_id, actor),
                    )
                    action = "bound"
                elif previous_profile_id == profile_id:
                    # Reenvio idempotente do mesmo vínculo — sem novo evento;
                    # devolve a linha persistida (ator/timestamp originais).
                    return _binding_from_row(existing)
                else:
                    cursor.execute(
                        f"""
                        UPDATE {_BINDINGS}
                        SET profile_id = %s, assigned_by = %s, assigned_at = NOW()
                        WHERE branch = %s AND work_center = %s
                        """,
                        (profile_id, actor, branch, work_center),
                    )
                    action = "rebound"

                cursor.execute(
                    f"""
                    INSERT INTO {_BINDING_EVENTS}
                        (branch, work_center, profile_id, previous_profile_id,
                         action, actor)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (branch, work_center, profile_id, previous_profile_id, action, actor),
                )

        if profile_id is None:
            return None
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT branch, work_center, profile_id, assigned_by, assigned_at
                    FROM {_BINDINGS}
                    WHERE branch = %s AND work_center = %s
                    """,
                    (branch, work_center),
                )
                row = cursor.fetchone()
        return _binding_from_row(row) if row else None
