"""GLPI #887: restricted, read-only reconciliation preview.

Names are weak hints for human review, NEVER proof of RH/Core identity.
No registration bindings are created or modified by this service.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from unicodedata import normalize


MAX_REVIEW_MEMBERS = 500

STATUSES = (
    "verified_mapping",
    "suggestion_by_name",
    "ambiguous_rh_name",
    "ambiguous_core_name",
    "already_assigned_to_other_registration",
    "no_exact_name_suggestion",
)


def _normalized_name(value: str | None) -> str:
    """Conservative formatting only; never fuzzy/phonetic identity matching."""
    return " ".join(normalize("NFKC", value or "").casefold().split())


class OrganizationIdentityReviewService:
    def __init__(self, organization_team, users, hr_registrations):
        self.team = organization_team
        self.users = users
        self.hr_registrations = hr_registrations

    def get_review(
        self,
        manager_registration: str,
        *,
        include_indirect: bool = True,
        details: bool = False,
    ) -> dict:
        team_data = self.team.get_team(
            manager_registration, include_indirect=include_indirect, include_inactive=False
        )
        members = team_data["members"]
        if len(members) > MAX_REVIEW_MEMBERS:
            raise ValueError("Equipe excede o limite da prévia administrativa (500).")

        # Core users are only evidence for an admin to investigate. Their email
        # or any personal profile data must not be returned by this endpoint.
        active_users = [user for user in self.users.list_all() if user.active]
        by_name = defaultdict(list)
        for user in active_users:
            normalized = _normalized_name(user.name)
            if normalized:
                by_name[normalized].append(user)

        allocated = self.hr_registrations.get_allocated_registrations(
            {user.id for user in active_users}
        )
        rh_name_counts = Counter(
            _normalized_name(member["fullName"])
            for member in members
            if member["identityStatus"] != "mapped"
        )
        counts = Counter()
        rows: list[dict] = []
        for member in members:
            status = None
            suggestion_id = None
            mapped_id = member["coreUserId"] if member["identityStatus"] == "mapped" else None
            normalized = _normalized_name(member["fullName"])
            if mapped_id:
                status = "verified_mapping"
            elif normalized and rh_name_counts[normalized] > 1:
                status = "ambiguous_rh_name"
            else:
                candidates = by_name.get(normalized, [])
                if not candidates:
                    status = "no_exact_name_suggestion"
                elif len(candidates) > 1:
                    status = "ambiguous_core_name"
                elif str(candidates[0].id) in allocated:
                    status = "already_assigned_to_other_registration"
                else:
                    status = "suggestion_by_name"
                    suggestion_id = str(candidates[0].id)
            counts[status] += 1
            if details:
                rows.append({
                    "registration": member["registration"],
                    "fullName": member["fullName"],
                    "branchCode": member["branchCode"],
                    "relationship": member["relationship"],
                    "status": status,
                    "mappedCoreUserId": mapped_id,
                    "suggestedCoreUserId": suggestion_id,
                    "verified": status == "verified_mapping",
                })

        result = {
            "source": "portal-rh+core",
            "managerRegistration": manager_registration,
            "includeIndirect": bool(include_indirect),
            "teamCount": len(members),
            "statusCounts": {status: counts[status] for status in STATUSES},
            "verifiedCount": counts["verified_mapping"],
            "suggestionCount": counts["suggestion_by_name"],
            "readOnly": True,
            "automaticMappingsCreated": 0,
            "warning": (
                "Sugestões por nome NÃO comprovam identidade, posse de conta Core "
                "nem correspondência Keycloak. Conferência administrativa obrigatória."
            ),
        }
        if details:
            result["members"] = rows
        return result
