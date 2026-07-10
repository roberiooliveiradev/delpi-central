from __future__ import annotations

from typing import Any

from app.application.dto.audit_5s.get_audit_5s_dashboard_request import (
    GetAudit5sDashboardRequest,
)
from app.application.services.audit_5s.scoring_service import (
    CriterionScoreInput,
    calculate_overall_percentual,
    calculate_senso_percentual,
    can_attach_criterion_photo,
    is_evaluation_complete,
    is_nc_candidate,
)
from app.application.services.audit_5s.catalog_service import (
    DEFAULT_CATALOG_VERSION,
    fallback_catalog_version,
)
from app.application.services.audit_5s.nc_attachment_storage import (
    Audit5sNcAttachmentStorage,
)
from app.application.services.audit_5s.response_attachment_storage import (
    Audit5sResponseAttachmentStorage,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.shared_quality.postgres_sequential_code_generator import (
    PostgresSequentialCodeGenerator,
)
from app.shared.utils.person_name import format_person_name


class PostgresAudit5sRepository(PluginBaseRepository):
    CATALOG_VERSION = DEFAULT_CATALOG_VERSION

    def resolve_catalog_version(self, branch_code: str) -> int:
        row = self.fetch_one(
            """
            SELECT catalog_version
              FROM quality.audit_5s_branch_catalog
             WHERE branch_code = %s
               AND active = TRUE
            """,
            (branch_code,),
        )
        if row:
            return int(row["catalog_version"])
        return fallback_catalog_version(branch_code)

    def list_areas(self, branch_code: str, *, active_only: bool = True) -> list[dict[str, Any]]:
        query = """
            SELECT id, branch_code, name, active, created_at
              FROM quality.audit_5s_areas
             WHERE branch_code = %s
        """
        params: list[Any] = [branch_code]
        if active_only:
            query += " AND active = TRUE"
        query += " ORDER BY lower(name)"
        return self.fetch_all(query, tuple(params))

    def create_area(
        self,
        *,
        branch_code: str,
        name: str,
        created_by_user_id: str | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.audit_5s_areas (
                branch_code, name, created_by_user_id
            ) VALUES (%s, %s, %s)
            RETURNING id, branch_code, name, active, created_at
            """,
            (branch_code, name.strip(), created_by_user_id),
        )
        if not row:
            raise PluginsRepositoryError("Falha ao cadastrar área auditada.")
        return row

    def list_criteria_catalog(self, catalog_version: int | None = None) -> list[dict[str, Any]]:
        version = catalog_version or self.CATALOG_VERSION
        return self.fetch_all(
            """
            SELECT c.id,
                   c.code,
                   c.description,
                   c.sort_order,
                   c.catalog_version,
                   s.id AS senso_id,
                   s.sort_order AS senso_order,
                   COALESCE(sn.name, s.name) AS senso_name
              FROM quality.audit_5s_criteria c
              JOIN quality.audit_5s_sensos s ON s.id = c.senso_id
              LEFT JOIN quality.audit_5s_catalog_senso_names sn
                ON sn.catalog_version = c.catalog_version
               AND sn.senso_sort_order = s.sort_order
             WHERE c.catalog_version = %s
               AND c.active = TRUE
               AND s.active = TRUE
             ORDER BY s.sort_order, c.sort_order
            """,
            (version,),
        )

    def get_max_catalog_version(self) -> int:
        row = self.fetch_one(
            """
            SELECT COALESCE(MAX(catalog_version), 0) AS max_version
              FROM quality.audit_5s_criteria
            """
        )
        return int(row["max_version"]) if row else 0

    def list_catalog_senso_names(self, catalog_version: int) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT catalog_version, senso_sort_order, name
              FROM quality.audit_5s_catalog_senso_names
             WHERE catalog_version = %s
             ORDER BY senso_sort_order
            """,
            (catalog_version,),
        )

    def get_latest_catalog_publication(self, branch_code: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT id,
                   branch_code,
                   catalog_version,
                   published_by_user_id,
                   published_at,
                   criteria_count,
                   notes
              FROM quality.audit_5s_catalog_publications
             WHERE branch_code = %s
             ORDER BY published_at DESC
             LIMIT 1
            """,
            (branch_code,),
        )

    def list_catalog_publications(self, branch_code: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id,
                   branch_code,
                   catalog_version,
                   published_by_user_id,
                   published_at,
                   criteria_count,
                   notes
              FROM quality.audit_5s_catalog_publications
             WHERE branch_code = %s
             ORDER BY published_at DESC
            """,
            (branch_code,),
        )

    def get_active_catalog(self, branch_code: str) -> dict[str, Any]:
        catalog_version = self.resolve_catalog_version(branch_code)
        criteria = self.list_criteria_catalog(catalog_version)
        senso_names = self.list_catalog_senso_names(catalog_version)
        latest_publication = self.get_latest_catalog_publication(branch_code)
        return {
            "branch_code": branch_code,
            "catalog_version": catalog_version,
            "criteria_count": len(criteria),
            "criteria": criteria,
            "senso_names": senso_names,
            "last_published_at": (
                latest_publication["published_at"] if latest_publication else None
            ),
            "last_published_by_user_id": (
                latest_publication["published_by_user_id"] if latest_publication else None
            ),
        }

    def publish_catalog(
        self,
        *,
        branch_code: str,
        criteria: list[dict[str, Any]],
        senso_names: list[dict[str, Any]] | None,
        published_by_user_id: str | None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        next_version = self.get_max_catalog_version() + 1
        senso_rows = self.fetch_all(
            """
            SELECT id, sort_order
              FROM quality.audit_5s_sensos
             WHERE active = TRUE
            """
        )
        senso_id_by_order = {int(row["sort_order"]): row["id"] for row in senso_rows}

        try:
            for item in criteria:
                senso_order = int(item["senso_order"])
                senso_id = senso_id_by_order.get(senso_order)
                if senso_id is None:
                    raise PluginsRepositoryError(
                        f"Senso {senso_order} não encontrado no catálogo base."
                    )
                self.execute(
                    """
                    INSERT INTO quality.audit_5s_criteria (
                        senso_id, code, description, sort_order, catalog_version
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        senso_id,
                        item["code"],
                        item["description"],
                        int(item["sort_order"]),
                        next_version,
                    ),
                    auto_commit=False,
                )

            if senso_names:
                for item in senso_names:
                    self.execute(
                        """
                        INSERT INTO quality.audit_5s_catalog_senso_names (
                            catalog_version, senso_sort_order, name
                        ) VALUES (%s, %s, %s)
                        ON CONFLICT (catalog_version, senso_sort_order) DO UPDATE
                            SET name = EXCLUDED.name
                        """,
                        (
                            next_version,
                            int(item["senso_sort_order"]),
                            item["name"],
                        ),
                        auto_commit=False,
                    )

            self.execute(
                """
                INSERT INTO quality.audit_5s_branch_catalog (branch_code, catalog_version)
                VALUES (%s, %s)
                ON CONFLICT (branch_code) DO UPDATE
                    SET catalog_version = EXCLUDED.catalog_version,
                        active = TRUE
                """,
                (branch_code, next_version),
                auto_commit=False,
            )

            publication = self.execute_returning_one(
                """
                INSERT INTO quality.audit_5s_catalog_publications (
                    branch_code,
                    catalog_version,
                    published_by_user_id,
                    criteria_count,
                    notes
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id,
                          branch_code,
                          catalog_version,
                          published_by_user_id,
                          published_at,
                          criteria_count,
                          notes
                """,
                (
                    branch_code,
                    next_version,
                    published_by_user_id,
                    len(criteria),
                    notes,
                ),
                auto_commit=False,
            )
            self.commit()
        except Exception:
            self.rollback()
            raise

        if not publication:
            raise PluginsRepositoryError("Falha ao registrar publicação do catálogo.")

        return {
            "branch_code": branch_code,
            "catalog_version": next_version,
            "criteria_count": len(criteria),
            "published_at": publication["published_at"],
            "published_by_user_id": publication["published_by_user_id"],
            "publication_id": publication["id"],
        }

    def criterion_belongs_to_catalog_version(
        self,
        *,
        criterion_id: str,
        catalog_version: int,
    ) -> bool:
        row = self.fetch_one(
            """
            SELECT 1
              FROM quality.audit_5s_criteria
             WHERE id = %s
               AND catalog_version = %s
               AND active = TRUE
            """,
            (criterion_id, catalog_version),
        )
        return row is not None

    def list_audits(
        self,
        branch_code: str,
        *,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT a.id,
                   a.branch_code,
                   a.audit_code,
                   a.audit_date,
                   a.area_responsible,
                   a.shift,
                   a.status,
                   a.overall_score_pct,
                   ar.name AS area_name,
                   a.created_at,
                   a.updated_at,
                   (
                       SELECT string_agg(aud.display_name, ', ' ORDER BY aud.display_name)
                         FROM quality.audit_5s_auditors aud
                        WHERE aud.audit_id = a.id
                   ) AS auditor_names
              FROM quality.audit_5s_audits a
              JOIN quality.audit_5s_areas ar ON ar.id = a.area_id
             WHERE a.branch_code = %s
        """
        params: list[Any] = [branch_code]
        if status:
            query += " AND a.status = %s"
            params.append(status)
        query += " ORDER BY a.audit_date DESC, a.created_at DESC"
        return self.fetch_all(query, tuple(params))

    def get_audit(self, audit_id: str) -> dict[str, Any] | None:
        audit = self.fetch_one(
            """
            SELECT a.id,
                   a.branch_code,
                   a.audit_code,
                   a.catalog_version,
                   a.audit_date,
                   a.area_id,
                   ar.name AS area_name,
                   a.area_responsible,
                   a.shift,
                   a.status,
                   a.overall_score_pct,
                   a.senso_scores,
                   a.created_by_user_id,
                   a.created_at,
                   a.updated_at
              FROM quality.audit_5s_audits a
              JOIN quality.audit_5s_areas ar ON ar.id = a.area_id
             WHERE a.id = %s
            """,
            (audit_id,),
        )
        if not audit:
            return None

        auditors = self.fetch_all(
            """
            SELECT id, user_id, display_name
              FROM quality.audit_5s_auditors
             WHERE audit_id = %s
             ORDER BY display_name
            """,
            (audit_id,),
        )

        criteria = self.list_criteria_catalog(int(audit["catalog_version"]))
        responses = self.fetch_all(
            """
            SELECT r.id,
                   r.criterion_id,
                   r.score,
                   r.is_not_applicable,
                   r.observation,
                   r.version,
                   r.updated_by_user_id,
                   r.updated_at
              FROM quality.audit_5s_responses r
             WHERE r.audit_id = %s
            """,
            (audit_id,),
        )
        attachments_by_response = {
            str(item["response_id"]): item
            for item in self.list_response_attachments_for_audit(audit_id)
        }
        for response in responses:
            response["attachment"] = attachments_by_response.get(str(response["id"]))

        response_by_criterion = {str(row["criterion_id"]): row for row in responses}

        progress = self._build_progress(criteria, response_by_criterion)
        scores = self._build_scores(criteria, response_by_criterion)

        return {
            **audit,
            "auditors": auditors,
            "criteria": criteria,
            "responses": responses,
            "progress": progress,
            "scores": scores,
        }

    def create_audit(
        self,
        *,
        branch_code: str,
        audit_date: str,
        area_id: str,
        area_responsible: str,
        shift: str,
        created_by_user_id: str,
        auditors: list[dict[str, str]],
    ) -> dict[str, Any]:
        sequence_key = f"audit_5s_branch_{branch_code}"
        code_generator = PostgresSequentialCodeGenerator(connection=self.connection)
        audit_code = code_generator.next_code(sequence_key)

        audit = self.execute_returning_one(
            """
            INSERT INTO quality.audit_5s_audits (
                branch_code,
                audit_code,
                catalog_version,
                audit_date,
                area_id,
                area_responsible,
                shift,
                created_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, audit_code, status, catalog_version, branch_code, audit_date
            """,
            (
                branch_code,
                audit_code,
                self.resolve_catalog_version(branch_code),
                audit_date,
                area_id,
                area_responsible.strip(),
                shift,
                created_by_user_id,
            ),
            auto_commit=False,
        )
        if not audit:
            raise PluginsRepositoryError("Falha ao criar auditoria.")

        audit_id = str(audit["id"])
        for auditor in auditors:
            self.execute(
                """
                INSERT INTO quality.audit_5s_auditors (audit_id, user_id, display_name)
                VALUES (%s, %s, %s)
                """,
                (
                    audit_id,
                    auditor["user_id"],
                    format_person_name(auditor.get("display_name")),
                ),
                auto_commit=False,
            )

        self.commit()
        return self.get_audit(audit_id) or audit

    def update_audit(
        self,
        *,
        audit_id: str,
        audit_date: str | None = None,
        area_id: str | None = None,
        area_responsible: str | None = None,
        shift: str | None = None,
        auditors: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        audit = self.fetch_one(
            """
            SELECT id, status, branch_code
              FROM quality.audit_5s_audits
             WHERE id = %s
            """,
            (audit_id,),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] == "closed":
            raise PluginsRepositoryError(
                "Auditoria encerrada — o cabeçalho não pode mais ser editado."
            )

        if area_id is not None:
            area = self.fetch_one(
                """
                SELECT id
                  FROM quality.audit_5s_areas
                 WHERE id = %s
                   AND branch_code = %s
                   AND active = TRUE
                """,
                (area_id, audit["branch_code"]),
            )
            if not area:
                raise PluginsRepositoryError("Área auditada inválida para esta filial.")

        fields: list[str] = []
        params: list[Any] = []

        if audit_date is not None:
            fields.append("audit_date = %s")
            params.append(audit_date)
        if area_id is not None:
            fields.append("area_id = %s")
            params.append(area_id)
        if area_responsible is not None:
            fields.append("area_responsible = %s")
            params.append(area_responsible.strip())
        if shift is not None:
            fields.append("shift = %s")
            params.append(shift)

        if not fields and auditors is None:
            raise PluginsRepositoryError("Nenhuma alteração informada.")

        if auditors is not None and not auditors:
            raise PluginsRepositoryError("Informe ao menos um auditor.")

        try:
            if fields:
                fields.append("updated_at = NOW()")
                params.append(audit_id)
                self.execute(
                    f"""
                    UPDATE quality.audit_5s_audits
                       SET {", ".join(fields)}
                     WHERE id = %s
                    """,
                    tuple(params),
                    auto_commit=False,
                )

            if auditors is not None:
                self.execute(
                    "DELETE FROM quality.audit_5s_auditors WHERE audit_id = %s",
                    (audit_id,),
                    auto_commit=False,
                )
                for auditor in auditors:
                    self.execute(
                        """
                        INSERT INTO quality.audit_5s_auditors (audit_id, user_id, display_name)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            audit_id,
                            auditor["user_id"],
                            format_person_name(auditor.get("display_name")),
                        ),
                        auto_commit=False,
                    )

            self.commit()
        except Exception:
            self.rollback()
            raise

        result = self.get_audit(audit_id)
        if not result:
            raise PluginsRepositoryError("Falha ao atualizar auditoria.")
        return result

    def ensure_auditor(
        self,
        *,
        audit_id: str,
        user_id: str,
        display_name: str,
    ) -> None:
        normalized_name = format_person_name(display_name)
        self.execute(
            """
            INSERT INTO quality.audit_5s_auditors (audit_id, user_id, display_name)
            SELECT %s, %s, %s
             WHERE EXISTS (
                   SELECT 1
                     FROM quality.audit_5s_audits
                    WHERE id = %s
               )
               AND NOT EXISTS (
                   SELECT 1
                     FROM quality.audit_5s_auditors
                    WHERE audit_id = %s
                      AND user_id = %s
               )
            """,
            (audit_id, user_id, normalized_name, audit_id, audit_id, user_id),
        )

    def upsert_response(
        self,
        *,
        audit_id: str,
        criterion_id: str,
        score: int | None,
        is_not_applicable: bool,
        observation: str | None,
        updated_by_user_id: str,
        expected_version: int | None,
    ) -> dict[str, Any]:
        audit = self.fetch_one(
            "SELECT id, status, catalog_version FROM quality.audit_5s_audits WHERE id = %s",
            (audit_id,),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] != "draft":
            raise PluginsRepositoryError("Auditoria não está em fase de avaliação.")

        existing = self.fetch_one(
            """
            SELECT id, version
              FROM quality.audit_5s_responses
             WHERE audit_id = %s AND criterion_id = %s
            """,
            (audit_id, criterion_id),
        )

        if existing and expected_version is not None and int(existing["version"]) != expected_version:
            raise PluginsRepositoryError("Conflito de versão na resposta do critério.")

        if existing:
            row = self.execute_returning_one(
                """
                UPDATE quality.audit_5s_responses
                   SET score = %s,
                       is_not_applicable = %s,
                       observation = %s,
                       version = version + 1,
                       updated_by_user_id = %s,
                       updated_at = NOW()
                 WHERE audit_id = %s
                   AND criterion_id = %s
                RETURNING id, criterion_id, score, is_not_applicable, observation, version, updated_by_user_id, updated_at
                """,
                (
                    score,
                    is_not_applicable,
                    observation,
                    updated_by_user_id,
                    audit_id,
                    criterion_id,
                ),
                auto_commit=False,
            )
        else:
            row = self.execute_returning_one(
                """
                INSERT INTO quality.audit_5s_responses (
                    audit_id, criterion_id, score, is_not_applicable, observation, updated_by_user_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, criterion_id, score, is_not_applicable, observation, version, updated_by_user_id, updated_at
                """,
                (
                    audit_id,
                    criterion_id,
                    score,
                    is_not_applicable,
                    observation,
                    updated_by_user_id,
                ),
                auto_commit=False,
            )

        self._refresh_audit_scores(audit_id, int(audit["catalog_version"]))
        self.commit()
        if not row:
            raise PluginsRepositoryError("Falha ao salvar resposta.")
        attachment = self.get_response_attachment_by_response_id(str(row["id"]))
        return {**row, "attachment": attachment}

    def list_response_attachments_for_audit(self, audit_id: str) -> list[dict[str, Any]]:
        try:
            return self.fetch_all(
                """
                SELECT a.id,
                       a.response_id,
                       r.criterion_id,
                       a.file_name,
                       a.original_name,
                       a.mime_type,
                       a.size_bytes,
                       a.storage_path,
                       a.uploaded_by_user_id,
                       a.uploaded_at
                  FROM quality.audit_5s_response_attachments a
                  JOIN quality.audit_5s_responses r ON r.id = a.response_id
                 WHERE r.audit_id = %s
                 ORDER BY a.uploaded_at DESC
                """,
                (audit_id,),
            )
        except PluginsRepositoryError:
            return []

    def get_response_attachment(self, attachment_id: str) -> dict[str, Any] | None:
        try:
            return self.fetch_one(
                """
                SELECT a.id,
                       a.response_id,
                       r.audit_id,
                       r.criterion_id,
                       a.file_name,
                       a.original_name,
                       a.mime_type,
                       a.size_bytes,
                       a.storage_path,
                       a.uploaded_by_user_id,
                       a.uploaded_at
                  FROM quality.audit_5s_response_attachments a
                  JOIN quality.audit_5s_responses r ON r.id = a.response_id
                 WHERE a.id = %s
                """,
                (attachment_id,),
            )
        except PluginsRepositoryError:
            return None

    def get_response_attachment_by_response_id(
        self, response_id: str
    ) -> dict[str, Any] | None:
        try:
            return self.fetch_one(
                """
                SELECT id,
                       response_id,
                       file_name,
                       original_name,
                       mime_type,
                       size_bytes,
                       storage_path,
                       uploaded_by_user_id,
                       uploaded_at
                  FROM quality.audit_5s_response_attachments
                 WHERE response_id = %s
                 ORDER BY uploaded_at DESC
                 LIMIT 1
                """,
                (response_id,),
            )
        except PluginsRepositoryError:
            return None

    def get_response_for_criterion(
        self, *, audit_id: str, criterion_id: str
    ) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT id, score, is_not_applicable, observation, version
              FROM quality.audit_5s_responses
             WHERE audit_id = %s AND criterion_id = %s
            """,
            (audit_id, criterion_id),
        )

    def get_response_attachment_for_criterion(
        self, *, audit_id: str, criterion_id: str
    ) -> dict[str, Any] | None:
        response = self.get_response_for_criterion(
            audit_id=audit_id, criterion_id=criterion_id
        )
        if not response:
            return None
        return self.get_response_attachment_by_response_id(str(response["id"]))

    def upsert_response_attachment(
        self,
        *,
        audit_id: str,
        criterion_id: str,
        original_name: str,
        file_name: str,
        storage_path: str,
        mime_type: str | None,
        size_bytes: int,
        uploaded_by_user_id: str,
    ) -> dict[str, Any]:
        audit = self.fetch_one(
            "SELECT id, status FROM quality.audit_5s_audits WHERE id = %s",
            (audit_id,),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] != "draft":
            raise PluginsRepositoryError(
                "Foto do critério só pode ser anexada durante a avaliação."
            )

        response = self.fetch_one(
            """
            SELECT id, score, is_not_applicable
              FROM quality.audit_5s_responses
             WHERE audit_id = %s AND criterion_id = %s
            """,
            (audit_id, criterion_id),
        )
        if not response:
            raise PluginsRepositoryError(
                "Salve a nota do critério antes de anexar a foto."
            )
        if not can_attach_criterion_photo(
            response.get("score"), bool(response.get("is_not_applicable"))
        ):
            raise PluginsRepositoryError(
                "Foto do critério disponível após informar a nota (1, 3 ou 5)."
            )

        response_id = str(response["id"])
        existing = self.get_response_attachment_by_response_id(response_id)
        if existing:
            try:
                Audit5sResponseAttachmentStorage().delete_file(
                    response_id=response_id,
                    file_name=str(existing["file_name"]),
                )
            except Exception:
                pass
            self.execute(
                "DELETE FROM quality.audit_5s_response_attachments WHERE response_id = %s",
                (response_id,),
                auto_commit=False,
            )

        row = self.execute_returning_one(
            """
            INSERT INTO quality.audit_5s_response_attachments (
                response_id,
                file_name,
                original_name,
                mime_type,
                size_bytes,
                storage_path,
                uploaded_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id,
                      response_id,
                      file_name,
                      original_name,
                      mime_type,
                      size_bytes,
                      storage_path,
                      uploaded_by_user_id,
                      uploaded_at
            """,
            (
                response_id,
                file_name,
                original_name,
                mime_type,
                size_bytes,
                storage_path,
                uploaded_by_user_id,
            ),
            auto_commit=False,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao salvar foto do critério.")
        self.commit()
        return {**row, "criterion_id": criterion_id}

    def delete_response_attachment(
        self, *, audit_id: str, criterion_id: str, attachment_id: str
    ) -> None:
        audit = self.fetch_one(
            "SELECT id, status FROM quality.audit_5s_audits WHERE id = %s",
            (audit_id,),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] != "draft":
            raise PluginsRepositoryError(
                "Foto do critério só pode ser removida durante a avaliação."
            )

        attachment = self.get_response_attachment(attachment_id)
        if (
            not attachment
            or str(attachment["audit_id"]) != audit_id
            or str(attachment["criterion_id"]) != criterion_id
        ):
            raise PluginsRepositoryError("Foto do critério não encontrada.")

        response_id = str(attachment["response_id"])
        try:
            Audit5sResponseAttachmentStorage().delete_file(
                response_id=response_id,
                file_name=str(attachment["file_name"]),
            )
        except Exception:
            pass

        self.execute(
            "DELETE FROM quality.audit_5s_response_attachments WHERE id = %s",
            (attachment_id,),
        )

    def seed_nc_before_from_response_attachment(
        self,
        *,
        nonconformity_id: str,
        response_id: str,
        uploaded_by_user_id: str,
    ) -> dict[str, Any] | None:
        existing_before = any(
            item.get("attachment_type") == "before"
            for item in self.list_nc_attachments(nonconformity_id)
        )
        if existing_before:
            return None

        source = self.get_response_attachment_by_response_id(response_id)
        if not source:
            return None

        response_storage = Audit5sResponseAttachmentStorage()
        nc_storage = Audit5sNcAttachmentStorage()
        try:
            source_path = response_storage.resolve_file(
                response_id=response_id,
                file_name=str(source["file_name"]),
            )
            content = source_path.read_bytes()
        except Exception as exc:
            raise PluginsRepositoryError(
                f"Não foi possível reutilizar a foto da avaliação: {exc}"
            ) from exc

        original_name = str(source.get("original_name") or source["file_name"])
        mime_type = source.get("mime_type")
        size_bytes = len(content)
        stored_name = nc_storage.save(
            nonconformity_id=nonconformity_id,
            attachment_type="before",
            original_name=original_name,
            content=content,
            mime_type=mime_type,
        )

        try:
            row = self.execute_returning_one(
                """
                INSERT INTO quality.audit_5s_nc_attachments (
                    nonconformity_id,
                    attachment_type,
                    original_name,
                    stored_name,
                    mime_type,
                    size_bytes,
                    uploaded_by_user_id
                ) VALUES (%s, 'before', %s, %s, %s, %s, %s)
                ON CONFLICT (nonconformity_id, attachment_type)
                DO NOTHING
                RETURNING id,
                          nonconformity_id,
                          attachment_type,
                          original_name,
                          stored_name,
                          mime_type,
                          size_bytes,
                          uploaded_by_user_id,
                          created_at
                """,
                (
                    nonconformity_id,
                    original_name,
                    stored_name,
                    mime_type,
                    size_bytes,
                    uploaded_by_user_id,
                ),
                auto_commit=False,
            )
            if not row:
                return None

            self.execute(
                """
                INSERT INTO quality.audit_5s_nc_events (
                    nonconformity_id, event_type, payload, actor_user_id
                ) VALUES (%s, 'attachment_uploaded', %s::jsonb, %s)
                """,
                (
                    nonconformity_id,
                    self._json_dumps(
                        {
                            "attachment_id": str(row["id"]),
                            "attachment_type": "before",
                            "original_name": original_name,
                            "seeded_from_evaluation": True,
                        }
                    ),
                    uploaded_by_user_id,
                ),
                auto_commit=False,
            )
            self.commit()
            return row
        except PluginsRepositoryError:
            try:
                nc_storage.resolve_file(
                    nonconformity_id=nonconformity_id,
                    stored_name=stored_name,
                ).unlink(missing_ok=True)
            except Exception:
                pass
            raise

    def complete_evaluation(self, audit_id: str) -> dict[str, Any]:
        audit = self.get_audit(audit_id)
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] != "draft":
            raise PluginsRepositoryError("Auditoria já concluiu a fase de avaliação.")

        if not is_evaluation_complete(
            total_criteria=audit["progress"]["total"],
            scored_criteria=audit["progress"]["scored"],
        ):
            raise PluginsRepositoryError(
                "Todos os critérios precisam receber uma nota (1, 3, 5 ou NA)."
            )

        self.execute(
            """
            UPDATE quality.audit_5s_audits
               SET status = 'evaluation_complete',
                   updated_at = NOW()
             WHERE id = %s
            """,
            (audit_id,),
        )
        refreshed = self.get_audit(audit_id)
        if not refreshed:
            raise PluginsRepositoryError("Falha ao concluir avaliação.")
        return refreshed

    def reopen_evaluation(self, audit_id: str) -> dict[str, Any]:
        audit = self.get_audit(audit_id)
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")

        status = str(audit["status"])
        if status == "draft":
            raise PluginsRepositoryError("A auditoria já está em fase de avaliação.")
        if status == "closed":
            raise PluginsRepositoryError(
                "Auditorias encerradas não podem ser reabertas para avaliação."
            )
        if status not in ("evaluation_complete", "nc_in_progress"):
            raise PluginsRepositoryError("Auditoria não pode ser reaberta neste status.")

        if self.list_nonconformities(audit_id):
            raise PluginsRepositoryError(
                "Não é possível reabrir a avaliação enquanto houver não conformidades registradas."
            )

        self.execute(
            """
            UPDATE quality.audit_5s_audits
               SET status = 'draft',
                   updated_at = NOW()
             WHERE id = %s
            """,
            (audit_id,),
        )
        refreshed = self.get_audit(audit_id)
        if not refreshed:
            raise PluginsRepositoryError("Falha ao reabrir avaliação.")
        return refreshed

    def list_nc_candidates(self, audit_id: str) -> list[dict[str, Any]]:
        audit = self.get_audit(audit_id)
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")

        candidates: list[dict[str, Any]] = []
        response_by_criterion = {str(row["criterion_id"]): row for row in audit["responses"]}

        for criterion in audit["criteria"]:
            response = response_by_criterion.get(str(criterion["id"]))
            if not response:
                continue
            if is_nc_candidate(response.get("score"), bool(response.get("is_not_applicable"))):
                candidates.append({**criterion, "response": response})
        return candidates

    _NC_LIST_EXTENDED_SQL = """
            SELECT nc.id,
                   nc.audit_id,
                   nc.response_id,
                   nc.description,
                   nc.root_cause,
                   nc.corrective_action,
                   nc.responsible_name,
                   nc.due_date,
                   nc.priority,
                   nc.status,
                   nc.created_at,
                   nc.updated_at,
                   c.code AS criterion_code,
                   c.description AS criterion_description,
                   s.sort_order AS senso_order,
                   s.name AS senso_name
              FROM quality.audit_5s_nonconformities nc
              JOIN quality.audit_5s_responses r ON r.id = nc.response_id
              JOIN quality.audit_5s_criteria c ON c.id = r.criterion_id
              JOIN quality.audit_5s_sensos s ON s.id = c.senso_id
             WHERE nc.audit_id = %s
             ORDER BY s.sort_order, c.sort_order
            """

    _NC_LIST_LEGACY_SQL = """
            SELECT nc.id,
                   nc.audit_id,
                   nc.response_id,
                   nc.description,
                   nc.responsible_name,
                   nc.due_date,
                   nc.status,
                   nc.created_at,
                   c.code AS criterion_code,
                   c.description AS criterion_description,
                   s.sort_order AS senso_order,
                   s.name AS senso_name
              FROM quality.audit_5s_nonconformities nc
              JOIN quality.audit_5s_responses r ON r.id = nc.response_id
              JOIN quality.audit_5s_criteria c ON c.id = r.criterion_id
              JOIN quality.audit_5s_sensos s ON s.id = c.senso_id
             WHERE nc.audit_id = %s
             ORDER BY s.sort_order, c.sort_order
            """

    @classmethod
    def _augment_nc_legacy_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            **row,
            "root_cause": None,
            "corrective_action": None,
            "priority": None,
            "updated_at": row.get("created_at"),
        }

    def list_nonconformities(self, audit_id: str) -> list[dict[str, Any]]:
        try:
            return self.fetch_all(self._NC_LIST_EXTENDED_SQL, (audit_id,))
        except PluginsRepositoryError:
            rows = self.fetch_all(self._NC_LIST_LEGACY_SQL, (audit_id,))
            return [self._augment_nc_legacy_row(row) for row in rows]

    def create_nonconformity(
        self,
        *,
        audit_id: str,
        response_id: str,
        description: str,
        responsible_name: str,
        due_date: str,
        root_cause: str | None = None,
        corrective_action: str | None = None,
        priority: str | None = None,
        created_by_user_id: str,
    ) -> dict[str, Any]:
        audit = self.fetch_one(
            "SELECT id, status FROM quality.audit_5s_audits WHERE id = %s",
            (audit_id,),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] not in ("evaluation_complete", "nc_in_progress"):
            raise PluginsRepositoryError("Auditoria não está na fase de NC.")

        response = self.fetch_one(
            """
            SELECT id, score, is_not_applicable
              FROM quality.audit_5s_responses
             WHERE id = %s AND audit_id = %s
            """,
            (response_id, audit_id),
        )
        if not response:
            raise PluginsRepositoryError("Resposta do critério não encontrada.")
        if not is_nc_candidate(response.get("score"), bool(response.get("is_not_applicable"))):
            raise PluginsRepositoryError("Critério não elegível para NC.")

        existing = self.fetch_one(
            "SELECT id FROM quality.audit_5s_nonconformities WHERE response_id = %s",
            (response_id,),
        )
        if existing:
            raise PluginsRepositoryError("NC já registrada para este critério.")

        row = self._insert_nonconformity_row(
            audit_id=audit_id,
            response_id=response_id,
            description=description.strip(),
            responsible_name=responsible_name.strip(),
            due_date=due_date,
            root_cause=self._normalize_text(root_cause),
            corrective_action=self._normalize_text(corrective_action),
            priority=priority,
            created_by_user_id=created_by_user_id,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao registrar NC.")

        nc_id = str(row["id"])
        self.execute(
            """
            INSERT INTO quality.audit_5s_nc_events (
                nonconformity_id, event_type, payload, actor_user_id
            ) VALUES (%s, 'created', '{}'::jsonb, %s)
            """,
            (nc_id, created_by_user_id),
            auto_commit=False,
        )
        self.execute(
            """
            UPDATE quality.audit_5s_audits
               SET status = 'nc_in_progress', updated_at = NOW()
             WHERE id = %s AND status = 'evaluation_complete'
            """,
            (audit_id,),
            auto_commit=False,
        )
        row = self._maybe_promote_nc_to_in_progress(nc_id, row)
        self.commit()
        try:
            self.seed_nc_before_from_response_attachment(
                nonconformity_id=nc_id,
                response_id=response_id,
                uploaded_by_user_id=created_by_user_id,
            )
        except Exception:
            # Plano da NC já foi criado; evidência "antes" permanece opcional até o upload manual.
            pass
        return row

    def _insert_nonconformity_row(
        self,
        *,
        audit_id: str,
        response_id: str,
        description: str,
        responsible_name: str,
        due_date: str,
        root_cause: str | None,
        corrective_action: str | None,
        priority: str | None,
        created_by_user_id: str,
    ) -> dict[str, Any] | None:
        extended_params = (
            audit_id,
            response_id,
            description,
            root_cause,
            corrective_action,
            responsible_name,
            due_date,
            priority,
            created_by_user_id,
        )
        try:
            return self.execute_returning_one(
                """
                INSERT INTO quality.audit_5s_nonconformities (
                    audit_id,
                    response_id,
                    description,
                    root_cause,
                    corrective_action,
                    responsible_name,
                    due_date,
                    priority,
                    created_by_user_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id,
                          audit_id,
                          response_id,
                          description,
                          root_cause,
                          corrective_action,
                          responsible_name,
                          due_date,
                          priority,
                          status,
                          created_at,
                          updated_at
                """,
                extended_params,
                auto_commit=False,
            )
        except PluginsRepositoryError:
            legacy_row = self.execute_returning_one(
                """
                INSERT INTO quality.audit_5s_nonconformities (
                    audit_id, response_id, description, responsible_name, due_date, created_by_user_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, audit_id, response_id, description, responsible_name, due_date, status, created_at
                """,
                (
                    audit_id,
                    response_id,
                    description,
                    responsible_name,
                    due_date,
                    created_by_user_id,
                ),
                auto_commit=False,
            )
            if not legacy_row:
                return None
            return self._augment_nc_legacy_row(legacy_row)

    def _update_nonconformity_row(
        self,
        *,
        nonconformity_id: str,
        updates: list[str],
        params: list[Any],
    ) -> dict[str, Any] | None:
        extended_updates = [*updates, "updated_at = NOW()"]
        extended_params = [*params, nonconformity_id]
        try:
            return self.execute_returning_one(
                f"""
                UPDATE quality.audit_5s_nonconformities
                   SET {", ".join(extended_updates)}
                 WHERE id = %s
                RETURNING id,
                          audit_id,
                          response_id,
                          description,
                          root_cause,
                          corrective_action,
                          responsible_name,
                          due_date,
                          priority,
                          status,
                          created_at,
                          updated_at
                """,
                tuple(extended_params),
                auto_commit=False,
            )
        except PluginsRepositoryError:
            legacy_pairs = [
                (clause, param)
                for clause, param in zip(updates, params)
                if not clause.startswith(
                    ("root_cause =", "corrective_action =", "priority ="),
                )
            ]
            if not legacy_pairs:
                return None

            legacy_updates = [clause for clause, _ in legacy_pairs]
            legacy_updates.append("updated_at = NOW()")
            legacy_params = [param for _, param in legacy_pairs]
            legacy_params.append(nonconformity_id)

            legacy_row = self.execute_returning_one(
                f"""
                UPDATE quality.audit_5s_nonconformities
                   SET {", ".join(legacy_updates)}
                 WHERE id = %s
                RETURNING id,
                          audit_id,
                          response_id,
                          description,
                          responsible_name,
                          due_date,
                          status,
                          created_at
                """,
                tuple(legacy_params),
                auto_commit=False,
            )
            if not legacy_row:
                return None
            return self._augment_nc_legacy_row(legacy_row)

    def update_nonconformity(
        self,
        *,
        nonconformity_id: str,
        description: str | None = None,
        responsible_name: str | None = None,
        due_date: str | None = None,
        root_cause: str | None = None,
        corrective_action: str | None = None,
        priority: str | None = None,
        actor_user_id: str,
    ) -> dict[str, Any]:
        nc = self.fetch_one(
            """
            SELECT id, audit_id, status
              FROM quality.audit_5s_nonconformities
             WHERE id = %s
            """,
            (nonconformity_id,),
        )
        if not nc:
            raise PluginsRepositoryError("NC não encontrada.")

        audit = self.fetch_one(
            "SELECT id, status FROM quality.audit_5s_audits WHERE id = %s",
            (nc["audit_id"],),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] == "closed":
            raise PluginsRepositoryError("Auditoria encerrada — NC não pode ser alterada.")
        if nc["status"] == "closed":
            raise PluginsRepositoryError("NC finalizada — altere apenas visualizando as evidências.")

        updates: list[str] = []
        params: list[Any] = []
        payload: dict[str, Any] = {}

        if description is not None:
            updates.append("description = %s")
            params.append(description.strip())
            payload["description"] = description.strip()
        if responsible_name is not None:
            updates.append("responsible_name = %s")
            params.append(responsible_name.strip())
            payload["responsible_name"] = responsible_name.strip()
        if due_date is not None:
            updates.append("due_date = %s")
            params.append(due_date)
            payload["due_date"] = due_date
        if root_cause is not None:
            normalized = self._normalize_text(root_cause)
            updates.append("root_cause = %s")
            params.append(normalized)
            payload["root_cause"] = normalized
        if corrective_action is not None:
            normalized = self._normalize_text(corrective_action)
            updates.append("corrective_action = %s")
            params.append(normalized)
            payload["corrective_action"] = normalized
        if priority is not None:
            updates.append("priority = %s")
            params.append(priority)
            payload["priority"] = priority

        if not updates:
            row = self.fetch_one(
                """
                SELECT id,
                       audit_id,
                       response_id,
                       description,
                       root_cause,
                       corrective_action,
                       responsible_name,
                       due_date,
                       priority,
                       status,
                       created_at,
                       updated_at
                  FROM quality.audit_5s_nonconformities
                 WHERE id = %s
                """,
                (nonconformity_id,),
            )
            if not row:
                raise PluginsRepositoryError("NC não encontrada.")
            return self._augment_nc_legacy_row(row) if "root_cause" not in row else row

        row = self._update_nonconformity_row(
            nonconformity_id=nonconformity_id,
            updates=updates,
            params=params,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao atualizar NC.")

        self.execute(
            """
            INSERT INTO quality.audit_5s_nc_events (
                nonconformity_id, event_type, payload, actor_user_id
            ) VALUES (%s, 'updated', %s::jsonb, %s)
            """,
            (
                nonconformity_id,
                self._json_dumps(payload),
                actor_user_id,
            ),
            auto_commit=False,
        )
        self.execute(
            """
            UPDATE quality.audit_5s_audits
               SET status = 'nc_in_progress', updated_at = NOW()
             WHERE id = %s AND status = 'evaluation_complete'
            """,
            (str(nc["audit_id"]),),
            auto_commit=False,
        )
        row = self._maybe_promote_nc_to_in_progress(nonconformity_id, row)
        self.commit()
        return row

    def add_nc_action(
        self,
        *,
        nonconformity_id: str,
        description: str,
        actor_user_id: str,
        actor_display_name: str,
    ) -> dict[str, Any]:
        nc = self.fetch_one(
            "SELECT id, status FROM quality.audit_5s_nonconformities WHERE id = %s",
            (nonconformity_id,),
        )
        if not nc:
            raise PluginsRepositoryError("NC não encontrada.")

        action = self.execute_returning_one(
            """
            INSERT INTO quality.audit_5s_nc_actions (
                nonconformity_id, description, actor_user_id, actor_display_name
            ) VALUES (%s, %s, %s, %s)
            RETURNING id, nonconformity_id, description, actor_user_id, actor_display_name, created_at
            """,
            (
                nonconformity_id,
                description.strip(),
                actor_user_id,
                actor_display_name,
            ),
            auto_commit=False,
        )
        if not action:
            raise PluginsRepositoryError("Falha ao registrar ação.")

        self.execute(
            """
            INSERT INTO quality.audit_5s_nc_events (
                nonconformity_id, event_type, payload, actor_user_id
            ) VALUES (%s, 'action_added', %s::jsonb, %s)
            """,
            (
                nonconformity_id,
                self._json_dumps({"action_id": str(action["id"]), "description": description.strip()}),
                actor_user_id,
            ),
            auto_commit=False,
        )
        self.execute(
            """
            UPDATE quality.audit_5s_nonconformities
               SET status = 'in_progress', updated_at = NOW()
             WHERE id = %s AND status = 'open'
            """,
            (nonconformity_id,),
            auto_commit=False,
        )
        self.commit()
        return action

    def list_nc_actions(self, nonconformity_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, description, actor_user_id, actor_display_name, created_at
              FROM quality.audit_5s_nc_actions
             WHERE nonconformity_id = %s
             ORDER BY created_at ASC
            """,
            (nonconformity_id,),
        )

    def list_nc_attachments(self, nonconformity_id: str) -> list[dict[str, Any]]:
        try:
            return self.fetch_all(
                """
                SELECT id,
                       nonconformity_id,
                       attachment_type,
                       original_name,
                       stored_name,
                       mime_type,
                       size_bytes,
                       uploaded_by_user_id,
                       created_at
                  FROM quality.audit_5s_nc_attachments
                 WHERE nonconformity_id = %s
                 ORDER BY attachment_type
                """,
                (nonconformity_id,),
            )
        except PluginsRepositoryError:
            return []

    def list_nc_attachments_for_audit(self, audit_id: str) -> list[dict[str, Any]]:
        try:
            return self.fetch_all(
                """
                SELECT a.id,
                       a.nonconformity_id,
                       a.attachment_type,
                       a.original_name,
                       a.stored_name,
                       a.mime_type,
                       a.size_bytes,
                       a.uploaded_by_user_id,
                       a.created_at
                  FROM quality.audit_5s_nc_attachments a
                  JOIN quality.audit_5s_nonconformities nc ON nc.id = a.nonconformity_id
                 WHERE nc.audit_id = %s
                 ORDER BY nc.id, a.attachment_type
                """,
                (audit_id,),
            )
        except PluginsRepositoryError:
            return []

    def get_nc_attachment(self, attachment_id: str) -> dict[str, Any] | None:
        try:
            return self.fetch_one(
                """
                SELECT id,
                       nonconformity_id,
                       attachment_type,
                       original_name,
                       stored_name,
                       mime_type,
                       size_bytes,
                       uploaded_by_user_id,
                       created_at
                  FROM quality.audit_5s_nc_attachments
                 WHERE id = %s
                """,
                (attachment_id,),
            )
        except PluginsRepositoryError:
            return None

    def upsert_nc_attachment(
        self,
        *,
        nonconformity_id: str,
        attachment_type: str,
        original_name: str,
        stored_name: str,
        mime_type: str | None,
        size_bytes: int,
        uploaded_by_user_id: str,
    ) -> dict[str, Any]:
        nc = self.fetch_one(
            """
            SELECT id, audit_id, status
              FROM quality.audit_5s_nonconformities
             WHERE id = %s
            """,
            (nonconformity_id,),
        )
        if not nc:
            raise PluginsRepositoryError("NC não encontrada.")
        if nc["status"] == "closed":
            raise PluginsRepositoryError("NC finalizada — evidências não podem ser alteradas.")

        audit = self.fetch_one(
            "SELECT status FROM quality.audit_5s_audits WHERE id = %s",
            (nc["audit_id"],),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] == "closed":
            raise PluginsRepositoryError("Auditoria encerrada.")

        row = self.execute_returning_one(
            """
            INSERT INTO quality.audit_5s_nc_attachments (
                nonconformity_id,
                attachment_type,
                original_name,
                stored_name,
                mime_type,
                size_bytes,
                uploaded_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (nonconformity_id, attachment_type)
            DO UPDATE SET
                original_name = EXCLUDED.original_name,
                stored_name = EXCLUDED.stored_name,
                mime_type = EXCLUDED.mime_type,
                size_bytes = EXCLUDED.size_bytes,
                uploaded_by_user_id = EXCLUDED.uploaded_by_user_id,
                created_at = NOW()
            RETURNING id,
                      nonconformity_id,
                      attachment_type,
                      original_name,
                      stored_name,
                      mime_type,
                      size_bytes,
                      uploaded_by_user_id,
                      created_at
            """,
            (
                nonconformity_id,
                attachment_type,
                original_name,
                stored_name,
                mime_type,
                size_bytes,
                uploaded_by_user_id,
            ),
            auto_commit=False,
        )
        if not row:
            raise PluginsRepositoryError("Falha ao salvar evidência.")

        self.execute(
            """
            INSERT INTO quality.audit_5s_nc_events (
                nonconformity_id, event_type, payload, actor_user_id
            ) VALUES (%s, 'attachment_uploaded', %s::jsonb, %s)
            """,
            (
                nonconformity_id,
                self._json_dumps(
                    {
                        "attachment_id": str(row["id"]),
                        "attachment_type": attachment_type,
                        "original_name": original_name,
                    }
                ),
                uploaded_by_user_id,
            ),
            auto_commit=False,
        )
        self.commit()
        return row

    def complete_nc_action(
        self,
        *,
        nonconformity_id: str,
        actor_user_id: str,
    ) -> dict[str, Any]:
        nc = self.fetch_one(
            """
            SELECT id,
                   audit_id,
                   description,
                   root_cause,
                   corrective_action,
                   responsible_name,
                   due_date,
                   status
              FROM quality.audit_5s_nonconformities
             WHERE id = %s
            """,
            (nonconformity_id,),
        )
        if not nc:
            raise PluginsRepositoryError("NC não encontrada.")
        if nc["status"] == "closed":
            return self._get_nonconformity_by_id(nonconformity_id) or nc

        audit = self.fetch_one(
            "SELECT status FROM quality.audit_5s_audits WHERE id = %s",
            (nc["audit_id"],),
        )
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] == "closed":
            raise PluginsRepositoryError("Auditoria encerrada.")

        if not self._is_nc_plan_complete(nc):
            raise PluginsRepositoryError(
                "Preencha descrição, causa, ação corretiva, responsável e prazo antes de finalizar."
            )

        attachments = self.list_nc_attachments(nonconformity_id)
        has_before = any(item["attachment_type"] == "before" for item in attachments)
        has_after = any(item["attachment_type"] == "after" for item in attachments)
        if not has_before or not has_after:
            raise PluginsRepositoryError(
                "Anexe a foto do antes e do depois para finalizar a ação."
            )

        row = self._update_nonconformity_row(
            nonconformity_id=nonconformity_id,
            updates=["status = %s"],
            params=["closed"],
        )
        if not row:
            raise PluginsRepositoryError("Falha ao finalizar NC.")

        self.execute(
            """
            INSERT INTO quality.audit_5s_nc_events (
                nonconformity_id, event_type, payload, actor_user_id
            ) VALUES (%s, 'action_completed', '{}'::jsonb, %s)
            """,
            (nonconformity_id, actor_user_id),
            auto_commit=False,
        )
        self.execute(
            """
            UPDATE quality.audit_5s_audits
               SET status = 'nc_in_progress', updated_at = NOW()
             WHERE id = %s AND status = 'evaluation_complete'
            """,
            (str(nc["audit_id"]),),
            auto_commit=False,
        )
        self.commit()
        return self._get_nonconformity_by_id(nonconformity_id) or row

    def close_audit(self, audit_id: str) -> dict[str, Any]:
        audit = self.get_audit(audit_id)
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] not in ("evaluation_complete", "nc_in_progress"):
            raise PluginsRepositoryError("Auditoria não pode ser encerrada neste status.")

        candidates = self.list_nc_candidates(audit_id)
        ncs = self.list_nonconformities(audit_id)
        if candidates and len(ncs) < len(candidates):
            raise PluginsRepositoryError(
                "Registre NC para todos os critérios abaixo da nota máxima antes de encerrar."
            )

        pending = [item for item in ncs if item.get("status") != "closed"]
        if pending:
            raise PluginsRepositoryError(
                "Finalize todas as ações corretivas com evidências antes de encerrar a auditoria."
            )

        self.execute(
            """
            UPDATE quality.audit_5s_audits
               SET status = 'closed', updated_at = NOW()
             WHERE id = %s
            """,
            (audit_id,),
        )
        refreshed = self.get_audit(audit_id)
        if not refreshed:
            raise PluginsRepositoryError("Falha ao encerrar auditoria.")
        return refreshed

    def get_audit_delete_target(self, audit_id: str) -> dict[str, Any] | None:
        normalized_id = audit_id.strip()
        if not normalized_id:
            return None

        return self.fetch_one(
            """
            SELECT a.id,
                   a.branch_code,
                   a.audit_code,
                   a.status
              FROM quality.audit_5s_audits a
             WHERE a.id = %s::uuid
            """,
            (normalized_id,),
        )

    def purge_audit_files(self, audit_id: str) -> None:
        nc_storage = Audit5sNcAttachmentStorage()
        response_storage = Audit5sResponseAttachmentStorage()

        for item in self.list_nc_attachments_for_audit(audit_id):
            nc_storage.delete_nonconformity_dir(str(item["nonconformity_id"]))

        response_ids = {
            str(item["response_id"])
            for item in self.list_response_attachments_for_audit(audit_id)
        }
        for response_id in response_ids:
            response_storage.delete_response_dir(response_id)

    def delete_audit(self, audit_id: str) -> None:
        normalized_id = audit_id.strip()
        audit = self.get_audit_delete_target(normalized_id)
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")
        if audit["status"] != "draft":
            raise PluginsRepositoryError(
                "Somente auditorias em avaliação podem ser excluídas."
            )

        self._delete_audit_cascade(normalized_id)

    def force_delete_audit(self, audit_id: str) -> None:
        normalized_id = audit_id.strip()
        audit = self.get_audit_delete_target(normalized_id)
        if not audit:
            raise PluginsRepositoryError("Auditoria não encontrada.")

        self._delete_audit_cascade(normalized_id)

    def _delete_audit_cascade(self, normalized_id: str) -> None:
        self.purge_audit_files(normalized_id)
        self.execute(
            """
            DELETE FROM quality.audit_5s_audits
             WHERE id = %s::uuid
            """,
            (normalized_id,),
        )

    def _refresh_audit_scores(self, audit_id: str, catalog_version: int) -> None:
        criteria = self.list_criteria_catalog(catalog_version)
        responses = self.fetch_all(
            """
            SELECT criterion_id, score, is_not_applicable
              FROM quality.audit_5s_responses
             WHERE audit_id = %s
            """,
            (audit_id,),
        )
        response_by_criterion = {str(row["criterion_id"]): row for row in responses}
        scores = self._build_scores(criteria, response_by_criterion)

        self.execute(
            """
            UPDATE quality.audit_5s_audits
               SET overall_score_pct = %s,
                   senso_scores = %s::jsonb,
                   updated_at = NOW()
             WHERE id = %s
            """,
            (
                scores["overall_percentual"],
                self._json_dumps(scores["sensos"]),
                audit_id,
            ),
            auto_commit=False,
        )

    def _build_progress(
        self,
        criteria: list[dict[str, Any]],
        response_by_criterion: dict[str, dict[str, Any]],
    ) -> dict[str, int]:
        total = len(criteria)
        scored = 0
        for criterion in criteria:
            response = response_by_criterion.get(str(criterion["id"]))
            if not response:
                continue
            if response.get("is_not_applicable") or response.get("score") is not None:
                scored += 1
        return {"total": total, "scored": scored, "pending": total - scored}

    def _build_scores(
        self,
        criteria: list[dict[str, Any]],
        response_by_criterion: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        by_senso: dict[int, list[CriterionScoreInput]] = {}
        for criterion in criteria:
            senso_order = int(criterion["senso_order"])
            by_senso.setdefault(senso_order, [])
            response = response_by_criterion.get(str(criterion["id"]))
            if not response:
                by_senso[senso_order].append(
                    CriterionScoreInput(senso_order=senso_order, score=None, is_not_applicable=False)
                )
                continue
            by_senso[senso_order].append(
                CriterionScoreInput(
                    senso_order=senso_order,
                    score=response.get("score"),
                    is_not_applicable=bool(response.get("is_not_applicable")),
                )
            )

        senso_scores: list[dict[str, Any]] = []
        senso_percentuals: list[float | None] = []
        for senso_order in sorted(by_senso):
            percentual = calculate_senso_percentual(by_senso[senso_order])
            senso_percentuals.append(percentual)
            senso_scores.append(
                {
                    "senso_order": senso_order,
                    "percentual": percentual,
                }
            )

        return {
            "sensos": senso_scores,
            "overall_percentual": calculate_overall_percentual(senso_percentuals),
        }

    @staticmethod
    def _is_nc_plan_complete(row: dict[str, Any]) -> bool:
        description = str(row.get("description") or "").strip()
        root_cause = str(row.get("root_cause") or "").strip()
        corrective_action = str(row.get("corrective_action") or "").strip()
        responsible_name = str(row.get("responsible_name") or "").strip()
        due_date = row.get("due_date")
        return (
            len(description) >= 3
            and len(root_cause) >= 3
            and len(corrective_action) >= 3
            and len(responsible_name) >= 2
            and bool(due_date)
        )

    def _get_nonconformity_by_id(self, nonconformity_id: str) -> dict[str, Any] | None:
        rows = self.fetch_all(
            """
            SELECT nc.id,
                   nc.audit_id,
                   nc.response_id,
                   nc.description,
                   nc.root_cause,
                   nc.corrective_action,
                   nc.responsible_name,
                   nc.due_date,
                   nc.priority,
                   nc.status,
                   nc.created_at,
                   nc.updated_at,
                   c.code AS criterion_code,
                   c.description AS criterion_description,
                   s.sort_order AS senso_order,
                   s.name AS senso_name
              FROM quality.audit_5s_nonconformities nc
              JOIN quality.audit_5s_responses r ON r.id = nc.response_id
              JOIN quality.audit_5s_criteria c ON c.id = r.criterion_id
              JOIN quality.audit_5s_sensos s ON s.id = c.senso_id
             WHERE nc.id = %s
            """,
            (nonconformity_id,),
        )
        if not rows:
            try:
                legacy_rows = self.fetch_all(
                    """
                    SELECT nc.id,
                           nc.audit_id,
                           nc.response_id,
                           nc.description,
                           nc.responsible_name,
                           nc.due_date,
                           nc.status,
                           nc.created_at,
                           c.code AS criterion_code,
                           c.description AS criterion_description,
                           s.sort_order AS senso_order,
                           s.name AS senso_name
                      FROM quality.audit_5s_nonconformities nc
                      JOIN quality.audit_5s_responses r ON r.id = nc.response_id
                      JOIN quality.audit_5s_criteria c ON c.id = r.criterion_id
                      JOIN quality.audit_5s_sensos s ON s.id = c.senso_id
                     WHERE nc.id = %s
                    """,
                    (nonconformity_id,),
                )
                if not legacy_rows:
                    return None
                return self._augment_nc_legacy_row(legacy_rows[0])
            except PluginsRepositoryError:
                return None
        return rows[0]

    def _maybe_promote_nc_to_in_progress(
        self,
        nonconformity_id: str,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        if row.get("status") != "open":
            return row
        if not self._is_nc_plan_complete(row):
            return row
        promoted = self._update_nonconformity_row(
            nonconformity_id=nonconformity_id,
            updates=["status = %s"],
            params=["in_progress"],
        )
        return promoted or row

    def get_dashboard(self, request: GetAudit5sDashboardRequest) -> dict[str, Any]:
        where_sql, params = self._dashboard_filter_clause(
            branch_code=request.branch_code,
            date_start=request.date_start.isoformat(),
            date_end=request.date_end.isoformat(),
            area_id=request.area_id,
            shift=request.shift,
            audit_status=request.audit_status,
        )
        senso_order = request.senso_order
        senso_name = self._dashboard_senso_name(senso_order) if senso_order else None
        nc_senso_sql, nc_senso_params = self._dashboard_nc_senso_clause(senso_order)

        if senso_order:
            score_base_where = (
                f"{where_sql} AND a.status != 'draft' AND senso_score.score_pct IS NOT NULL"
            )
            summary_row = self.fetch_one(
                f"""
                SELECT COUNT(*)::int AS audit_count,
                       AVG(senso_score.score_pct) AS average_score_pct
                  FROM quality.audit_5s_audits a
                  CROSS JOIN LATERAL ({self._dashboard_senso_score_subquery(senso_order)}) AS senso_score
                 WHERE {score_base_where}
                """,
                tuple(params),
            ) or {"audit_count": 0, "average_score_pct": None}
        else:
            score_base_where = (
                f"{where_sql} AND a.status != 'draft' AND a.overall_score_pct IS NOT NULL"
            )
            summary_row = self.fetch_one(
                f"""
                SELECT COUNT(*)::int AS audit_count,
                       AVG(
                           CASE
                               WHEN a.status != 'draft' AND a.overall_score_pct IS NOT NULL
                               THEN a.overall_score_pct
                           END
                       ) AS average_score_pct
                  FROM quality.audit_5s_audits a
                 WHERE {where_sql}
                """,
                tuple(params),
            ) or {"audit_count": 0, "average_score_pct": None}

        nc_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS nc_total,
                   COUNT(*) FILTER (
                       WHERE nc.status IN ('open', 'in_progress')
                   )::int AS nc_open,
                   COUNT(*) FILTER (
                       WHERE nc.status = 'closed'
                   )::int AS nc_closed,
                   COUNT(*) FILTER (
                       WHERE nc.status != 'closed' AND nc.due_date < CURRENT_DATE
                   )::int AS nc_overdue
              FROM quality.audit_5s_nonconformities nc
              JOIN quality.audit_5s_audits a ON a.id = nc.audit_id
             WHERE {where_sql}
               {nc_senso_sql}
            """,
            tuple([*params, *nc_senso_params]),
        ) or {"nc_total": 0, "nc_open": 0, "nc_closed": 0, "nc_overdue": 0}

        trunc = self._dashboard_date_trunc_unit(request.granularity)

        if senso_order:
            score_by_period = self.fetch_all(
                f"""
                SELECT to_char(date_trunc('{trunc}', a.audit_date::timestamp), 'YYYY-MM-DD') AS period,
                       ROUND(AVG(senso_score.score_pct)::numeric, 2) AS average_score_pct,
                       COUNT(*)::int AS audit_count
                  FROM quality.audit_5s_audits a
                  CROSS JOIN LATERAL ({self._dashboard_senso_score_subquery(senso_order)}) AS senso_score
                 WHERE {score_base_where}
                 GROUP BY date_trunc('{trunc}', a.audit_date::timestamp)
                 ORDER BY 1
                """,
                tuple(params),
            )
            score_by_area = self.fetch_all(
                f"""
                SELECT a.area_id::text AS area_id,
                       ar.name AS area_name,
                       ROUND(AVG(senso_score.score_pct)::numeric, 2) AS average_score_pct,
                       COUNT(*)::int AS audit_count
                  FROM quality.audit_5s_audits a
                  JOIN quality.audit_5s_areas ar ON ar.id = a.area_id
                  CROSS JOIN LATERAL ({self._dashboard_senso_score_subquery(senso_order)}) AS senso_score
                 WHERE {score_base_where}
                 GROUP BY a.area_id, ar.name
                 ORDER BY average_score_pct DESC NULLS LAST, ar.name
                 LIMIT 20
                """,
                tuple(params),
            )
        else:
            score_by_period = self.fetch_all(
                f"""
                SELECT to_char(date_trunc('{trunc}', a.audit_date::timestamp), 'YYYY-MM-DD') AS period,
                       ROUND(AVG(a.overall_score_pct)::numeric, 2) AS average_score_pct,
                       COUNT(*)::int AS audit_count
                  FROM quality.audit_5s_audits a
                 WHERE {score_base_where}
                 GROUP BY date_trunc('{trunc}', a.audit_date::timestamp)
                 ORDER BY 1
                """,
                tuple(params),
            )
            score_by_area = self.fetch_all(
                f"""
                SELECT a.area_id::text AS area_id,
                       ar.name AS area_name,
                       ROUND(AVG(a.overall_score_pct)::numeric, 2) AS average_score_pct,
                       COUNT(*)::int AS audit_count
                  FROM quality.audit_5s_audits a
                  JOIN quality.audit_5s_areas ar ON ar.id = a.area_id
                 WHERE {score_base_where}
                 GROUP BY a.area_id, ar.name
                 ORDER BY average_score_pct DESC NULLS LAST, ar.name
                 LIMIT 20
                """,
                tuple(params),
            )

        score_by_senso_where = (
            f"{where_sql} AND a.status != 'draft'"
            if senso_order
            else f"{where_sql} AND a.status != 'draft' AND a.overall_score_pct IS NOT NULL"
        )
        score_by_senso_filter = (
            f"AND s.sort_order = {int(senso_order)}" if senso_order else ""
        )
        score_by_senso = self.fetch_all(
            f"""
            SELECT s.sort_order AS senso_order,
                   s.name AS senso_name,
                   ROUND(AVG((elem->>'percentual')::numeric), 2) AS average_score_pct
              FROM quality.audit_5s_audits a
              CROSS JOIN LATERAL jsonb_array_elements(
                  CASE
                      WHEN jsonb_typeof(a.senso_scores) = 'array' THEN a.senso_scores
                      ELSE '[]'::jsonb
                  END
              ) AS elem
              LEFT JOIN quality.audit_5s_sensos s
                ON s.sort_order = (elem->>'senso_order')::int
             WHERE {score_by_senso_where}
               AND elem->>'percentual' IS NOT NULL
               AND elem->>'percentual' <> 'null'
               AND s.id IS NOT NULL
               {score_by_senso_filter}
             GROUP BY s.sort_order, s.name
             ORDER BY s.sort_order
            """,
            tuple(params),
        )

        nc_by_status = self.fetch_all(
            f"""
            SELECT nc.status,
                   COUNT(*)::int AS count
              FROM quality.audit_5s_nonconformities nc
              JOIN quality.audit_5s_audits a ON a.id = nc.audit_id
             WHERE {where_sql}
               {nc_senso_sql}
             GROUP BY nc.status
             ORDER BY nc.status
            """,
            tuple([*params, *nc_senso_params]),
        )

        total_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS total
              FROM quality.audit_5s_audits a
             WHERE {where_sql}
            """,
            tuple(params),
        ) or {"total": 0}
        total = int(total_row.get("total") or 0)
        offset = (request.page - 1) * request.page_size

        senso_score_select = (
            f"({self._dashboard_senso_score_scalar_subquery(senso_order)}) AS senso_score_pct"
            if senso_order
            else "NULL::numeric AS senso_score_pct"
        )

        nc_item_filter = self._dashboard_nc_item_exists_sql(senso_order)

        items = self.fetch_all(
            f"""
            SELECT a.id::text AS id,
                   a.audit_code,
                   a.audit_date::text AS audit_date,
                   ar.name AS area_name,
                   a.shift,
                   a.status,
                   a.overall_score_pct,
                   {senso_score_select},
                   (
                       SELECT string_agg(aud.display_name, ', ' ORDER BY aud.display_name)
                         FROM quality.audit_5s_auditors aud
                        WHERE aud.audit_id = a.id
                   ) AS auditor_names,
                   (
                       SELECT COUNT(*)::int
                         FROM quality.audit_5s_nonconformities nc
                        WHERE nc.audit_id = a.id
                          {nc_item_filter}
                   ) AS nc_total,
                   (
                       SELECT COUNT(*)::int
                         FROM quality.audit_5s_nonconformities nc
                        WHERE nc.audit_id = a.id
                          AND nc.status IN ('open', 'in_progress')
                          {nc_item_filter}
                   ) AS nc_open
              FROM quality.audit_5s_audits a
              JOIN quality.audit_5s_areas ar ON ar.id = a.area_id
             WHERE {where_sql}
             ORDER BY a.audit_date DESC, a.created_at DESC
             LIMIT %s OFFSET %s
            """,
            (*params, request.page_size, offset),
        )

        return {
            "summary": {
                "audit_count": int(summary_row.get("audit_count") or 0),
                "average_score_pct": self._to_float(summary_row.get("average_score_pct")),
                "nc_total": int(nc_row.get("nc_total") or 0),
                "nc_open": int(nc_row.get("nc_open") or 0),
                "nc_closed": int(nc_row.get("nc_closed") or 0),
                "nc_overdue": int(nc_row.get("nc_overdue") or 0),
                "filtered_senso_order": senso_order,
                "filtered_senso_name": senso_name,
            },
            "charts": {
                "score_by_period": [self._serialize_chart_row(row) for row in score_by_period],
                "score_by_area": [self._serialize_chart_row(row) for row in score_by_area],
                "score_by_senso": [self._serialize_chart_row(row) for row in score_by_senso],
                "nc_by_status": [self._serialize_chart_row(row) for row in nc_by_status],
            },
            "items": [self._serialize_dashboard_item(row) for row in items],
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total": total,
            },
        }

    def _dashboard_filter_clause(
        self,
        *,
        branch_code: str,
        date_start: str,
        date_end: str,
        area_id: str | None,
        shift: str | None,
        audit_status: str | None,
    ) -> tuple[str, list[Any]]:
        conditions = [
            "a.branch_code = %s",
            "a.audit_date BETWEEN %s AND %s",
        ]
        params: list[Any] = [branch_code, date_start, date_end]
        if area_id:
            conditions.append("a.area_id = %s")
            params.append(area_id)
        if shift:
            conditions.append("a.shift = %s")
            params.append(shift)
        if audit_status:
            conditions.append("a.status = %s")
            params.append(audit_status)
        return " AND ".join(conditions), params

    @staticmethod
    def _dashboard_date_trunc_unit(granularity: str) -> str:
        units = {"day": "day", "week": "week", "month": "month"}
        unit = units.get(granularity)
        if not unit:
            raise PluginsRepositoryError("Granularidade inválida.")
        return unit

    @staticmethod
    def _dashboard_senso_score_subquery(senso_order: int) -> str:
        order = int(senso_order)
        return f"""
            SELECT (elem->>'percentual')::numeric AS score_pct
              FROM jsonb_array_elements(
                  CASE
                      WHEN jsonb_typeof(a.senso_scores) = 'array' THEN a.senso_scores
                      ELSE '[]'::jsonb
                  END
              ) AS elem
             WHERE (elem->>'senso_order')::int = {order}
               AND elem->>'percentual' IS NOT NULL
               AND elem->>'percentual' <> 'null'
             LIMIT 1
        """

    @staticmethod
    def _dashboard_senso_score_scalar_subquery(senso_order: int) -> str:
        order = int(senso_order)
        return f"""
            SELECT (elem->>'percentual')::numeric
              FROM jsonb_array_elements(
                  CASE
                      WHEN jsonb_typeof(a.senso_scores) = 'array' THEN a.senso_scores
                      ELSE '[]'::jsonb
                  END
              ) AS elem
             WHERE (elem->>'senso_order')::int = {order}
               AND elem->>'percentual' IS NOT NULL
               AND elem->>'percentual' <> 'null'
             LIMIT 1
        """

    @staticmethod
    def _dashboard_nc_senso_clause(
        senso_order: int | None,
    ) -> tuple[str, list[Any]]:
        if not senso_order:
            return "", []
        return (
            """
               AND EXISTS (
                    SELECT 1
                      FROM quality.audit_5s_responses r
                      JOIN quality.audit_5s_criteria c ON c.id = r.criterion_id
                      JOIN quality.audit_5s_sensos s ON s.id = c.senso_id
                     WHERE r.id = nc.response_id
                       AND s.sort_order = %s
               )
            """,
            [senso_order],
        )

    @staticmethod
    def _dashboard_nc_item_exists_sql(senso_order: int | None) -> str:
        if not senso_order:
            return ""
        order = int(senso_order)
        return f"""
                          AND EXISTS (
                                SELECT 1
                                  FROM quality.audit_5s_responses r
                                  JOIN quality.audit_5s_criteria c ON c.id = r.criterion_id
                                  JOIN quality.audit_5s_sensos s ON s.id = c.senso_id
                                 WHERE r.id = nc.response_id
                                   AND s.sort_order = {order}
                          )
        """

    def _dashboard_senso_name(self, senso_order: int) -> str | None:
        row = self.fetch_one(
            """
            SELECT name
              FROM quality.audit_5s_sensos
             WHERE sort_order = %s
            """,
            (senso_order,),
        )
        if not row:
            return None
        return str(row.get("name") or "")

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        return round(float(value), 2)

    @staticmethod
    def _serialize_chart_row(row: dict[str, Any]) -> dict[str, Any]:
        serialized: dict[str, Any] = {}
        for key, value in row.items():
            if key in ("average_score_pct",) and value is not None:
                serialized[key] = round(float(value), 2)
            elif key in ("senso_order", "audit_count", "count") and value is not None:
                serialized[key] = int(value)
            elif hasattr(value, "isoformat"):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized

    @staticmethod
    def _serialize_dashboard_item(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "audit_code": row["audit_code"],
            "audit_date": str(row["audit_date"])[:10],
            "area_name": row["area_name"],
            "shift": row["shift"],
            "status": row["status"],
            "overall_score_pct": PostgresAudit5sRepository._to_float(row.get("overall_score_pct")),
            "senso_score_pct": PostgresAudit5sRepository._to_float(row.get("senso_score_pct")),
            "auditor_names": row.get("auditor_names"),
            "nc_total": int(row.get("nc_total") or 0),
            "nc_open": int(row.get("nc_open") or 0),
        }

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None

    @staticmethod
    def _json_dumps(value: Any) -> str:
        import json

        return json.dumps(value)
