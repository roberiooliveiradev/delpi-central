from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from commercial_app.domain.entities.satisfaction_survey import (
    SatisfactionCampaign,
    SatisfactionRecipient,
    SatisfactionResponse,
)


class SatisfactionSurveyRepositoryPort(ABC):
    @abstractmethod
    def list_campaigns(self) -> list[SatisfactionCampaign]:
        raise NotImplementedError

    @abstractmethod
    def get_campaign(self, campaign_id: str) -> SatisfactionCampaign | None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def list_recipients(self, campaign_id: str) -> list[SatisfactionRecipient]:
        raise NotImplementedError

    @abstractmethod
    def get_recipient(
        self, *, campaign_id: str, recipient_id: str
    ) -> SatisfactionRecipient | None:
        raise NotImplementedError

    @abstractmethod
    def get_recipient_by_token_hash(
        self, token_hash: str
    ) -> SatisfactionRecipient | None:
        raise NotImplementedError

    @abstractmethod
    def find_recipient_by_customer(
        self,
        *,
        campaign_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SatisfactionRecipient | None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def update_recipient_contact(
        self,
        *,
        campaign_id: str,
        recipient_id: str,
        expected_version: int,
        contact_name: str | None,
        contact_email: str | None,
    ) -> SatisfactionRecipient:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def get_response_by_recipient(
        self, recipient_id: str
    ) -> SatisfactionResponse | None:
        raise NotImplementedError

    @abstractmethod
    def count_responses_for_campaign(self, campaign_id: str) -> int:
        raise NotImplementedError
