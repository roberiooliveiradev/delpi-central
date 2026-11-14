from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from commercial_app.domain.entities.satisfaction_survey import (
    SatisfactionCampaign,
    SatisfactionRecipient,
    SatisfactionResponse,
)
from commercial_app.domain.ports.satisfaction_survey_repository_port import (
    SatisfactionSurveyRepositoryPort,
)
from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_CAMPAIGN_COLUMNS = (
    "c.id, c.name, c.starts_at, c.ends_at, c.questionnaire_version, "
    "c.invite_subject, c.invite_body, c.created_by_user_id, "
    "c.created_at, c.updated_at, c.version"
)

_RECIPIENT_COLUMNS = (
    "r.id, r.campaign_id, r.customer_code, r.customer_store, "
    "r.customer_name_snapshot, r.contact_name, r.contact_email, "
    "r.token_hash, r.token_ciphertext, r.created_by_user_id, "
    "r.created_at, r.updated_at, r.version"
)

_RESPONSE_COLUMNS = (
    "id, recipient_id, overall_score, recommendation_score, dimensions, "
    "strengths, improvements, unmet_needs, questionnaire_version, submitted_at"
)


class PostgresSatisfactionSurveyRepository(
    PluginBaseRepository, SatisfactionSurveyRepositoryPort
):
    def list_campaigns(self) -> list[SatisfactionCampaign]:
        rows = self.fetch_all(
            f"""
            SELECT {_CAMPAIGN_COLUMNS},
                   COALESCE(rc.recipient_count, 0) AS recipient_count,
                   COALESCE(rs.response_count, 0) AS response_count
              FROM commercial.satisfaction_campaigns c
              LEFT JOIN (
                    SELECT campaign_id, COUNT(*) AS recipient_count
                      FROM commercial.satisfaction_recipients
                     GROUP BY campaign_id
              ) rc ON rc.campaign_id = c.id
              LEFT JOIN (
                    SELECT r.campaign_id, COUNT(*) AS response_count
                      FROM commercial.satisfaction_responses resp
                      JOIN commercial.satisfaction_recipients r
                        ON r.id = resp.recipient_id
                     GROUP BY r.campaign_id
              ) rs ON rs.campaign_id = c.id
             ORDER BY c.starts_at DESC
            """
        )
        return [self._hydrate_campaign(row) for row in rows]

    def get_campaign(self, campaign_id: str) -> SatisfactionCampaign | None:
        row = self.fetch_one(
            f"""
            SELECT {_CAMPAIGN_COLUMNS},
                   COALESCE(rc.recipient_count, 0) AS recipient_count,
                   COALESCE(rs.response_count, 0) AS response_count
              FROM commercial.satisfaction_campaigns c
              LEFT JOIN (
                    SELECT campaign_id, COUNT(*) AS recipient_count
                      FROM commercial.satisfaction_recipients
                     GROUP BY campaign_id
              ) rc ON rc.campaign_id = c.id
              LEFT JOIN (
                    SELECT r.campaign_id, COUNT(*) AS response_count
                      FROM commercial.satisfaction_responses resp
                      JOIN commercial.satisfaction_recipients r
                        ON r.id = resp.recipient_id
                     GROUP BY r.campaign_id
              ) rs ON rs.campaign_id = c.id
             WHERE c.id = %s
            """,
            (campaign_id,),
        )
        return self._hydrate_campaign(row) if row else None

    def create_campaign(
        self,
        *,
        name: str,
        starts_at: datetime,
        ends_at: datetime,
        questionnaire_version: str,
        invite_subject: str,
        invite_body: str,
        created_by_user_id: str,
    ) -> SatisfactionCampaign:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.satisfaction_campaigns (
                name, starts_at, ends_at, questionnaire_version,
                invite_subject, invite_body, created_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING {_CAMPAIGN_COLUMNS.replace('c.', '')}
            """,
            (
                name,
                starts_at,
                ends_at,
                questionnaire_version,
                invite_subject,
                invite_body,
                created_by_user_id,
            ),
        )
        campaign = self._hydrate_campaign(
            {
                **row,
                "recipient_count": 0,
                "response_count": 0,
            }
        )
        return campaign

    def update_campaign(
        self,
        *,
        campaign_id: str,
        expected_version: int,
        name: str | None = None,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
        invite_subject: str | None = None,
        invite_body: str | None = None,
    ) -> SatisfactionCampaign:
        current = self.get_campaign(campaign_id)
        if current is None:
            raise LookupError("Campanha não encontrada.")
        if current.version != expected_version:
            raise ConflictError("Versão da campanha desatualizada.")

        next_name = name if name is not None else current.name
        next_starts = starts_at if starts_at is not None else current.starts_at
        next_ends = ends_at if ends_at is not None else current.ends_at
        next_subject = (
            invite_subject if invite_subject is not None else current.invite_subject
        )
        next_body = invite_body if invite_body is not None else current.invite_body

        row = self.execute_returning_one(
            f"""
            UPDATE commercial.satisfaction_campaigns
               SET name = %s,
                   starts_at = %s,
                   ends_at = %s,
                   invite_subject = %s,
                   invite_body = %s,
                   updated_at = NOW(),
                   version = version + 1
             WHERE id = %s AND version = %s
         RETURNING {_CAMPAIGN_COLUMNS.replace('c.', '')}
            """,
            (
                next_name,
                next_starts,
                next_ends,
                next_subject,
                next_body,
                campaign_id,
                expected_version,
            ),
        )
        if not row:
            raise ConflictError("Versão da campanha desatualizada.")
        refreshed = self.get_campaign(campaign_id)
        if refreshed is None:
            raise LookupError("Campanha não encontrada após atualização.")
        return refreshed

    def list_recipients(self, campaign_id: str) -> list[SatisfactionRecipient]:
        rows = self.fetch_all(
            f"""
            SELECT {_RECIPIENT_COLUMNS},
                   (resp.id IS NOT NULL) AS has_response,
                   resp.id AS response_id,
                   resp.submitted_at AS submitted_at
              FROM commercial.satisfaction_recipients r
              LEFT JOIN commercial.satisfaction_responses resp
                ON resp.recipient_id = r.id
             WHERE r.campaign_id = %s
             ORDER BY r.customer_name_snapshot ASC NULLS LAST,
                      r.customer_code ASC, r.customer_store ASC
            """,
            (campaign_id,),
        )
        return [self._hydrate_recipient(row) for row in rows]

    def get_recipient(
        self, *, campaign_id: str, recipient_id: str
    ) -> SatisfactionRecipient | None:
        row = self.fetch_one(
            f"""
            SELECT {_RECIPIENT_COLUMNS},
                   (resp.id IS NOT NULL) AS has_response,
                   resp.id AS response_id,
                   resp.submitted_at AS submitted_at
              FROM commercial.satisfaction_recipients r
              LEFT JOIN commercial.satisfaction_responses resp
                ON resp.recipient_id = r.id
             WHERE r.campaign_id = %s AND r.id = %s
            """,
            (campaign_id, recipient_id),
        )
        return self._hydrate_recipient(row) if row else None

    def get_recipient_by_token_hash(
        self, token_hash: str
    ) -> SatisfactionRecipient | None:
        row = self.fetch_one(
            f"""
            SELECT {_RECIPIENT_COLUMNS},
                   (resp.id IS NOT NULL) AS has_response,
                   resp.id AS response_id,
                   resp.submitted_at AS submitted_at
              FROM commercial.satisfaction_recipients r
              LEFT JOIN commercial.satisfaction_responses resp
                ON resp.recipient_id = r.id
             WHERE r.token_hash = %s
            """,
            (token_hash,),
        )
        return self._hydrate_recipient(row) if row else None

    def find_recipient_by_customer(
        self,
        *,
        campaign_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SatisfactionRecipient | None:
        row = self.fetch_one(
            f"""
            SELECT {_RECIPIENT_COLUMNS},
                   (resp.id IS NOT NULL) AS has_response,
                   resp.id AS response_id,
                   resp.submitted_at AS submitted_at
              FROM commercial.satisfaction_recipients r
              LEFT JOIN commercial.satisfaction_responses resp
                ON resp.recipient_id = r.id
             WHERE r.campaign_id = %s
               AND r.customer_code = %s
               AND r.customer_store = %s
            """,
            (campaign_id, customer_code, customer_store),
        )
        return self._hydrate_recipient(row) if row else None

    def create_recipient(
        self,
        *,
        campaign_id: str,
        customer_code: str,
        customer_store: str,
        customer_name_snapshot: str | None,
        contact_name: str | None,
        contact_email: str | None,
        token_hash: str,
        token_ciphertext: str,
        created_by_user_id: str,
    ) -> SatisfactionRecipient:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.satisfaction_recipients (
                campaign_id, customer_code, customer_store,
                customer_name_snapshot, contact_name, contact_email,
                token_hash, token_ciphertext, created_by_user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {_RECIPIENT_COLUMNS.replace('r.', '')}
            """,
            (
                campaign_id,
                customer_code,
                customer_store,
                customer_name_snapshot,
                contact_name,
                contact_email,
                token_hash,
                token_ciphertext,
                created_by_user_id,
            ),
        )
        return self._hydrate_recipient(
            {
                **row,
                "has_response": False,
                "response_id": None,
                "submitted_at": None,
            }
        )

    def update_recipient_contact(
        self,
        *,
        campaign_id: str,
        recipient_id: str,
        expected_version: int,
        contact_name: str | None,
        contact_email: str | None,
    ) -> SatisfactionRecipient:
        row = self.execute_returning_one(
            f"""
            UPDATE commercial.satisfaction_recipients
               SET contact_name = %s,
                   contact_email = %s,
                   updated_at = NOW(),
                   version = version + 1
             WHERE id = %s
               AND campaign_id = %s
               AND version = %s
         RETURNING {_RECIPIENT_COLUMNS.replace('r.', '')}
            """,
            (
                contact_name,
                contact_email,
                recipient_id,
                campaign_id,
                expected_version,
            ),
        )
        if not row:
            raise ConflictError("Participante não encontrado ou versão desatualizada.")
        refreshed = self.get_recipient(
            campaign_id=campaign_id, recipient_id=recipient_id
        )
        if refreshed is None:
            raise LookupError("Participante não encontrado após atualização.")
        return refreshed

    def create_response(
        self,
        *,
        recipient_id: str,
        overall_score: int,
        recommendation_score: int,
        dimensions: dict[str, Any],
        strengths: str | None,
        improvements: str | None,
        unmet_needs: str | None,
        questionnaire_version: str,
    ) -> SatisfactionResponse:
        row = self.execute_returning_one(
            f"""
            INSERT INTO commercial.satisfaction_responses (
                recipient_id, overall_score, recommendation_score, dimensions,
                strengths, improvements, unmet_needs, questionnaire_version
            ) VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s)
            RETURNING {_RESPONSE_COLUMNS}
            """,
            (
                recipient_id,
                overall_score,
                recommendation_score,
                json.dumps(dimensions),
                strengths,
                improvements,
                unmet_needs,
                questionnaire_version,
            ),
        )
        return self._hydrate_response(row)

    def get_response_by_recipient(
        self, recipient_id: str
    ) -> SatisfactionResponse | None:
        row = self.fetch_one(
            f"""
            SELECT {_RESPONSE_COLUMNS}
              FROM commercial.satisfaction_responses
             WHERE recipient_id = %s
            """,
            (recipient_id,),
        )
        return self._hydrate_response(row) if row else None

    def count_responses_for_campaign(self, campaign_id: str) -> int:
        row = self.fetch_one(
            """
            SELECT COUNT(*) AS total
              FROM commercial.satisfaction_responses resp
              JOIN commercial.satisfaction_recipients r
                ON r.id = resp.recipient_id
             WHERE r.campaign_id = %s
            """,
            (campaign_id,),
        )
        return int(row["total"] if row else 0)

    def _hydrate_campaign(self, row: dict[str, Any]) -> SatisfactionCampaign:
        return SatisfactionCampaign(
            id=str(row["id"]),
            name=str(row["name"]),
            starts_at=row["starts_at"],
            ends_at=row["ends_at"],
            questionnaire_version=str(row["questionnaire_version"]),
            invite_subject=str(row.get("invite_subject") or ""),
            invite_body=str(row.get("invite_body") or ""),
            created_by_user_id=str(row["created_by_user_id"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            version=int(row["version"]),
            recipient_count=int(row.get("recipient_count") or 0),
            response_count=int(row.get("response_count") or 0),
        )

    def _hydrate_recipient(self, row: dict[str, Any]) -> SatisfactionRecipient:
        return SatisfactionRecipient(
            id=str(row["id"]),
            campaign_id=str(row["campaign_id"]),
            customer_code=str(row["customer_code"]),
            customer_store=str(row["customer_store"]),
            customer_name_snapshot=(
                str(row["customer_name_snapshot"])
                if row.get("customer_name_snapshot") is not None
                else None
            ),
            contact_name=(
                str(row["contact_name"]) if row.get("contact_name") is not None else None
            ),
            contact_email=(
                str(row["contact_email"])
                if row.get("contact_email") is not None
                else None
            ),
            token_hash=str(row["token_hash"]),
            token_ciphertext=str(row["token_ciphertext"]),
            created_by_user_id=str(row["created_by_user_id"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            version=int(row["version"]),
            has_response=bool(row.get("has_response")),
            response_id=(
                str(row["response_id"]) if row.get("response_id") is not None else None
            ),
            submitted_at=row.get("submitted_at"),
        )

    def _hydrate_response(self, row: dict[str, Any]) -> SatisfactionResponse:
        dimensions = row.get("dimensions") or {}
        if isinstance(dimensions, str):
            dimensions = json.loads(dimensions)
        return SatisfactionResponse(
            id=str(row["id"]),
            recipient_id=str(row["recipient_id"]),
            overall_score=int(row["overall_score"]),
            recommendation_score=int(row["recommendation_score"]),
            dimensions=dict(dimensions),
            strengths=row.get("strengths"),
            improvements=row.get("improvements"),
            unmet_needs=row.get("unmet_needs"),
            questionnaire_version=str(row["questionnaire_version"]),
            submitted_at=row["submitted_at"],
        )


class ConflictError(RuntimeError):
    """Optimistic concurrency / uniqueness conflict."""
