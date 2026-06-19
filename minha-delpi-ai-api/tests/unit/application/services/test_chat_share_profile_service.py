from unittest.mock import MagicMock

from app.application.services.chat_share_profile_service import ChatShareProfileService


def test_enrich_shares_adds_profile_fields():
    gateway = MagicMock()
    gateway.lookup_directory_users.return_value = [
        {"id": "user-1", "name": "Maria", "email": "maria@delpi.com"}
    ]

    shares = [{"target_user_id": "user-1", "role": "viewer"}]
    enriched = ChatShareProfileService(gateway).enrich_shares(
        shares,
        access_token="token",
    )

    assert enriched[0]["target_user_name"] == "Maria"
    assert enriched[0]["target_user_email"] == "maria@delpi.com"


def test_enrich_user_ranking_adds_profile_fields():
    gateway = MagicMock()
    gateway.lookup_directory_users.return_value = [
        {"id": "user-1", "name": "Maria", "email": "maria@delpi.com"}
    ]

    ranking = [{"userId": "user-1", "messages": 10, "sessions": 2}]
    enriched = ChatShareProfileService(gateway).enrich_user_ranking(
        ranking,
        access_token="token",
    )

    assert enriched[0]["userName"] == "Maria"
    assert enriched[0]["userEmail"] == "maria@delpi.com"
    assert enriched[0]["messages"] == 10
