from app.domain.ports.core_api_gateway_port import CoreApiGatewayPort


class ChatShareProfileService:
    def __init__(self, core_api_gateway: CoreApiGatewayPort):
        self.core_api_gateway = core_api_gateway

    def enrich_shares(
        self,
        shares: list[dict],
        *,
        access_token: str | None,
    ) -> list[dict]:
        if not access_token or not shares:
            return shares

        user_ids = [
            str(share.get("target_user_id") or "")
            for share in shares
            if share.get("target_user_id")
        ]

        if not user_ids:
            return shares

        profiles = self.core_api_gateway.lookup_directory_users(access_token, user_ids)
        profile_by_id = {profile["id"]: profile for profile in profiles}

        enriched: list[dict] = []

        for share in shares:
            profile = profile_by_id.get(str(share.get("target_user_id") or ""))
            enriched.append(
                {
                    **share,
                    "target_user_name": profile.get("name") if profile else None,
                    "target_user_email": profile.get("email") if profile else None,
                }
            )

        return enriched

    def enrich_user_ranking(
        self,
        ranking: list[dict],
        *,
        access_token: str | None,
    ) -> list[dict]:
        if not access_token or not ranking:
            return ranking

        user_ids = [
            str(entry.get("userId") or "")
            for entry in ranking
            if entry.get("userId")
        ]

        if not user_ids:
            return ranking

        profiles = self.core_api_gateway.lookup_directory_users(access_token, user_ids)
        profile_by_id = {profile["id"]: profile for profile in profiles}

        enriched: list[dict] = []

        for entry in ranking:
            profile = profile_by_id.get(str(entry.get("userId") or ""))
            enriched.append(
                {
                    **entry,
                    "userName": profile.get("name") if profile else None,
                    "userEmail": profile.get("email") if profile else None,
                }
            )

        return enriched
